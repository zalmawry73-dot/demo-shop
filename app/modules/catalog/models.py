# -*- coding: utf-8 -*-
"""
SQLAlchemy models for the Product Catalog module.
Handles Products, Variants, Images, and Options with proper relationships.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from itertools import product as itertools_product

from sqlalchemy import (
    Column,
    String,
    Text,
    Enum as SQLEnum,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, backref
from enum import Enum

from app.core.database import Base


# ----------------------------------------------------------------------
# Enumerations
# ----------------------------------------------------------------------
class ProductTypeEnum(str, Enum):
    PHYSICAL = "Physical"
    DIGITAL = "Digital"
    SERVICE = "Service"
    FOOD = "Food"


class ProductStatusEnum(str, Enum):
    ACTIVE = "Active"
    DRAFT = "Draft"
    ARCHIVED = "Archived"


# ----------------------------------------------------------------------
# Core Models
# ----------------------------------------------------------------------

class Category(Base):
    """
    Hierarchical category model for organizing products.
    Supports infinite nesting (Parent -> Child -> Grandchild).
    """
    __tablename__ = "categories"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Hierarchy
    parent_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    
    # Basic Info
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(1024), nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # SEO
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(512), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    children = relationship(
        "Category",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
        order_by="Category.sort_order"
    )
    
    # Products relationship (one-to-many)
    products = relationship("Product", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.id} '{self.name}'>"


class Product(Base):
    """
    Main product model representing a sellable item.
    Can have multiple variants, images, and options.
    """
    __tablename__ = "products"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)  # HTML content
    
    # Product classification
    product_type = Column(
        String(20),
        nullable=False,
        default="Physical"
    )
    status = Column(
        String(20),
        nullable=False,
        default="Draft",
        index=True
    )
    
    # Relationships to other entities (nullable for now)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    brand_id = Column(String(36), nullable=True, index=True)
    
    # Tax configuration
    taxable = Column(Boolean, default=False, nullable=False)
    
    # Physical attributes
    weight = Column(Float, nullable=True)  # in kg
    
    # SEO fields
    page_title = Column(String(255), nullable=True)
    meta_description = Column(String(512), nullable=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships (cascade delete)
    category = relationship("Category", back_populates="products")
    variants = relationship(
        "ProductVariant",
        cascade="all, delete-orphan",
        back_populates="product",
        lazy="selectin"
    )

    images = relationship(
        "ProductImage",
        cascade="all, delete-orphan",
        back_populates="product",
        lazy="selectin",
        order_by="ProductImage.display_order"
    )
    options = relationship(
        "ProductOption",
        cascade="all, delete-orphan",
        back_populates="product",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Product {self.id} '{self.name}'>"


class ProductVariant(Base):
    """
    Represents a specific variant of a product (e.g., Red-Large).
    This is the actual inventory unit.
    """
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_variant_sku"),
    )

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to product
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    
    # Unique identifiers
    sku = Column(String(64), nullable=False, unique=True, index=True)
    barcode = Column(String(64), nullable=True)
    
    # Pricing
    price = Column(Float, nullable=False, default=0.0)
    cost_price = Column(Float, nullable=True)  # For profit calculation
    compare_at_price = Column(Float, nullable=True)  # Original price for discounts
    
    # Inventory
    quantity = Column(Integer, nullable=False, default=0, index=True)
    weight = Column(Float, nullable=True)  # kg or lbs
    
    # Variant options stored as JSON-like string
    # Example: '{"Color": "Red", "Size": "L"}'
    options = Column(Text, nullable=False, default="{}")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship back to product
    product = relationship("Product", back_populates="variants")

    def __repr__(self) -> str:
        return f"<ProductVariant {self.sku} (Product: {self.product_id})>"


class ProductImage(Base):
    """
    Stores product images with ordering and main image designation.
    """
    __tablename__ = "product_images"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to product
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    
    # Image details
    image_url = Column(String(1024), nullable=False)
    alt_text = Column(String(255), nullable=True)
    is_main = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship back to product
    product = relationship("Product", back_populates="images")

    def __repr__(self) -> str:
        return f"<ProductImage {self.id} (Main: {self.is_main})>"


class ProductOption(Base):
    """
    Metadata for variant options (e.g., Size, Color).
    Stores the option name and possible values.
    """
    __tablename__ = "product_options"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to product
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    
    # Option details
    name = Column(String(64), nullable=False)  # e.g., "Size", "Color"
    values = Column(Text, nullable=False, default="[]")  # JSON array as string: '["S", "M", "L"]'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship back to product
    product = relationship("Product", back_populates="options")

    def __repr__(self) -> str:
        return f"<ProductOption '{self.name}' for Product {self.product_id}>"


class Attribute(Base):
    """
    Global attributes/options that can be reused across products.
    e.g., Color, Size, Material.
    """
    __tablename__ = "attributes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    type = Column(String(50), default="text", nullable=False)  # text, color, image
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to values
    values = relationship(
        "AttributeValue",
        backref=backref("attribute"),
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def __repr__(self):
        return f"<Attribute {self.id} '{self.name}'>"


class AttributeValue(Base):
    """
    Specific values for an attribute.
    e.g., Red, Blue (for Color); S, M, L (for Size).
    """
    __tablename__ = "attribute_values"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attribute_id = Column(String(36), ForeignKey("attributes.id"), nullable=False, index=True)
    value = Column(String(255), nullable=False)  # The display value
    meta = Column(String(255), nullable=True)    # Hex code (for color) or Image URL
    sort_order = Column(Integer, default=0)

    def __repr__(self):
        return f"<AttributeValue {self.value}>"


class ProductReview(Base):
    """
    Customer reviews for products.
    """
    __tablename__ = "product_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=True) # Optional link to user system if exists
    customer_name = Column(String(255), nullable=False)
    rating = Column(Integer, nullable=False) # 1-5
    comment = Column(Text, nullable=True)
    status = Column(String(20), default="Pending", index=True) # Pending, Approved, Rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    product = relationship("Product", backref=backref("reviews", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Review {self.id} {self.rating}*>"


class ProductQuestion(Base):
    """
    Customer questions about products.
    """
    __tablename__ = "product_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=True) # Optional link to user system if exists
    customer_name = Column(String(255), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)
    status = Column(String(20), default="Pending", index=True) # Pending, Approved, Rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    answered_at = Column(DateTime, nullable=True)

    # Relationship
    product = relationship("Product", backref=backref("questions", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Question {self.id}>"


class StockNotification(Base):
    """
    Subscribers interested in out-of-stock products.
    """
    __tablename__ = "stock_notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True) # Link to Customer model if registered
    
    name = Column(String(255), nullable=True) # Guest or Customer Name
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    status = Column(String(20), default="Pending", index=True) # Pending, Sent
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    # Relationships
    product = relationship("Product", backref=backref("stock_notifications", cascade="all, delete-orphan"))
    # We use a string for the relationship to avoid circular imports if possible, or reliance on registry
    customer = relationship("app.modules.customers.models.Customer")

    def __repr__(self):
        return f"<StockNotification {self.email} for {self.product_id}>"


class StockNotificationSetting(Base):
    """
    Global settings for stock notifications (Singleton).
    """
    __tablename__ = "stock_notification_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Automation
    delay_duration = Column(Integer, default=0) # Minutes to wait before sending
    
    # Channels
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    
    # Content - Email
    email_subject_ar = Column(String(255), default="المنتج توفر من جديد")
    email_subject_en = Column(String(255), default="Product is back in stock")
    email_body_ar = Column(Text, default="عزيزنا العميل، المنتج الذي كنت تنتظره توفر الآن.")
    email_body_en = Column(Text, default="Dear customer, the product you were waiting for is now available.")
    
    # Content - SMS
    sms_body_ar = Column(Text, default="المنتج توفر الآن. اطلبه قبل نفاذ الكمية.")
    sms_body_en = Column(Text, default="Product is back in stock. Order now.")
    
    show_discount_code = Column(Boolean, default=False)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)




class CustomFieldDefinition(Base):
    """
    Defines a custom field that can be added to products.
    e.g. "Author" (Text), "Warranty Period" (Number), "Manufacturing Date" (Date).
    """
    __tablename__ = "custom_field_definitions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    key = Column(String(255), nullable=False, unique=True, index=True) # key for API/Code usage, e.g. "author"
    type = Column(String(50), nullable=False, default="text") # text, number, date, boolean, select
    options = Column(Text, nullable=True) # JSON list for 'select' type options
    is_required = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CustomFieldDefinition {self.key} ({self.type})>"


class ProductCustomFieldValue(Base):
    """
    Stores the actual value of a custom field for a specific product.
    """
    __tablename__ = "product_custom_field_values"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    field_id = Column(String(36), ForeignKey("custom_field_definitions.id"), nullable=False, index=True)
    
    # We store everything as string for flexibility, type casting happens in app logic
    value = Column(Text, nullable=True) 

    # Relationships
    product = relationship("Product", backref=backref("custom_field_values", cascade="all, delete-orphan"))
    definition = relationship("CustomFieldDefinition")

    def __repr__(self):
        return f"<CustomFieldValue {self.value} for Product {self.product_id}>"



# ----------------------------------------------------------------------
# Utility Functions
# ----------------------------------------------------------------------
def generate_variants_from_options(options_dict: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """
    Generate all possible variant combinations from options (Cartesian product).
    
    Args:
        options_dict: Dictionary mapping option names to lists of values
                     e.g., {"Color": ["Red", "Blue"], "Size": ["S", "M"]}
    
    Returns:
        List of dictionaries, each representing a variant combination
        e.g., [
            {"Color": "Red", "Size": "S"},
            {"Color": "Red", "Size": "M"},
            {"Color": "Blue", "Size": "S"},
            {"Color": "Blue", "Size": "M"}
        ]
    
    Example:
        >>> opts = {"Color": ["Red", "Blue"], "Size": ["S", "M"]}
        >>> generate_variants_from_options(opts)
        [
            {"Color": "Red", "Size": "S"},
            {"Color": "Red", "Size": "M"},
            {"Color": "Blue", "Size": "S"},
            {"Color": "Blue", "Size": "M"}
        ]
    """
    if not options_dict:
        return [{}]
    
    # Get option names in consistent order
    option_names = list(options_dict.keys())
    option_values = [options_dict[name] for name in option_names]
    
    # Generate Cartesian product
    variants = []
    for combination in itertools_product(*option_values):
        variant = {name: value for name, value in zip(option_names, combination)}
        variants.append(variant)
    
    return variants


def generate_sku(product_name: str, variant_options: Dict[str, str], index: int = 0) -> str:
    """
    Generate a SKU for a variant based on product name and options.
    
    Args:
        product_name: Name of the product
        variant_options: Dictionary of variant options
        index: Optional index for uniqueness
    
    Returns:
        Generated SKU string
    
    Example:
        >>> generate_sku("T-Shirt", {"Color": "Red", "Size": "M"}, 1)
        "TSHIRT-RED-M-001"
    """
    # Clean product name
    base = product_name.upper().replace(" ", "")[:10]
    
    # Add option values
    option_parts = [str(v).upper()[:3] for v in variant_options.values()]
    
    # Combine
    sku_parts = [base] + option_parts + [f"{index:03d}"]
    return "-".join(sku_parts)
