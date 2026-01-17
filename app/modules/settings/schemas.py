from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.modules.settings.models import AddressCollectionMethod

class CheckoutConfigUpdate(BaseModel):
    address_collection_method: Optional[AddressCollectionMethod] = None
    enable_apple_pay_quick: Optional[bool] = None
    enable_sms_login: Optional[bool] = None
    enable_email_login: Optional[bool] = None
    is_email_mandatory: Optional[bool] = None
    enable_whatsapp_login: Optional[bool] = None
    show_apple_pay_on_other_browsers: Optional[bool] = None
    enable_stacked_discounts: Optional[bool] = None
    allow_guest_checkout: Optional[bool] = None
    enabled_payment_methods: Optional[List[str]] = None
    enable_customer_notes: Optional[bool] = None
    enable_one_step_checkout: Optional[bool] = None
    show_pickup_items: Optional[bool] = None
    allow_b2b_checkout: Optional[bool] = None

class CheckoutConfigResponse(CheckoutConfigUpdate):
    id: int

    class Config:
        from_attributes = True

class GiftingConfigUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    enable_custom_message: Optional[bool] = None
    price_visible: Optional[bool] = None
class GiftingConfigUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    enable_custom_message: Optional[bool] = None
    price_visible: Optional[bool] = None
    service_fee: Optional[float] = None

class InvoiceConfigUpdate(BaseModel):
    create_invoice_automatically: Optional[bool] = None
    email_invoice_to_admin: Optional[bool] = None
    email_invoice_to_customer: Optional[bool] = None
    show_qr_code: Optional[bool] = None
    show_barcode: Optional[bool] = None
    show_order_status: Optional[bool] = None
    show_expected_delivery: Optional[bool] = None
    show_sku: Optional[bool] = None
    show_product_image: Optional[bool] = None
    show_weight: Optional[bool] = None
    show_discount_code: Optional[bool] = None
    show_tax_number: Optional[bool] = None
    show_product_description: Optional[bool] = None

class OrderSettingsUpdate(BaseModel):
    is_guest_checkout_enabled: Optional[bool] = None
    auto_complete_paid_orders: Optional[bool] = None
    auto_ready_paid_orders: Optional[bool] = None
    enable_reorder: Optional[bool] = None
    min_order_limit_enabled: Optional[bool] = None
    min_order_limit: Optional[float] = None
    max_order_limit_enabled: Optional[bool] = None
    max_order_limit: Optional[float] = None

class ProductSettingsUpdate(BaseModel):
    show_similar_products: Optional[bool] = None
    return_cancelled_quantity: Optional[bool] = None
    show_similar_on_product_page: Optional[bool] = None
    similar_products_limit: Optional[int] = None
    show_low_stock_warning: Optional[bool] = None
    low_stock_threshold: Optional[int] = None
    set_max_quantity_per_cart: Optional[bool] = None
    max_quantity_per_cart: Optional[int] = None
    show_purchase_count: Optional[bool] = None
    min_purchase_count_to_show: Optional[int] = None
    show_out_of_stock_at_end: Optional[bool] = None

# Shipping Constraints Schemas
from typing import Dict, List, Any

class ShippingConstraintConditionCreate(BaseModel):
    type: str # CART_TOTAL, PRODUCT, etc.
    operator: Optional[str] = None # EQ, GT, LT, IN
    value: Dict[str, Any] # {min: 10, max: 100} or [ids]

class ShippingConstraintConditionRead(ShippingConstraintConditionCreate):
    id: int
    constraint_id: int

    class Config:
        from_attributes = True

class ShippingConstraintBase(BaseModel):
    name: str
    is_active: bool = True
    shipping_company_ids: List[str] = [] # List of IDs/Names
    custom_error_message: Optional[str] = None
    is_custom_error_enabled: bool = False

class ShippingConstraintCreate(ShippingConstraintBase):
    conditions: List[ShippingConstraintConditionCreate] = []

class ShippingConstraintUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    shipping_company_ids: Optional[List[str]] = None
    custom_error_message: Optional[str] = None
    is_custom_error_enabled: Optional[bool] = None
    conditions: Optional[List[ShippingConstraintConditionCreate]] = None

class ShippingConstraintRead(ShippingConstraintBase):
    id: int
    conditions: List[ShippingConstraintConditionRead] = []

    class Config:
        from_attributes = True

# Payment Constraints Schemas

class PaymentConstraintConditionCreate(BaseModel):
    type: str 
    operator: Optional[str] = None 
    value: Dict[str, Any] 

class PaymentConstraintConditionRead(PaymentConstraintConditionCreate):
    id: int
    constraint_id: int

    class Config:
        from_attributes = True

class PaymentConstraintBase(BaseModel):
    name: str
    is_active: bool = True
    payment_method_ids: List[str] = [] 
    custom_error_message: Optional[str] = None
    is_custom_error_enabled: bool = False

class PaymentConstraintCreate(PaymentConstraintBase):
    conditions: List[PaymentConstraintConditionCreate] = []

class PaymentConstraintUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    payment_method_ids: Optional[List[str]] = None
    custom_error_message: Optional[str] = None
    is_custom_error_enabled: Optional[bool] = None
    conditions: Optional[List[PaymentConstraintConditionCreate]] = None

class PaymentConstraintRead(PaymentConstraintBase):
    id: int
    conditions: List[PaymentConstraintConditionRead] = []

    class Config:
        from_attributes = True

class StoreSettingsUpdate(BaseModel):
    store_name: Optional[str] = None
    logo_url: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    iban: Optional[str] = None
    vat_id: Optional[str] = None
    tax_inclusive: Optional[bool] = None
    is_vat_enabled: Optional[bool] = None
    prices_include_vat: Optional[bool] = None
    apply_vat_to_shipping: Optional[bool] = None
    display_prices_with_vat: Optional[bool] = None
    default_tax_rate: Optional[float] = None
    staff_notifications: Optional[Dict] = None
    staff_emails: Optional[List[str]] = None
    is_question_customer_notification_enabled: Optional[bool] = None
    is_question_merchant_notification_enabled: Optional[bool] = None
    question_notification_email: Optional[str] = None
    store_desc: Optional[str] = None
    commercial_activity_type: Optional[str] = None
    commercial_name: Optional[str] = None
    commercial_registration_number: Optional[str] = None
    commercial_registration_name: Optional[str] = None
    is_manager_owner: Optional[bool] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    show_address_in_storefront: Optional[bool] = None
    use_google_maps_location: Optional[bool] = None
    timezone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_country: Optional[str] = None
    address_lat: Optional[float] = None
    address_lng: Optional[float] = None
    national_id: Optional[str] = None
    branches_count: Optional[int] = None
    employees_count: Optional[int] = None
    electronic_activity: Optional[str] = None
    electronic_activity_type: Optional[str] = None
    national_id_image: Optional[str] = None
    tax_certificate_image: Optional[str] = None
    freelance_certificate_image: Optional[str] = None
    ecommerce_auth_certificate_image: Optional[str] = None
    bank_certificate_image: Optional[str] = None
    activity_license_image: Optional[str] = None
    commercial_registration_image_url: Optional[str] = None

# Notification Template Schemas
class NotificationTemplateBase(BaseModel):
    event_type: str
    channel: str
    is_enabled: bool = True
    message_template_ar: Optional[str] = ""
    message_template_en: Optional[str] = ""

class NotificationTemplateCreate(NotificationTemplateBase):
    pass

class NotificationTemplateUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    message_template_ar: Optional[str] = None
    message_template_en: Optional[str] = None

    # Maintenance Mode
    maintenance_mode_enabled: Optional[bool] = None
    maintenance_type: Optional[str] = None
    maintenance_period_type: Optional[str] = None
    maintenance_minutes: Optional[int] = None
    maintenance_hours: Optional[int] = None
    maintenance_start_at: Optional[datetime] = None
    maintenance_end_at: Optional[datetime] = None
    maintenance_show_countdown: Optional[bool] = None
    maintenance_title_ar: Optional[str] = None
    maintenance_title_en: Optional[str] = None
    maintenance_message_ar: Optional[str] = None
    maintenance_message_en: Optional[str] = None
    maintenance_daily_schedule: Optional[Dict] = None

class NotificationTemplateResponse(NotificationTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

# ----------------------------------------------------------------------
# Work Group Schemas
# ----------------------------------------------------------------------
class WorkGroupBase(BaseModel):
    name: str
    permissions: Dict = {}

class WorkGroupCreate(WorkGroupBase):
    user_ids: List[int] = []

class WorkGroupUpdate(WorkGroupBase):
    user_ids: List[int] = []

class UserInGroup(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class WorkGroupResponse(WorkGroupBase):
    id: int
    users_count: int = 0
    users: List[UserInGroup] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------------------------------------------------------------
# Team Member Schemas
# ----------------------------------------------------------------------

class TeamMemberBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: str = "staff" # 'staff' or 'admin' or 'merchant'
    group_id: Optional[int] = None
    is_active: bool = True

class TeamMemberCreate(TeamMemberBase):
    password: str

class TeamMemberUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None # Optional password reset

class TeamMemberResponse(TeamMemberBase):
    id: int
    group: Optional["WorkGroupResponse"] = None   # To show group name
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CountryTaxBase(BaseModel):
    country_code: str
    country_name: str
    tax_number: Optional[str] = None
    tax_rate: float = 0.0
    vat_certificate_url: Optional[str] = None
    display_tax_number_in_footer: bool = True
    display_vat_certificate_in_footer: bool = True

class CountryTaxCreate(CountryTaxBase):
    pass

class CountryTaxUpdate(BaseModel):
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    tax_number: Optional[str] = None
    tax_rate: Optional[float] = None
    vat_certificate_url: Optional[str] = None
    display_tax_number_in_footer: Optional[bool] = None
    display_vat_certificate_in_footer: Optional[bool] = None

class CountryTaxResponse(CountryTaxBase):
    id: int

    class Config:
        from_attributes = True


class LegalPageBase(BaseModel):
    slug: str
    title_ar: str
    title_en: str
    content_ar: Optional[str] = None
    content_en: Optional[str] = None
    is_visible: bool = True
    is_customer_visible: bool = True
    locations: List[str] = ["footer"]

class LegalPageUpdate(BaseModel):
    title_ar: Optional[str] = None
    title_en: Optional[str] = None
    content_ar: Optional[str] = None
    content_en: Optional[str] = None
    is_visible: Optional[bool] = None
    is_customer_visible: Optional[bool] = None
    locations: Optional[List[str]] = None

class LegalPageResponse(LegalPageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
