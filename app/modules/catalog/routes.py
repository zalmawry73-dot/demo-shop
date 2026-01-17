# -*- coding: utf-8 -*-
"""
FastAPI routes for Product Catalog module.
Handles CRUD operations, filtering, import/export.
"""

import json
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Request, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.catalog.models import (
    Product, ProductVariant, ProductImage, ProductOption, Category,
    ProductTypeEnum, ProductStatusEnum, ProductCustomFieldValue,
    generate_variants_from_options, generate_sku
)
from app.modules.catalog.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductListItem, ProductFilters, BulkProductOperation,
    VariantGenerationRequest, VariantGenerationResponse,
    ProductVariantCreate,
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeItem, CategoryListResponse,
    AttributeCreate, AttributeUpdate, AttributeResponse,
    ReviewCreate, ReviewUpdateStatus, ReviewResponse,
    CustomFieldDefinitionCreate, CustomFieldDefinitionUpdate, CustomFieldDefinitionResponse
)
from app.modules.catalog.services import CategoryService, AttributeService, ReviewService, CustomFieldService

import pandas as pd
import io
import shutil
import os
import time
from pathlib import Path


router = APIRouter(prefix="/catalog", tags=["Catalog"])
templates = Jinja2Templates(directory="templates")


# ----------------------------------------------------------------------
# Page Routes
# ----------------------------------------------------------------------
@router.get("/products")
async def products_list_page(request: Request):
    """Render the products list page"""
    return templates.TemplateResponse("catalog/products_list.html", {"request": request})


@router.get("/custom-fields", response_class=HTMLResponse)
async def custom_fields_page(request: Request):
    """Render the Custom Fields management page"""
    return templates.TemplateResponse("catalog/custom_fields.html", {"request": request})


@router.get("/products/new")
async def product_editor_new(request: Request):
    """Render the product editor for creating a new product"""
    return templates.TemplateResponse("catalog/product_editor.html", {
        "request": request,
        "mode": "create"
    })


@router.get("/products/{product_id}/edit")
async def product_editor_edit(request: Request, product_id: str):
    """Render the product editor for editing an existing product"""
    return templates.TemplateResponse("catalog/product_editor.html", {
        "request": request,
        "mode": "edit",
        "product_id": product_id
    })


# ----------------------------------------------------------------------
# API Routes - Product CRUD
# ----------------------------------------------------------------------
@router.get("/api/products", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    product_type: Optional[str] = None,
    status: Optional[str] = None,
    stock_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List products with filtering and pagination.
    Returns aggregated data for the list view.
    """
    # Build base query
    query = select(Product).options(
        selectinload(Product.variants),
        selectinload(Product.images),
        selectinload(Product.category)
    )
    
    # Apply filters
    filters = []
    
    if search:
        search_filter = or_(
            Product.name.ilike(f"%{search}%"),
            Product.slug.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if category_id:
        filters.append(Product.category_id == category_id)
    
    if product_type:
        filters.append(Product.product_type == product_type)
    
    if status:
        filters.append(Product.status == status)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count()).select_from(Product)
    if filters:
        count_query = count_query.where(and_(*filters))
    result = await db.execute(count_query)
    total = result.scalar_one()
    
    # Apply pagination and ordering
    query = query.order_by(desc(Product.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Build response items
    from app.modules.inventory.service import get_variant_total_stock
    
    items = []
    for product in products:
        # Aggregate variant data - calculate stock from InventoryItem
        total_stock = 0
        for variant in product.variants:
            variant_stock = await get_variant_total_stock(db, variant.id)
            total_stock += variant_stock
        
        prices = [v.price for v in product.variants if v.price > 0]
        min_price = min(prices) if prices else None
        max_price = max(prices) if prices else None
        
        # Get main image
        main_image = next((img.image_url for img in product.images if img.is_main), None)
        if not main_image and product.images:
            main_image = product.images[0].image_url
        
        # Apply stock filter if needed
        if stock_status:
            if stock_status == 'out' and total_stock > 0:
                continue
            if stock_status == 'in' and total_stock == 0:
                 continue
            if stock_status == 'low' and total_stock >= 5:
                continue
        
        items.append(ProductListItem(
            id=product.id,
            name=product.name,
            slug=product.slug,
            product_type=product.product_type,
            status=product.status,
            created_at=product.created_at,
            total_variants=len(product.variants),
            total_stock=total_stock,
            min_price=min_price,
            max_price=max_price,
            main_image_url=main_image,
            category_id=product.category_id,
            category_name=product.category.name if product.category else None
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/api/products", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new product with nested variants, images, and options.
    """
    # Check for duplicate slug
    existing = await db.execute(select(Product).where(Product.slug == product_data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Product with this slug already exists")
    
    # Create product
    product = Product(
        name=product_data.name,
        description=product_data.description,
        product_type=ProductTypeEnum(product_data.product_type),
        status=ProductStatusEnum(product_data.status),
        category_id=product_data.category_id,
        brand_id=product_data.brand_id,
        taxable=product_data.taxable,
        page_title=product_data.page_title,
        meta_description=product_data.meta_description,
        slug=product_data.slug
    )
    
    db.add(product)
    await db.flush()  # Get product ID
    
    # Add images
    for img_data in product_data.images:
        image = ProductImage(
            product_id=product.id,
            image_url=img_data.image_url,
            alt_text=img_data.alt_text,
            is_main=img_data.is_main,
            display_order=img_data.display_order
        )
        db.add(image)
    
    # Add options
    for opt_data in product_data.options:
        option = ProductOption(
            product_id=product.id,
            name=opt_data.name,
            values=json.dumps(opt_data.values)
        )
        db.add(option)
    
    
    # Add variants and sync to inventory
    from app.modules.inventory.service import sync_variant_to_inventory, get_default_warehouse
    
    # Get default warehouse for initial stock
    default_warehouse = await get_default_warehouse(db)
    if not default_warehouse:
        raise HTTPException(
            status_code=500, 
            detail="No active warehouse found. Please create a warehouse first."
        )
    
    for var_data in product_data.variants:
        variant = ProductVariant(
            product_id=product.id,
            sku=var_data.sku,
            barcode=var_data.barcode,
            price=var_data.price,
            cost_price=var_data.cost_price,
            compare_at_price=var_data.compare_at_price,
            weight=var_data.weight,
            options=json.dumps(var_data.options)
            # ⚠️ NO quantity field - managed in InventoryItem
        )
        db.add(variant)
        await db.flush()  # Get variant ID
        
        # Sync to inventory if quantity > 0
        if var_data.quantity > 0:
            # Determine target warehouse (use initial_warehouse_id if provided, else default)
            target_warehouse_id = getattr(var_data, 'initial_warehouse_id', None) or default_warehouse.id
            
            await sync_variant_to_inventory(
                db, 
                variant_id=variant.id,
                quantity=var_data.quantity,
                warehouse_id=target_warehouse_id
            )


    # Add Custom Fields
    if product_data.custom_fields:
        for field_id, value in product_data.custom_fields.items():
            # Ensure value is string
            str_val = str(value) if value is not None else ""
            cf = ProductCustomFieldValue(
                product_id=product.id,
                field_id=field_id,
                value=str_val
            )
            db.add(cf)
    
    await db.commit()
    
    # Re-fetch with all relationships to avoid MissingGreenlet error during serialization
    stmt = select(Product).where(Product.id == product.id).options(
        selectinload(Product.variants),
        selectinload(Product.images),
        selectinload(Product.options),
        selectinload(Product.custom_field_values)
    )
    result = await db.execute(stmt)
    product = result.scalar_one()

    return product



# ----------------------------------------------------------------------
# Export Route (Must be before get_product to avoid ID collision)
# ----------------------------------------------------------------------
@router.get("/api/products/export")
async def export_products(
    ids: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Export products to Excel (All or Selected)"""
    query = select(Product).options(
        selectinload(Product.variants),
        selectinload(Product.category)
    )
    
    if ids:
        id_list = ids.split(',')
        query = query.where(Product.id.in_(id_list))
        
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Build data for export with Arabic Headers
    export_data = []
    for product in products:
        # If no variants, at least export product info
        if not product.variants:
            export_data.append({
                "اسم المنتج": product.name,
                "SKU": product.slug, # Fallback
                "الباركود": "",
                "السعر": 0,
                "سعر التكلفة": 0,
                "الكمية": 0,
                "الحالة": product.status,
                "النوع": product.product_type,
                "التصنيف": product.category.name if product.category else "-",
                "الخيارات": ""
            })
            continue

        for variant in product.variants:
            export_data.append({
                "اسم المنتج": product.name,
                "SKU": variant.sku,
                "الباركود": variant.barcode,
                "السعر": variant.price,
                "سعر التكلفة": variant.cost_price,
                "الكمية": variant.quantity,
                "الحالة": product.status,
                "النوع": product.product_type,
                "التصنيف": product.category.name if product.category else "-",
                "الخيارات": variant.options
            })
    
    df = pd.DataFrame(export_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=products_export.xlsx"}
    )


@router.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single product by ID with all related data"""
    query = select(Product).where(Product.id == product_id).options(
        selectinload(Product.variants),
        selectinload(Product.images),
        selectinload(Product.options),
        selectinload(Product.custom_field_values)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/api/products/{product_id}/inventory")
async def get_product_inventory_distribution(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get inventory distribution for all variants of a product across warehouses.
    Shows how stock is distributed across different locations.
    """
    from app.modules.inventory.service import get_variant_stock_by_warehouse, get_variant_total_stock
    
    # Get product with variants
    query = select(Product).where(Product.id == product_id).options(
        selectinload(Product.variants)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Build inventory distribution for all variants
    inventory_data = []
    for variant in product.variants:
        total_stock = await get_variant_total_stock(db, variant.id)
        distribution = await get_variant_stock_by_warehouse(db, variant.id)
        
        inventory_data.append({
            "variant_id": variant.id,
            "sku": variant.sku,
            "options": json.loads(variant.options) if variant.options else {},
            "total_stock": total_stock,
            "warehouses": distribution
        })
    
    return {
        "product_id": product.id,
        "product_name": product.name,
        "variants": inventory_data
    }



@router.put("/api/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing product"""
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    update_data = product_data.dict(exclude_unset=True)
    custom_fields_data = update_data.pop('custom_fields', None) # Extract custom fields

    for field, value in update_data.items():
        if field in ['product_type', 'status'] and value:
            value = ProductTypeEnum(value) if field == 'product_type' else ProductStatusEnum(value)
        setattr(product, field, value)
    
    # Update Custom Fields (Delete All & Re-insert strategy for simplicity)
    if custom_fields_data is not None:
        from sqlalchemy import delete
        # 1. Delete existing
        await db.execute(delete(ProductCustomFieldValue).where(ProductCustomFieldValue.product_id == product_id))
        
        # 2. Insert new
        for field_id, value in custom_fields_data.items():
            str_val = str(value) if value is not None else ""
            cf = ProductCustomFieldValue(
                product_id=product.id,
                field_id=field_id,
                value=str_val
            )
            db.add(cf)
    
    await db.commit()
    await db.commit()
    
    # Reload product with all relationships
    query = select(Product).where(Product.id == product_id).options(
        selectinload(Product.variants),
        selectinload(Product.images),
        selectinload(Product.options),
        selectinload(Product.custom_field_values)
    )
    result = await db.execute(query)
    product = result.scalar_one()
    
    return product


@router.delete("/api/products/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a product and all related data (cascade)"""
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product)
    await db.commit()


# ----------------------------------------------------------------------
# Variant Generation
# ----------------------------------------------------------------------
@router.post("/api/products/generate-variants", response_model=VariantGenerationResponse)
async def generate_variants(
    request: VariantGenerationRequest
):
    """
    Generate variant combinations from options (Cartesian product).
    Does not save to database, just returns the generated data.
    """
    variants_data = generate_variants_from_options(request.options)
    
    variants = []
    for idx, variant_options in enumerate(variants_data):
        sku = generate_sku(request.product_name, variant_options, idx)
        variant = ProductVariantCreate(
            sku=sku,
            price=request.base_price,
            quantity=request.base_quantity,
            options=variant_options
        )
        variants.append(variant)
    
    return VariantGenerationResponse(
        variants=variants,
        count=len(variants)
    )


# ----------------------------------------------------------------------
# Bulk Operations
# ----------------------------------------------------------------------
@router.post("/api/products/bulk", status_code=200)
async def bulk_operations(
    operation: BulkProductOperation,
    db: AsyncSession = Depends(get_db)
):
    """Perform bulk operations on multiple products"""
    if operation.action == "delete":
        query = select(Product).where(Product.id.in_(operation.product_ids))
        result = await db.execute(query)
        products = result.scalars().all()
        
        for product in products:
            await db.delete(product)
        
        await db.commit()
        return {"message": f"Deleted {len(products)} products"}
    
    elif operation.action == "update_status":
        if not operation.value:
            raise HTTPException(status_code=400, detail="Status value required")
        
        query = select(Product).where(Product.id.in_(operation.product_ids))
        result = await db.execute(query)
        products = result.scalars().all()
        
        for product in products:
            product.status = ProductStatusEnum(operation.value)
        
        await db.commit()
        return {"message": f"Updated {len(products)} products"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


# ----------------------------------------------------------------------
# Import / Export / Upload
# ----------------------------------------------------------------------
@router.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file and return the URL"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Ensure directory exists
    upload_dir = Path("static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate safe filename
    safe_name = f"{int(time.time())}_{file.filename.replace(' ', '_')}"
    file_path = upload_dir / safe_name
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/static/uploads/{safe_name}", "filename": safe_name}





@router.post("/api/products/import")
async def import_products(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Import products from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    # Read Excel file
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    
    # Validate required columns
    required_cols = ["Product Name", "SKU", "Price", "Quantity"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_cols)}"
        )
    
    # Group by product name to handle variants
    imported_count = 0
    for product_name, group in df.groupby("Product Name"):
        # Create product with first variant's data
        first_row = group.iloc[0]
        
        # Generate slug from name
        slug = product_name.lower().replace(" ", "-")
        
        # Check if product exists
        existing = await db.execute(select(Product).where(Product.slug == slug))
        if existing.scalar_one_or_none():
            continue  # Skip existing products
        
        product = Product(
            name=product_name,
            slug=slug,
            product_type=ProductTypeEnum(first_row.get("Type", "Physical")),
            status=ProductStatusEnum(first_row.get("Status", "Active")),
            taxable=first_row.get("Taxable", False)
        )
        
        db.add(product)
        await db.flush()
        
        # Add variants from all rows for this product
        for _, row in group.iterrows():
            variant = ProductVariant(
                product_id=product.id,
                sku=row["SKU"],
                barcode=row.get("Barcode"),
                price=float(row["Price"]),
                cost_price=float(row.get("Cost Price", 0)),
                quantity=int(row["Quantity"]),
                options=row.get("Options", "{}")
            )
            db.add(variant)
        
        imported_count += 1
    
    await db.commit()
    
    return {"message": f"Imported {imported_count} products successfully"}


# ----------------------------------------------------------------------
# Category Management Routes
# ----------------------------------------------------------------------
@router.get("/categories", response_class=HTMLResponse)
async def list_categories_page(request: Request):
    """Render categories management page"""
    return templates.TemplateResponse("catalog/categories_list.html", {"request": request})


@router.get("/categories/create", response_class=HTMLResponse)
async def create_category_page(request: Request):
    """Render create category page"""
    return templates.TemplateResponse("catalog/category_form.html", {"request": request, "category": None})


@router.get("/categories/{category_id}/edit", response_class=HTMLResponse)
async def edit_category_page(
    category_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Render edit category page"""
    service = CategoryService(db)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    return templates.TemplateResponse("catalog/category_form.html", {
        "request": request,
        "category": category
    })


@router.get("/api/categories/tree", response_model=List[CategoryTreeItem])
async def get_categories_tree(
    db: AsyncSession = Depends(get_db)
):
    """Get nested category tree with product counts"""
    service = CategoryService(db)
    return await service.get_tree()


@router.get("/api/categories/list", response_model=CategoryListResponse)
async def list_categories_api(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get paginated category list"""
    service = CategoryService(db)
    return await service.get_list(page=page, page_size=page_size, search=search)


@router.post("/api/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new category"""
    # Check if slug exists
    query = select(Category).where(Category.slug == data.slug)
    existing = await db.execute(query)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category slug already exists")

    service = CategoryService(db)
    return await service.create(data)


@router.put("/api/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing category"""
    service = CategoryService(db)
    category = await service.update(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/api/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Safe delete category.
    Unlinks associated products before deletion.
    """
    service = CategoryService(db)
    success = await service.delete_safe(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")


@router.post("/api/categories/reorder", status_code=200)
async def reorder_categories(
    items: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """
    Update sort order and parent_id for drag & drop.
    items: [{id: "...", parent_id: "...", sort_order: 1}, ...]
    """
    # Simple batch update
    for item in items:
        stmt = update(Category).where(Category.id == item["id"]).values(
            parent_id=item.get("parent_id"),
            sort_order=item.get("sort_order", 0)
        )
        await db.execute(stmt)
    await db.commit()
    await db.commit()
    return {"message": "Categories reordered successfully"}


@router.get("/api/categories/{category_id}/breadcrumbs")
async def get_category_breadcrumbs(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get breadcrumb path for a category"""
    return breadcrumbs


class RulesPreviewRequest(BaseModel):
    rules: str


@router.post("/api/categories/preview-rules", response_model=List[ProductListItem])
async def preview_category_rules(
    data: RulesPreviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """Preview products matching dynamic category rules"""
    service = CategoryService(db)
    products = await service.preview_rules(data.rules)
    
    # Map to ProductListItem
    items = []
    for product in products:
         items.append(ProductListItem(
            id=product.id,
            name=product.name,
            slug=product.slug,
            product_type=product.product_type.value,
            status=product.status.value,
            created_at=product.created_at,
            total_variants=len(product.variants),
            total_stock=0, # Simplified for preview
            min_price=0,
            max_price=0,
            main_image_url=None,
            category_id=product.category_id,
            category_name=None
        ))
    return items


# ----------------------------------------------------------------------
# Attribute (Options) Routes
# ----------------------------------------------------------------------
@router.get("/options", response_class=HTMLResponse)
async def list_options_page(request: Request):
    """Render options list page"""
    return templates.TemplateResponse("catalog/options_list.html", {"request": request})


@router.get("/options/form", response_class=HTMLResponse)
async def create_option_page(request: Request):
    """Render create option page"""
    return templates.TemplateResponse("catalog/options_form.html", {
        "request": request,
        "option": None
    })


@router.get("/options/{option_id}/form", response_class=HTMLResponse)
async def edit_option_page(
    option_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Render edit option page"""
    service = AttributeService(db)
    attribute = await service.get_by_id(option_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="Option not found")
        
    return templates.TemplateResponse("catalog/options_form.html", {
        "request": request,
        "option": attribute
    })


@router.get("/api/attributes", response_model=List[AttributeResponse])
async def list_attributes(
    db: AsyncSession = Depends(get_db)
):
    """List all attributes"""
    service = AttributeService(db)
    return await service.get_all()


@router.get("/api/attributes/{attribute_id}", response_model=AttributeResponse)
async def get_attribute(
    attribute_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get single attribute"""
    service = AttributeService(db)
    attribute = await service.get_by_id(attribute_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return attribute


@router.post("/api/attributes", response_model=AttributeResponse, status_code=201)
async def create_attribute(
    data: AttributeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new attribute"""
    service = AttributeService(db)
    return await service.create(data)


@router.put("/api/attributes/{attribute_id}", response_model=AttributeResponse)
async def update_attribute(
    attribute_id: str,
    data: AttributeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update attribute"""
    service = AttributeService(db)
    attribute = await service.update(attribute_id, data)
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return attribute


@router.delete("/api/attributes/{attribute_id}", status_code=204)
async def delete_attribute(
    attribute_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete attribute"""
    service = AttributeService(db)
    success = await service.delete(attribute_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attribute not found")
    if not success:
        raise HTTPException(status_code=404, detail="Attribute not found")


# ----------------------------------------------------------------------
# Custom Fields Routes
# ----------------------------------------------------------------------
@router.get("/api/custom-fields", response_model=List[CustomFieldDefinitionResponse])
async def list_custom_fields(
    db: AsyncSession = Depends(get_db)
):
    """List all custom field definitions"""
    service = CustomFieldService(db)
    return await service.get_all()

@router.post("/api/custom-fields", response_model=CustomFieldDefinitionResponse, status_code=201)
async def create_custom_field(
    data: CustomFieldDefinitionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom field definition"""
    service = CustomFieldService(db)
    return await service.create(data)

@router.put("/api/custom-fields/{field_id}", response_model=CustomFieldDefinitionResponse)
async def update_custom_field(
    field_id: str,
    data: CustomFieldDefinitionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a custom field definition"""
    service = CustomFieldService(db)
    result = await service.update(field_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Custom field not found")
    return result

@router.delete("/api/custom-fields/{field_id}", status_code=204)
async def delete_custom_field(
    field_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom field definition"""
    service = CustomFieldService(db)
    success = await service.delete(field_id)
    if not success:
        raise HTTPException(status_code=404, detail="Custom field not found")


# ----------------------------------------------------------------------
# Review Routes
# ----------------------------------------------------------------------


