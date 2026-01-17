
from typing import Optional, Dict
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Float, Boolean, Enum, JSON, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.models import TimeStampedModel

class ShippingConditionType(str, PyEnum):
    FIXED = "fixed"
    WEIGHT_BASED = "weight_based"
    PRICE_BASED = "price_based"

class StoreSettings(TimeStampedModel):
    __tablename__ = "store_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_name: Mapped[str] = mapped_column(String(255), default="My Store")
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    support_email: Mapped[Optional[str]] = mapped_column(String(255))
    support_phone: Mapped[Optional[str]] = mapped_column(String(50))
    iban: Mapped[Optional[str]] = mapped_column(String(100))
    vat_id: Mapped[Optional[str]] = mapped_column(String(50))
    tax_inclusive: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_rate: Mapped[float] = mapped_column(Float, default=0.15) # Deprecated
    # Tax & VAT Settings
    is_vat_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    prices_include_vat: Mapped[bool] = mapped_column(Boolean, default=False)
    apply_vat_to_shipping: Mapped[bool] = mapped_column(Boolean, default=False)
    display_prices_with_vat: Mapped[bool] = mapped_column(Boolean, default=False)
    default_tax_rate: Mapped[float] = mapped_column(Float, default=0.0) # General tax rate if no country specific

    # Staff Notifications
    staff_notifications: Mapped[Dict] = mapped_column(JSON, default={
        "new": False,
        "processing": False,
        "ready": False,
        "delivering": False,
        "completed": False,
        "cancelled": False
    })
    staff_emails: Mapped[Dict] = mapped_column(JSON, default=[]) # List of email strings
    
    # Question Notifications
    is_question_customer_notification_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_question_merchant_notification_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    question_notification_email: Mapped[Optional[str]] = mapped_column(String(255))

    # Store Information (New Fields)
    store_desc: Mapped[Optional[str]] = mapped_column(String(500))
    commercial_activity_type: Mapped[Optional[str]] = mapped_column(String(50))
    commercial_name: Mapped[Optional[str]] = mapped_column(String(255))
    commercial_registration_number: Mapped[Optional[str]] = mapped_column(String(50))
    commercial_registration_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_manager_owner: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_name: Mapped[Optional[str]] = mapped_column(String(100))
    owner_phone: Mapped[Optional[str]] = mapped_column(String(50))
    show_address_in_storefront: Mapped[bool] = mapped_column(Boolean, default=False)
    use_google_maps_location: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[Optional[str]] = mapped_column(String(50))
    address_street: Mapped[Optional[str]] = mapped_column(String(255))
    address_city: Mapped[Optional[str]] = mapped_column(String(100))
    address_country: Mapped[Optional[str]] = mapped_column(String(100))
    address_lat: Mapped[Optional[float]] = mapped_column(Float)
    address_lng: Mapped[Optional[float]] = mapped_column(Float)

    # Detailed Commercial Fields
    national_id: Mapped[Optional[str]] = mapped_column(String(50))
    branches_count: Mapped[Optional[int]] = mapped_column(Integer)
    employees_count: Mapped[Optional[int]] = mapped_column(Integer)
    electronic_activity: Mapped[Optional[str]] = mapped_column(String(100))
    electronic_activity_type: Mapped[Optional[str]] = mapped_column(String(100))

    # File URLs
    national_id_image: Mapped[Optional[str]] = mapped_column(String(500))
    tax_certificate_image: Mapped[Optional[str]] = mapped_column(String(500))
    freelance_certificate_image: Mapped[Optional[str]] = mapped_column(String(500))
    ecommerce_auth_certificate_image: Mapped[Optional[str]] = mapped_column(String(500))
    bank_certificate_image: Mapped[Optional[str]] = mapped_column(String(500))
    activity_license_image: Mapped[Optional[str]] = mapped_column(String(500))
    commercial_registration_image_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Maintenance Mode / Working Hours
    maintenance_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_type: Mapped[str] = mapped_column(String(50), default="fully_closed") # 'fully_closed', 'stop_orders'
    maintenance_period_type: Mapped[str] = mapped_column(String(50), default="unlimited") # 'unlimited', 'minutes', 'hours', 'scheduled'
    maintenance_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    maintenance_hours: Mapped[Optional[int]] = mapped_column(Integer)
    maintenance_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    maintenance_end_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    maintenance_show_countdown: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_title_ar: Mapped[Optional[str]] = mapped_column(String(255))
    maintenance_title_en: Mapped[Optional[str]] = mapped_column(String(255))
    maintenance_message_ar: Mapped[Optional[str]] = mapped_column(String(1000))
    maintenance_message_en: Mapped[Optional[str]] = mapped_column(String(1000))
    maintenance_daily_schedule: Mapped[Dict] = mapped_column(JSON, default={})


class NotificationEventType(str, PyEnum):
    ORDER_CREATED = "order_created"
    ORDER_PROCESSING = "order_processing"
    ORDER_READY = "order_ready"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    ORDER_COMPLETED = "order_completed"
    ORDER_CANCELLED = "order_cancelled"

class NotificationChannel(str, PyEnum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"

class NotificationTemplate(TimeStampedModel):
    __tablename__ = "notification_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(Integer, default=1) # Single store for now
    event_type: Mapped[NotificationEventType] = mapped_column(Enum(NotificationEventType))
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    message_template_ar: Mapped[Optional[str]] = mapped_column(String(500))
    message_template_en: Mapped[Optional[str]] = mapped_column(String(500))


class LegalPage(TimeStampedModel):
    __tablename__ = "legal_pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True) # privacy, terms, refund, complaints, license
    title_ar: Mapped[str] = mapped_column(String(255))
    title_en: Mapped[str] = mapped_column(String(255))
    content_ar: Mapped[Optional[str]] = mapped_column(String) # Text or HTML
    content_en: Mapped[Optional[str]] = mapped_column(String)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    is_customer_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    locations: Mapped[Dict] = mapped_column(JSON, default=["footer"]) # 'footer', 'header', etc.



class PaymentConfig(TimeStampedModel):
    __tablename__ = "payment_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(100), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[Dict] = mapped_column(JSON, default={})

class ShippingRule(TimeStampedModel):
    __tablename__ = "shipping_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    zone: Mapped[str] = mapped_column(String(100), default="All")
    condition_type: Mapped[ShippingConditionType] = mapped_column(Enum(ShippingConditionType), default=ShippingConditionType.FIXED)
    condition_value: Mapped[float] = mapped_column(Float, default=0.0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class StoreLanguage(TimeStampedModel):
    __tablename__ = "store_languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)  # e.g., 'ar', 'en'
    name: Mapped[str] = mapped_column(String(50))  # e.g., 'Arabic'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_code: Mapped[Optional[str]] = mapped_column(String(10))  # For UI flag icon

class Currency(TimeStampedModel):
    __tablename__ = "store_currencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)  # e.g., 'SAR', 'USD'
    name: Mapped[str] = mapped_column(String(50))
    symbol: Mapped[str] = mapped_column(String(10))  # e.g., 'ر.س', '$'
    exchange_rate: Mapped[float] = mapped_column(Float, default=1.0)  # Relative to default currency
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

class AddressCollectionMethod(str, PyEnum):
    MAP = "map"
    MANUAL = "manual"
    GOOGLE_AUTOCOMPLETE = "google_autocomplete"

class CheckoutConfig(TimeStampedModel):
    __tablename__ = "checkout_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    address_collection_method: Mapped[AddressCollectionMethod] = mapped_column(Enum(AddressCollectionMethod), default=AddressCollectionMethod.MAP)
    enable_apple_pay_quick: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_sms_login: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_email_login: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_whatsapp_login: Mapped[bool] = mapped_column(Boolean, default=False)
    show_apple_pay_on_other_browsers: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_stacked_discounts: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_guest_checkout: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled_payment_methods: Mapped[Dict] = mapped_column(JSON, default=["online", "cod", "bank_transfer"])
    enable_customer_notes: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_one_step_checkout: Mapped[bool] = mapped_column(Boolean, default=True)
    show_pickup_items: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_b2b_checkout: Mapped[bool] = mapped_column(Boolean, default=False)

class GiftingConfig(TimeStampedModel):
    __tablename__ = "gifting_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_custom_message: Mapped[bool] = mapped_column(Boolean, default=True)
    price_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    service_fee: Mapped[float] = mapped_column(Float, default=0.0)

class InvoiceConfig(TimeStampedModel):
    __tablename__ = "invoice_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    create_invoice_automatically: Mapped[bool] = mapped_column(Boolean, default=True)
    email_invoice_to_admin: Mapped[bool] = mapped_column(Boolean, default=True)
    email_invoice_to_customer: Mapped[bool] = mapped_column(Boolean, default=True)
    show_qr_code: Mapped[bool] = mapped_column(Boolean, default=True)
    show_barcode: Mapped[bool] = mapped_column(Boolean, default=True)
    show_order_status: Mapped[bool] = mapped_column(Boolean, default=False)
    show_expected_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    show_sku: Mapped[bool] = mapped_column(Boolean, default=False)
    show_product_image: Mapped[bool] = mapped_column(Boolean, default=False)
    show_weight: Mapped[bool] = mapped_column(Boolean, default=False)
    show_discount_code: Mapped[bool] = mapped_column(Boolean, default=False)
    show_tax_number: Mapped[bool] = mapped_column(Boolean, default=True)
    show_product_description: Mapped[bool] = mapped_column(Boolean, default=True)

class OrderSettings(TimeStampedModel):
    __tablename__ = "order_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_guest_checkout_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_complete_paid_orders: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_ready_paid_orders: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_reorder: Mapped[bool] = mapped_column(Boolean, default=False)
    min_order_limit_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    min_order_limit: Mapped[float] = mapped_column(Float, default=0.0)
    max_order_limit_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    max_order_limit: Mapped[float] = mapped_column(Float, default=0.0)

class ProductSettings(TimeStampedModel):
    __tablename__ = "product_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    show_similar_products: Mapped[bool] = mapped_column(Boolean, default=True)
    return_cancelled_quantity: Mapped[bool] = mapped_column(Boolean, default=True) # Return products to stock when order is cancelled
    show_similar_on_product_page: Mapped[bool] = mapped_column(Boolean, default=True)
    similar_products_limit: Mapped[int] = mapped_column(Integer, default=4)
    show_low_stock_warning: Mapped[bool] = mapped_column(Boolean, default=True) # Show remaining qty when low
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10)
    set_max_quantity_per_cart: Mapped[bool] = mapped_column(Boolean, default=False) # Limit max qty per product purchase
    max_quantity_per_cart: Mapped[int] = mapped_column(Integer, default=10)
    show_purchase_count: Mapped[bool] = mapped_column(Boolean, default=True)
    min_purchase_count_to_show: Mapped[int] = mapped_column(Integer, default=0)
    show_out_of_stock_at_end: Mapped[bool] = mapped_column(Boolean, default=False)


class ShippingConstraint(TimeStampedModel):
    __tablename__ = "shipping_constraints"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    shipping_company_ids: Mapped[Dict] = mapped_column(JSON, default=[]) # List of IDs/Names
    custom_error_message: Mapped[Optional[str]] = mapped_column(String(500))
    is_custom_error_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    conditions: Mapped[list["ShippingConstraintCondition"]] = relationship("ShippingConstraintCondition", back_populates="constraint", cascade="all, delete-orphan")

class ShippingConstraintCondition(TimeStampedModel):
    __tablename__ = "shipping_constraint_conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    constraint_id: Mapped[int] = mapped_column(ForeignKey("shipping_constraints.id"))
    type: Mapped[str] = mapped_column(String(50)) # CART_TOTAL, PRODUCT, etc.
    operator: Mapped[Optional[str]] = mapped_column(String(20)) # EQ, GT, LT, IN
    value: Mapped[Dict] = mapped_column(JSON, default={}) # {min: 10, max: 100} or [ids]

    constraint: Mapped["ShippingConstraint"] = relationship("ShippingConstraint", back_populates="conditions")


class PaymentConstraint(TimeStampedModel):
    __tablename__ = "payment_constraints"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    payment_method_ids: Mapped[Dict] = mapped_column(JSON, default=[]) # List of Strings (cod, stripe, etc.)
    custom_error_message: Mapped[Optional[str]] = mapped_column(String(500))
    is_custom_error_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    conditions: Mapped[list["PaymentConstraintCondition"]] = relationship("PaymentConstraintCondition", back_populates="constraint", cascade="all, delete-orphan")


class PaymentConstraintCondition(TimeStampedModel):
    __tablename__ = "payment_constraint_conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    constraint_id: Mapped[int] = mapped_column(ForeignKey("payment_constraints.id"))
    type: Mapped[str] = mapped_column(String(50)) 
    operator: Mapped[Optional[str]] = mapped_column(String(20))
    value: Mapped[Dict] = mapped_column(JSON, default={}) 

    constraint: Mapped["PaymentConstraint"] = relationship("PaymentConstraint", back_populates="conditions")

class CountryTax(TimeStampedModel):
    __tablename__ = "country_taxes"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_code: Mapped[str] = mapped_column(String(10)) # unique per store ideally, but simple here
    country_name: Mapped[str] = mapped_column(String(100))
    tax_number: Mapped[Optional[str]] = mapped_column(String(50))
    tax_rate: Mapped[float] = mapped_column(Float, default=0.0)
    vat_certificate_url: Mapped[Optional[str]] = mapped_column(String(500))
    # Footer display options
    display_tax_number_in_footer: Mapped[bool] = mapped_column(Boolean, default=True)
    display_vat_certificate_in_footer: Mapped[bool] = mapped_column(Boolean, default=True)
