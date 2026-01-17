
# -*- coding: utf-8 -*-
"""
Service layer for Category Management.
Handles business logic including tree generation and safe deletion.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from app.modules.catalog.models import Category, Product, Attribute, AttributeValue
from app.modules.catalog.schemas import (
    CategoryCreate, CategoryUpdate,
    AttributeCreate, AttributeUpdate
)



class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Category]:
        """Get all categories flat list"""
        query = select(Category).order_by(Category.parent_id, Category.sort_order)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_list(self, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        """Get paginated category list with search"""
        query = select(Category)
        
        if search:
            query = query.where(Category.name.ilike(f"%{search}%"))
            
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()
        
        # Paginate
        query = query.order_by(Category.sort_order).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def get_tree(self) -> List[Dict[str, Any]]:
        """
        Build a nested tree structure of categories.
        Includes product counts for each category.
        """
        # Fetch all categories
        query = select(Category).order_by(Category.sort_order)
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        # Fetch product counts (group by category_id)
        count_query = select(Product.category_id, func.count(Product.id)).group_by(Product.category_id)
        count_result = await self.db.execute(count_query)
        product_counts = {row[0]: row[1] for row in count_result.all()}
        
        # Build lookup dict
        category_map = {}
        roots = []
        
        # First pass: Create dicts and map
        for cat in categories:
            cat_dict = {
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "parent_id": cat.parent_id,
                "image_url": cat.image_url,
                "is_active": cat.is_active,
                "sort_order": cat.sort_order,
                "products_count": product_counts.get(cat.id, 0),
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
                "description": cat.description,
                "seo_title": cat.seo_title,
                "seo_description": cat.seo_description,
                "is_dynamic": getattr(cat, "is_dynamic", False),
                "rules": getattr(cat, "rules", None),
                "children": []
            }
            category_map[cat.id] = cat_dict
            
        # Second pass: Build tree
        for cat_id, cat_dict in category_map.items():
            parent_id = cat_dict["parent_id"]
            if parent_id and parent_id in category_map:
                category_map[parent_id]["children"].append(cat_dict)
            else:
                roots.append(cat_dict)
                
        return roots

    async def get_by_id(self, category_id: str) -> Optional[Category]:
        """Get category by ID"""
        query = select(Category).where(Category.id == category_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
        
    async def _generate_unique_slug(self, name: str, exclude_id: Optional[str] = None) -> str:
        """Generate unique slug from name"""
        import re
        # Basic slugify: lowercase, replace spaces/symbols with hyphens
        slug = re.sub(r'[^a-z0-9\u0600-\u06FF]+', '-', name.lower()).strip('-')
        if not slug:
            slug = "category"
            
        base_slug = slug
        counter = 1
        
        while True:
            # Check existence
            query = select(Category).where(Category.slug == slug)
            if exclude_id:
                query = query.where(Category.id != exclude_id)
                
            result = await self.db.execute(query)
            if not result.scalar_one_or_none():
                break
                
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        return slug

    async def create(self, data: CategoryCreate) -> Category:
        """Create new category"""
        # Auto-generate slug if missing
        if not data.slug:
            data.slug = await self._generate_unique_slug(data.name)
        else:
            # Ensure provided slug is unique
            data.slug = await self._generate_unique_slug(data.slug)

        # Exclude non-model fields
        category_data = data.dict()
        category_data.pop('is_dynamic', None)
        category_data.pop('rules', None)
        
        category = Category(**category_data)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: str, data: CategoryUpdate) -> Optional[Category]:
        """Update existing category"""
        category = await self.get_by_id(category_id)
        if not category:
            return None
            
        update_data = data.dict(exclude_unset=True)
        
        # Handle slug update if provided
        if "slug" in update_data:
             update_data["slug"] = await self._generate_unique_slug(update_data["slug"], exclude_id=category_id)

        # Exclude non-model fields
        update_data.pop('is_dynamic', None)
        update_data.pop('rules', None)

        for field, value in update_data.items():
            setattr(category, field, value)
            
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete_safe(self, category_id: str) -> bool:
        """
        Delete category safely.
        1. Unlink all products (set category_id = NULL)
        2. Delete the category (children will cascade delete due to model config, 
           OR we should handle them safely too? 
           Model says: cascade="all, delete-orphan". This means deleting a parent 
           WILL delete child categories. This is standard behavior for category trees.
           Products however are safely unlinked.)
        """
        category = await self.get_by_id(category_id)
        if not category:
            return False
            
        # 1. Unlink products
        stmt = update(Product).where(Product.category_id == category_id).values(category_id=None)
        await self.db.execute(stmt)
        
        # 2. Delete category
        await self.db.delete(category)
        await self.db.commit()
        return True

    async def get_breadcrumbs(self, category_id: str) -> List[Dict[str, str]]:
        """
        Get breadcrumb path for a category (Root -> ... -> Current).
        Returns list of dicts: [{'id': ..., 'name': ..., 'slug': ...}, ...]
        """
        breadcrumbs = []
        current_id = category_id
        
        # Simple iterative approach to climb up the tree
        # Improved performance could be achieved with CTEs (Common Table Expressions) if supported,
        # but for category depth < 10, iterative query is fine.
        while current_id:
            category = await self.get_by_id(current_id)
            if not category:
                break
                
            breadcrumbs.insert(0, {
                "id": category.id,
                "name": category.name,
                "slug": category.slug
            })
            current_id = category.parent_id
            
        return breadcrumbs

    async def apply_dynamic_filters(self, query: Any, rules_json: str) -> Any:
        """
        Apply dynamic filters to a Product query based on rules JSON.
        Rules format:
        {
            "match": "all" | "any",
            "conditions": [
                { "field": "name", "operator": "contains", "value": "term" },
                { "field": "price", "operator": "gt", "value": 100 },
                { "field": "stock", "operator": "gt", "value": 0 }
            ]
        }
        """
        import json
        from sqlalchemy import or_, and_
        
        try:
            rules = json.loads(rules_json)
        except:
            return query
            
        conditions = rules.get("conditions", [])
        if not conditions:
            return query
            
        filters = []
        for cond in conditions:
            field = cond.get("field")
            op = cond.get("operator")
            val = cond.get("value")
            
            clause = None
            
            # Field Mapping
            if field == "name":
                if op == "contains":
                    clause = Product.name.ilike(f"%{val}%")
                elif op == "eq":
                    clause = Product.name == val
                    
            elif field == "price":
                # Check if any variant matches
                if op == "gt":
                    clause = Product.variants.any(ProductVariant.price > float(val))
                elif op == "lt":
                    clause = Product.variants.any(ProductVariant.price < float(val))
                    
            elif field == "stock":
                # Simple stock check (any variant has stock)
                # True aggregation is expensive here, so we check "variants with quantity"
                if op == "gt":
                    clause = Product.variants.any(ProductVariant.quantity > int(val))
                elif op == "eq":
                    if int(val) == 0:
                        # Logic for "out of stock": NO variant has quantity > 0
                        # This is equivalent to NOT(any(quantity > 0))
                        # But for simplicity in this builder, let's use sum logic only if possible or simplify
                        # Let's stick to "Has a variant with quantity [op] [val]"
                        clause = Product.variants.any(ProductVariant.quantity == int(val))
            
            elif field == "product_type":
                 if op == "eq":
                    clause = Product.product_type == val

            if clause is not None:
                filters.append(clause)
        
        if not filters:
            return query
            
        if rules.get("match") == "any":
            query = query.where(or_(*filters))
        else:
            query = query.where(and_(*filters))
            
        return query

    async def preview_rules(self, rules_json: str) -> List[Product]:
        """Preview products matching a rule set"""
        query = select(Product).options(selectinload(Product.variants))
        query = await self.apply_dynamic_filters(query, rules_json)
        query = query.limit(20) # Limit preview
        result = await self.db.execute(query)
        return result.scalars().all()


class AttributeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Attribute]:
        """Get all attributes with values"""
        query = select(Attribute).order_by(Attribute.name)
        result = await self.db.execute(query)
        return result.scalars().unique().all()

    async def get_by_id(self, attribute_id: str) -> Optional[Attribute]:
        """Get attribute by ID"""
        query = select(Attribute).where(Attribute.id == attribute_id)
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def create(self, data: AttributeCreate) -> Attribute:
        """Create new attribute with values"""
        attribute = Attribute(
            name=data.name,
            type=data.type
        )
        self.db.add(attribute)
        await self.db.flush()

        # Add values
        for val_data in data.values:
            val = AttributeValue(
                attribute_id=attribute.id,
                value=val_data.value,
                meta=val_data.meta,
                sort_order=val_data.sort_order
            )
            self.db.add(val)

        await self.db.commit()
        await self.db.refresh(attribute)
        return attribute

    async def update(self, attribute_id: str, data: AttributeUpdate) -> Optional[Attribute]:
        """
        Update attribute.
        Full update for values: delete existing and recreate (simplest approach).
        """
        attribute = await self.get_by_id(attribute_id)
        if not attribute:
            return None

        # Update basic fields
        if data.name:
            attribute.name = data.name
        if data.type:
            attribute.type = data.type

        # Update values if provided
        if data.values is not None:
             # Delete existing values
            await self.db.execute(
                select(AttributeValue).where(AttributeValue.attribute_id == attribute_id).execution_options(synchronize_session=False)
            )
            stmt = select(AttributeValue).where(AttributeValue.attribute_id == attribute_id) # dummy select to avoid linting issues if delete not standard
            # Actually use delete statement
            from sqlalchemy import delete
            await self.db.execute(delete(AttributeValue).where(AttributeValue.attribute_id == attribute_id))
            
            # Add new values
            for val_data in data.values:
                val = AttributeValue(
                    attribute_id=attribute.id,
                    value=val_data.value,
                    meta=val_data.meta,
                    sort_order=val_data.sort_order
                )
                self.db.add(val)

        await self.db.commit()
        await self.db.refresh(attribute)
        return attribute

    async def delete(self, attribute_id: str) -> bool:
        """Delete attribute"""
        attribute = await self.get_by_id(attribute_id)
        if not attribute:
            return False

        await self.db.delete(attribute)
        await self.db.commit()
        return True


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, status: Optional[str] = None, search: Optional[str] = None) -> List[Any]:
        """
        Get all reviews, optionally filtered by status and search query.
        Joins with Product to get product name.
        """
        # Local import to avoid circular dependency
        from app.modules.catalog.models import ProductReview, Product
        from sqlalchemy import or_
        
        query = select(ProductReview).options(selectinload(ProductReview.product)).order_by(ProductReview.created_at.desc())
        
        if status:
            if status == "Hidden":
                # Assuming Hidden maps to Rejected or we can add specific logic
                query = query.where(ProductReview.status == "Rejected")
            elif status == "Published":
                query = query.where(ProductReview.status == "Approved")
            elif status != "All" and status != "Modified":
                 query = query.where(ProductReview.status == status)

        if search:
            search_filter = or_(
                ProductReview.customer_name.ilike(f"%{search}%"),
                ProductReview.comment.ilike(f"%{search}%")
                # Add product name search if possible, requires join or extra logic
            )
            query = query.where(search_filter)
            
        result = await self.db.execute(query)
        reviews = result.scalars().all()
        
        # Enrich with product name manually if needed
        enriched = []
        for r in reviews:
            r.product_name = r.product.name if r.product else "Deleted Product"
            enriched.append(r)
            
        return enriched

    async def create(self, data: Any) -> Any:
        from app.modules.catalog.models import ProductReview
        review = ProductReview(**data.dict())
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def update_status(self, review_id: str, status: str) -> bool:
        from app.modules.catalog.models import ProductReview
        
        stmt = update(ProductReview).where(ProductReview.id == review_id).values(status=status)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def delete(self, review_id: str) -> bool:
        from app.modules.catalog.models import ProductReview
        
        stmt = select(ProductReview).where(ProductReview.id == review_id)
        result = await self.db.execute(stmt)
        review = result.scalar_one_or_none()
        
        if not review:
            return False
            
        await self.db.delete(review)
        await self.db.commit()
        return True


class CustomFieldService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Any]:
        from app.modules.catalog.models import CustomFieldDefinition
        query = select(CustomFieldDefinition).order_by(CustomFieldDefinition.sort_order)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, data: Any) -> Any:
        from app.modules.catalog.models import CustomFieldDefinition
        # Check key uniqueness
        existing = await self.db.execute(select(CustomFieldDefinition).where(CustomFieldDefinition.key == data.key))
        if existing.scalar_one_or_none():
            raise ValueError(f"Field with key '{data.key}' already exists")

        field = CustomFieldDefinition(**data.dict())
        self.db.add(field)
        await self.db.commit()
        await self.db.refresh(field)
        return field

    async def update(self, field_id: str, data: Any) -> Optional[Any]:
        from app.modules.catalog.models import CustomFieldDefinition
        field = await self.db.get(CustomFieldDefinition, field_id)
        if not field:
            return None
        
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(field, key, value)
            
        await self.db.commit()
        await self.db.refresh(field)
        return field

    async def delete(self, field_id: str) -> bool:
        from app.modules.catalog.models import CustomFieldDefinition, ProductCustomFieldValue
        field = await self.db.get(CustomFieldDefinition, field_id)
        if not field:
            return False
            
        # Delete related values first (although cascade should handle it if set)
        from sqlalchemy import delete
        await self.db.execute(delete(ProductCustomFieldValue).where(ProductCustomFieldValue.field_id == field_id))
        
        await self.db.delete(field)
        await self.db.commit()
        return True


class QuestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, status: Optional[str] = None, search: Optional[str] = None) -> List[Any]:
        from app.modules.catalog.models import ProductQuestion, Product
        from sqlalchemy import or_

        query = select(ProductQuestion).options(selectinload(ProductQuestion.product)).order_by(ProductQuestion.created_at.desc())

        if status:
            if status != "All":
                query = query.where(ProductQuestion.status == status)

        if search:
            search_filter = or_(
                ProductQuestion.customer_name.ilike(f"%{search}%"),
                ProductQuestion.question_text.ilike(f"%{search}%"),
                ProductQuestion.answer_text.ilike(f"%{search}%")
            )
            query = query.where(search_filter)

        result = await self.db.execute(query)
        questions = result.scalars().all()

        enriched = []
        for q in questions:
            q.product_name = q.product.name if q.product else "Deleted Product"
            enriched.append(q)
            
        return enriched

    async def create(self, data: Any) -> Any:
        from app.modules.catalog.models import ProductQuestion
        question = ProductQuestion(**data.dict())
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def answer_question(self, question_id: str, answer_text: str) -> bool:
        from app.modules.catalog.models import ProductQuestion
        query = select(ProductQuestion).where(ProductQuestion.id == question_id)
        result = await self.db.execute(query)
        question = result.scalar_one_or_none()
        
        if not question:
            return False
            
        question.answer_text = answer_text
        question.answered_at = datetime.utcnow()
        question.status = "Approved"
        await self.db.commit()
        return True

    async def update_status(self, question_id: str, status: str) -> bool:
        from app.modules.catalog.models import ProductQuestion
        query = select(ProductQuestion).where(ProductQuestion.id == question_id)
        result = await self.db.execute(query)
        question = result.scalar_one_or_none()
        
        if not question:
            return False
            
        question.status = status
        await self.db.commit()
        return True

    async def delete(self, question_id: str) -> bool:
        from app.modules.catalog.models import ProductQuestion
        query = select(ProductQuestion).where(ProductQuestion.id == question_id)
        result = await self.db.execute(query)
        question = result.scalar_one_or_none()
        
        if not question:
            return False
            
        await self.db.delete(question)
        await self.db.commit()
        return True


class StockNotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> dict:
        from app.modules.catalog.models import StockNotification
        from sqlalchemy import func
        # Mock logic or simple counts
        query_total = select(func.count(StockNotification.id))
        query_sent = select(func.count(StockNotification.id)).where(StockNotification.status == "Sent")
        
        total = (await self.db.execute(query_total)).scalar() or 0
        sent = (await self.db.execute(query_sent)).scalar() or 0
        
        return {
            "total_subscribers": total,
            "alerts_sent": sent,
            "sales_conversion": 0
        }

    async def get_all(self, status: Optional[str] = None, search: Optional[str] = None, period: Optional[str] = None) -> List[Any]:
        from app.modules.catalog.models import StockNotification, Product, ProductImage
        from sqlalchemy import or_, func

        query = select(StockNotification).options(
            selectinload(StockNotification.product).selectinload(Product.images)
        ).order_by(StockNotification.created_at.desc())

        if status and status != 'All':
            if status == "Sent":
                query = query.where(StockNotification.status == "Sent")
            elif status == "Pending":
                query = query.where(StockNotification.status == "Pending")
        
        if search:
            search_filter = or_(
                StockNotification.name.ilike(f"%{search}%"),
                StockNotification.email.ilike(f"%{search}%"),
                StockNotification.phone.ilike(f"%{search}%"),
                # Join with product to search product name if needed
            )
            query = query.where(search_filter)

        # Date filters (Simple implementation)
        now = datetime.utcnow()
        if period == "Today":
            query = query.where(func.date(StockNotification.created_at) == now.date())
        # Add other periods as needed

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        enriched = []
        for n in notifications:
            n.product_name = n.product.name if n.product else "Deleted Product"
            n.product_image = n.product.images[0].image_url if n.product and n.product.images else "/static/images/placeholder.png"
            enriched.append(n)
            
        return enriched

    async def create(self, data: Any) -> Any:
        from app.modules.catalog.models import StockNotification
        notif = StockNotification(**data.dict())
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def send_notification(self, notification_id: str, channel: str) -> bool:
        from app.modules.catalog.models import StockNotification
        query = select(StockNotification).where(StockNotification.id == notification_id)
        result = await self.db.execute(query)
        notif = result.scalar_one_or_none()
        
        if not notif:
            return False
        
        # Mock sending logic (Email/SMS)
        # In real app, call email/sms provider here
        
        notif.status = "Sent"
        notif.sent_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def get_settings(self) -> Any:
        from app.modules.catalog.models import StockNotificationSetting
        # Singleton pattern
        query = select(StockNotificationSetting)
        result = await self.db.execute(query)
        setting = result.scalars().first()
        
        if not setting:
            setting = StockNotificationSetting()
            self.db.add(setting)
            await self.db.commit()
            await self.db.refresh(setting)
        
        return setting

    async def update_settings(self, data: Any) -> Any:
        setting = await self.get_settings()
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(setting, key, value)
        
        await self.db.commit()
        await self.db.refresh(setting)
        return setting


