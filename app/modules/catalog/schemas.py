# -*- coding: utf-8 -*-
"""
Pydantic schemas for Product Catalog API validation.
"""

from typing import List, Optional, Dict, Any
import json
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ----------------------------------------------------------------------
# Image Schemas
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Category Schemas
# ----------------------------------------------------------------------
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=1024)
    is_active: bool = True
    sort_order: int = 0
    parent_id: Optional[str] = None
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = Field(None, max_length=512)
    is_dynamic: bool = False
    rules: Optional[str] = None # JSON string


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=1024)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    parent_id: Optional[str] = None
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = Field(None, max_length=512)
    is_dynamic: Optional[bool] = None
    rules: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    items: List[CategoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategoryTreeItem(CategoryResponse):
    """
    Product count and children for the tree view.
    Using forward reference for recursive children.
    """
    products_count: int = 0
    children: List['CategoryTreeItem'] = []

# Update forward reference for recursive schema
CategoryTreeItem.update_forward_refs()


# ----------------------------------------------------------------------
# Image Schemas
# ----------------------------------------------------------------------
class ProductImageBase(BaseModel):
    image_url: str = Field(..., max_length=1024)
    alt_text: Optional[str] = Field(None, max_length=255)
    is_main: bool = False
    display_order: int = 0


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageResponse(ProductImageBase):
    id: str
    product_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------------------------------------------------------------
# Option Schemas
# ----------------------------------------------------------------------
class ProductOptionBase(BaseModel):
    name: str = Field(..., max_length=64)
    values: List[str] = Field(default_factory=list)


class ProductOptionCreate(ProductOptionBase):
    pass


class ProductOptionResponse(ProductOptionBase):
    id: str
    product_id: str
    created_at: datetime

    class Config:
        from_attributes = True

    @validator('values', pre=True)
    def parse_values(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v


# ----------------------------------------------------------------------
# Variant Schemas
# ----------------------------------------------------------------------
class ProductVariantBase(BaseModel):
    sku: str = Field(..., max_length=64)
    barcode: Optional[str] = Field(None, max_length=64)
    price: float = Field(..., ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    compare_at_price: Optional[float] = Field(None, ge=0)
    quantity: int = Field(default=0, ge=0)
    weight: Optional[float] = Field(None, ge=0)
    options: Dict[str, str] = Field(default_factory=dict)


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=64)
    barcode: Optional[str] = Field(None, max_length=64)
    price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    compare_at_price: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)
    weight: Optional[float] = Field(None, ge=0)
    options: Optional[Dict[str, str]] = None


class ProductVariantResponse(ProductVariantBase):
    id: str
    product_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator('options', pre=True)
    def parse_options(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v


# ----------------------------------------------------------------------
# Product Schemas
# ----------------------------------------------------------------------
class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    product_type: str = Field(default="Physical")
    status: str = Field(default="Draft")
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    taxable: bool = False
    page_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=512)
    slug: str = Field(..., max_length=255)

    @validator('product_type')
    def validate_product_type(cls, v):
        allowed = ["Physical", "Digital", "Service", "Food"]
        if v not in allowed:
            raise ValueError(f"Product type must be one of {allowed}")
        return v

    @validator('status')
    def validate_status(cls, v):
        allowed = ["Active", "Draft", "Archived"]
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v



class ProductCreate(ProductBase):
    """Schema for creating a product with nested data"""
    images: List[ProductImageCreate] = Field(default_factory=list)
    options: List[ProductOptionCreate] = Field(default_factory=list)
    variants: List[ProductVariantCreate] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Dictionary of field_id: value")


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    product_type: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    taxable: Optional[bool] = None
    page_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=512)
    slug: Optional[str] = Field(None, max_length=255)
    custom_fields: Optional[Dict[str, Any]] = None


class ProductCustomFieldValueResponse(BaseModel):
    field_id: str
    value: Any

    class Config:
        from_attributes = True

class ProductResponse(ProductBase):
    """Schema for product response with relationships"""
    id: str
    created_at: datetime
    updated_at: datetime
    variants: List[ProductVariantResponse] = Field(default_factory=list)
    images: List[ProductImageResponse] = Field(default_factory=list)
    options: List[ProductOptionResponse] = Field(default_factory=list)
    custom_field_values: List[ProductCustomFieldValueResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProductListItem(BaseModel):
    """Simplified schema for product list view"""
    id: str
    name: str
    slug: str
    product_type: str
    status: str
    created_at: datetime
    
    # Aggregated data
    total_variants: int = 0
    total_stock: int = 0
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    max_price: Optional[float] = None
    main_image_url: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


# ----------------------------------------------------------------------
# Filter & Pagination Schemas
# ----------------------------------------------------------------------
class ProductFilters(BaseModel):
    """Query parameters for filtering products"""
    search: Optional[str] = None
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    product_type: Optional[str] = None
    status: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None


class ProductListResponse(BaseModel):
    """Paginated product list response"""
    items: List[ProductListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ----------------------------------------------------------------------
# Bulk Operation Schemas
# ----------------------------------------------------------------------
class BulkProductOperation(BaseModel):
    product_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., description="delete or update_status")
    value: Optional[str] = None  # For update_status action


# ----------------------------------------------------------------------
# Variant Generation Schema
# ----------------------------------------------------------------------
class VariantGenerationRequest(BaseModel):
    """Request to generate variants from options"""
    product_name: str
    options: Dict[str, List[str]] = Field(
        ...,
        description="Dictionary of option names to value lists",
        example={"Color": ["Red", "Blue"], "Size": ["S", "M"]}
    )
    base_price: float = Field(default=0.0, ge=0)
    base_quantity: int = Field(default=0, ge=0)


class VariantGenerationResponse(BaseModel):
    """Response with generated variant data"""
    variants: List[ProductVariantCreate]
    count: int


# ----------------------------------------------------------------------
# Attribute (Global Options) Schemas
# ----------------------------------------------------------------------
class AttributeValueBase(BaseModel):
    value: str = Field(..., max_length=255)
    meta: Optional[str] = Field(None, max_length=255)
    sort_order: int = 0


class AttributeValueCreate(AttributeValueBase):
    pass


class AttributeValueResponse(AttributeValueBase):
    id: str
    attribute_id: str

    class Config:
        from_attributes = True


class AttributeBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: str = Field(default="text", max_length=50)


class AttributeCreate(AttributeBase):
    values: List[AttributeValueCreate] = Field(default_factory=list)


class AttributeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=50)
    values: Optional[List[AttributeValueCreate]] = None


class AttributeResponse(AttributeBase):
    id: str
    created_at: datetime
    values: List[AttributeValueResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ----------------------------------------------------------------------
# Review Schemas
# ----------------------------------------------------------------------
class ReviewBase(BaseModel):
    customer_name: str = Field(..., max_length=255)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    product_id: str


class ReviewUpdateStatus(BaseModel):
    status: str

# ----------------------------------------------------------------------
# Question Schemas
# ----------------------------------------------------------------------
class QuestionBase(BaseModel):
    product_id: str
    user_id: Optional[str] = None
    customer_name: str
    question_text: str

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(BaseModel):
    answer_text: str

class QuestionStatusUpdate(BaseModel):
    status: str

class QuestionResponse(QuestionBase):
    id: str
    answer_text: Optional[str] = None
    status: str
    created_at: datetime
    answered_at: Optional[datetime] = None
    product_name: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewResponse(ReviewBase):
    id: str
    product_id: str
    status: str
    created_at: datetime
    product_name: Optional[str] = None # For display in list

    class Config:
        from_attributes = True


# ----------------------------------------------------------------------
# Custom Field Schemas
# ----------------------------------------------------------------------
class CustomFieldDefinitionBase(BaseModel):
    name: str = Field(..., max_length=255)
    key: str = Field(..., max_length=255)
    type: str = Field(..., pattern="^(text|number|date|boolean|select)$")
    options: Optional[str] = None # JSON string for select options
    is_required: bool = False
    sort_order: int = 0


class CustomFieldDefinitionCreate(CustomFieldDefinitionBase):
    pass


class CustomFieldDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    options: Optional[str] = None
    is_required: Optional[bool] = None
    sort_order: Optional[int] = None


class CustomFieldDefinitionResponse(CustomFieldDefinitionBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------------------------------------------------------------
# Stock Notification Schemas
# ----------------------------------------------------------------------
class StockNotificationCreate(BaseModel):
    product_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    customer_id: Optional[int] = None
    name: Optional[str] = None

class StockNotificationResponse(BaseModel):
    id: str
    product_id: str
    customer_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    product_name: Optional[str] = None
    product_image: Optional[str] = None

    class Config:
        from_attributes = True

class StockNotificationSettingUpdate(BaseModel):
    delay_duration: Optional[int] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    email_subject_ar: Optional[str] = None
    email_subject_en: Optional[str] = None
    email_body_ar: Optional[str] = None
    email_body_en: Optional[str] = None
    sms_body_ar: Optional[str] = None
    sms_body_en: Optional[str] = None
    show_discount_code: Optional[bool] = None

class StockNotificationStats(BaseModel):
    total_subscribers: int
    alerts_sent: int
    sales_conversion: int # Mocked for now


