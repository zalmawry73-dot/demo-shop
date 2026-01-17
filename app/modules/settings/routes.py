
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from typing import List
import shutil
import os
from fastapi import UploadFile, File
from pathlib import Path

from app.core.database import get_db
from app.dependencies import get_current_user
from app.modules.settings.models import StoreSettings, PaymentConfig, ShippingRule, ShippingConditionType, StoreLanguage, Currency, CheckoutConfig, AddressCollectionMethod, GiftingConfig, InvoiceConfig, OrderSettings, ProductSettings, CountryTax, NotificationTemplate, NotificationChannel, NotificationEventType, LegalPage
from app.modules.settings.schemas import CheckoutConfigUpdate, GiftingConfigUpdate, InvoiceConfigUpdate, OrderSettingsUpdate, ProductSettingsUpdate, StoreSettingsUpdate, CountryTaxCreate, CountryTaxUpdate, CountryTaxResponse, NotificationTemplateResponse, NotificationTemplateUpdate, LegalPageResponse, LegalPageUpdate, TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse
from app.modules.settings import schemas
from app.modules.auth.models import User, UserRole
from app.modules.auth import models as auth_models
from app.core.security import get_password_hash

router = APIRouter(tags=["Settings"])
templates = Jinja2Templates(directory="templates")

@router.get("/settings")
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/settings/staff-notifications")
async def staff_notifications_page(request: Request):
    return templates.TemplateResponse("settings/staff_notifications.html", {"request": request})

@router.get("/settings/notifications/orders")
async def order_notifications_page(request: Request):
    return templates.TemplateResponse("settings/order_notifications.html", {"request": request})

@router.get("/settings/communications/questions")
async def questions_notifications_page(request: Request):
    return templates.TemplateResponse("settings/communications/questions.html", {"request": request})

@router.get("/settings/information")
async def information_settings_page(request: Request):
    return templates.TemplateResponse("settings/information/index.html", {"request": request})

@router.get("/settings/maintenance")
async def maintenance_settings_page(request: Request):
    return templates.TemplateResponse("settings/maintenance/index.html", {"request": request})


@router.get("/api/settings/notifications/templates", response_model=List[NotificationTemplateResponse])
async def get_notification_templates(channel: str = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(NotificationTemplate)
    if channel:
        stmt = stmt.where(NotificationTemplate.channel == channel)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.put("/api/settings/notifications/templates/{template_id}")
async def update_notification_template(template_id: int, data: NotificationTemplateUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    
    await db.commit()
    await db.refresh(template)
    return template

@router.get("/api/settings/general")
async def get_general_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(StoreSettings).limit(1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    if not settings:
        settings = StoreSettings()
        db.add(settings)
        await db.commit()
    return settings

    return settings

@router.put("/api/settings/store")
async def update_store_settings(data: StoreSettingsUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(StoreSettings).limit(1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    if not settings:
        settings = StoreSettings()
        db.add(settings)
    
    settings_data = data.dict(exclude_unset=True)
    for key, value in settings_data.items():
        setattr(settings, key, value)
    
    await db.commit()
    await db.refresh(settings)
    return settings

@router.get("/api/settings/payment")
async def get_payment_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(PaymentConfig)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/api/settings/shipping")
async def get_shipping_rules(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ShippingRule)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/api/settings/shipping")
async def create_shipping_rule(rule: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_rule = ShippingRule(
        name=rule['name'],
        zone=rule.get('zone', 'All'),
        condition_type=rule.get('condition_type', 'fixed'),
        condition_value=float(rule.get('condition_value', 0)),
        cost=float(rule['cost'])
    )
    db.add(new_rule)
    await db.commit()
    return new_rule

# Languages & Currencies Page
@router.get("/settings/languages-currencies")
async def languages_currencies_page(request: Request):
    return templates.TemplateResponse("settings/languages_currencies.html", {"request": request})

# Languages APIs
@router.get("/api/settings/languages")
async def get_languages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StoreLanguage))
    return result.scalars().all()

@router.post("/api/settings/languages")
async def create_language(data: dict, db: AsyncSession = Depends(get_db)):
    # Check if code already exists
    existing = await db.execute(select(StoreLanguage).where(StoreLanguage.code == data['code']))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Language code already exists")
    
    # If this is the first language, make it default
    all_langs = await db.execute(select(StoreLanguage))
    is_first = len(all_langs.scalars().all()) == 0
    
    new_lang = StoreLanguage(
        code=data['code'],
        name=data['name'],
        flag_code=data.get('flag_code'),
        is_active=data.get('is_active', True),
        is_default=is_first or data.get('is_default', False)
    )
    db.add(new_lang)
    await db.commit()
    return new_lang

@router.put("/api/settings/languages/{lang_id}/default")
async def set_default_language(lang_id: int, db: AsyncSession = Depends(get_db)):
    # Unset previous default
    await db.execute(update(StoreLanguage).values(is_default=False))
    # Set new default
    lang = await db.get(StoreLanguage, lang_id)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    lang.is_default = True
    await db.commit()
    return {"message": "Default language updated"}

@router.put("/api/settings/languages/{lang_id}")
async def update_language(lang_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    lang = await db.get(StoreLanguage, lang_id)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    
    lang.name = data.get('name', lang.name)
    lang.code = data.get('code', lang.code)
    lang.flag_code = data.get('flag_code', lang.flag_code)
    lang.is_active = data.get('is_active', lang.is_active)
    
    await db.commit()
    return lang

# Currencies APIs
@router.get("/api/settings/currencies")
async def get_currencies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Currency))
    return result.scalars().all()

@router.post("/api/settings/currencies")
async def create_currency(data: dict, db: AsyncSession = Depends(get_db)):
    # Check if code already exists
    existing = await db.execute(select(Currency).where(Currency.code == data['code']))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Currency code already exists")
        
    # If this is the first currency, make it default
    all_currencies = await db.execute(select(Currency))
    is_first = len(all_currencies.scalars().all()) == 0

    new_currency = Currency(
        code=data['code'],
        name=data['name'],
        symbol=data['symbol'],
        exchange_rate=float(data.get('exchange_rate', 1.0)),
        is_active=data.get('is_active', True),
        is_default=is_first or data.get('is_default', False)
    )
    
    if new_currency.is_default:
        new_currency.exchange_rate = 1.0

    db.add(new_currency)
    await db.commit()
    return new_currency

@router.put("/api/settings/currencies/{curr_id}/default")
async def set_default_currency(curr_id: int, db: AsyncSession = Depends(get_db)):
    # Unset previous default
    await db.execute(update(Currency).values(is_default=False))
    
    # Set new default
    curr = await db.get(Currency, curr_id)
    if not curr:
        raise HTTPException(status_code=404, detail="Currency not found")
    curr.is_default = True
    curr.exchange_rate = 1.0 # Default currency always has rate 1.0
    
    await db.commit()
    return {"message": "Default currency updated"}

@router.put("/api/settings/currencies/{curr_id}")
async def update_currency(curr_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    curr = await db.get(Currency, curr_id)
    if not curr:
        raise HTTPException(status_code=404, detail="Currency not found")
        
    curr.name = data.get('name', curr.name)
    curr.code = data.get('code', curr.code)
    curr.symbol = data.get('symbol', curr.symbol)
    curr.exchange_rate = float(data.get('exchange_rate', curr.exchange_rate))
    curr.is_active = data.get('is_active', curr.is_active)
    
    if curr.is_default:
        curr.exchange_rate = 1.0
        
    await db.commit()
    return curr

@router.get("/settings/checkout")
async def checkout_settings_page(request: Request):
    return templates.TemplateResponse("settings/checkout_settings.html", {"request": request})

@router.get("/api/settings/checkout")
async def get_checkout_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(CheckoutConfig).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = CheckoutConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
    return config

@router.put("/api/settings/checkout")
async def update_checkout_settings(data: CheckoutConfigUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(CheckoutConfig).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = CheckoutConfig()
        db.add(config)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    await db.commit()
    await db.refresh(config)
    return config

@router.get("/settings/gifting")
async def gifting_settings_page(request: Request):
    return templates.TemplateResponse("settings/gifting_settings.html", {"request": request})

@router.get("/api/settings/gifting")
async def get_gifting_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(GiftingConfig).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = GiftingConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
    return config

@router.put("/api/settings/gifting")
async def update_gifting_settings(data: GiftingConfigUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(GiftingConfig).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = GiftingConfig()
        db.add(config)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    await db.commit()
    await db.refresh(config)
    return config

@router.get("/settings/invoice")
async def invoice_settings_page(request: Request):
    return templates.TemplateResponse("settings/invoice_settings.html", {"request": request})

@router.get("/api/settings/invoice")
async def get_invoice_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(InvoiceConfig).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = InvoiceConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
    return config

@router.put("/api/settings/invoice")
async def update_invoice_settings(data: InvoiceConfigUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(InvoiceConfig).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = InvoiceConfig()
        db.add(config)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    await db.commit()
    await db.refresh(config)
    return config

@router.get("/settings/orders-products")
async def orders_products_settings_page(request: Request):
    return templates.TemplateResponse("settings/orders_products.html", {"request": request})

@router.get("/api/settings/orders")
async def get_order_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(OrderSettings).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = OrderSettings()
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
    return config

@router.put("/api/settings/orders")
async def update_order_settings(data: OrderSettingsUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(OrderSettings).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = OrderSettings()
        db.add(config)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    await db.commit()
    await db.refresh(config)
    return config

@router.get("/api/settings/products")
async def get_product_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ProductSettings).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = ProductSettings()
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
    return config

@router.put("/api/settings/products")
async def update_product_settings(data: ProductSettingsUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ProductSettings).limit(1)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        config = ProductSettings()
        db.add(config)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    await db.commit()
    await db.refresh(config)
    return config

# Shipping Constraints APIs
from app.modules.settings.models import ShippingConstraint, ShippingConstraintCondition
from app.modules.settings.schemas import ShippingConstraintCreate, ShippingConstraintUpdate, ShippingConstraintRead, ShippingConstraintConditionCreate
from app.modules.settings.models import PaymentConstraint, PaymentConstraintCondition
from app.modules.settings.schemas import PaymentConstraintCreate, PaymentConstraintUpdate, PaymentConstraintRead, PaymentConstraintConditionCreate
from sqlalchemy.orm import selectinload

@router.get("/settings/constraints")
async def constraints_page(request: Request):
    return templates.TemplateResponse("settings/constraints/list.html", {"request": request})

@router.get("/settings/constraints/shipping/create")
async def constraints_create_page(request: Request):
    return templates.TemplateResponse("settings/constraints/shipping_form.html", {"request": request})

@router.get("/settings/constraints/shipping/{id}/edit")
async def constraints_edit_page(request: Request, id: int, db: AsyncSession = Depends(get_db)):
    constraint = await db.get(ShippingConstraint, id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    return templates.TemplateResponse("settings/constraints/shipping_form.html", {"request": request, "constraint": constraint})

@router.get("/api/settings/constraints/shipping", response_model=list[ShippingConstraintRead])
async def get_shipping_constraints(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ShippingConstraint).options(selectinload(ShippingConstraint.conditions))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/api/settings/constraints/shipping/{id}", response_model=ShippingConstraintRead)
async def get_shipping_constraint(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ShippingConstraint).where(ShippingConstraint.id == id).options(selectinload(ShippingConstraint.conditions))
    result = await db.execute(stmt)
    constraint = result.scalar_one_or_none()
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    return constraint

@router.post("/api/settings/constraints/shipping", response_model=ShippingConstraintRead)
async def create_shipping_constraint(data: ShippingConstraintCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Create constraint
    new_constraint = ShippingConstraint(
        name=data.name,
        is_active=data.is_active,
        shipping_company_ids=data.shipping_company_ids,
        custom_error_message=data.custom_error_message,
        is_custom_error_enabled=data.is_custom_error_enabled
    )
    db.add(new_constraint)
    await db.flush() # Get ID

    # Create conditions
    for condition_data in data.conditions:
        new_condition = ShippingConstraintCondition(
            constraint_id=new_constraint.id,
            type=condition_data.type,
            operator=condition_data.operator,
            value=condition_data.value
        )
        db.add(new_condition)

    await db.commit()
    # Refresh with relations
    stmt = select(ShippingConstraint).where(ShippingConstraint.id == new_constraint.id).options(selectinload(ShippingConstraint.conditions))
    result = await db.execute(stmt)
    return result.scalar_one()

@router.put("/api/settings/constraints/shipping/{id}", response_model=ShippingConstraintRead)
async def update_shipping_constraint(id: int, data: ShippingConstraintUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ShippingConstraint).where(ShippingConstraint.id == id).options(selectinload(ShippingConstraint.conditions))
    result = await db.execute(stmt)
    constraint = result.scalar_one_or_none()
    
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    
    # Update fields
    if data.name is not None: constraint.name = data.name
    if data.is_active is not None: constraint.is_active = data.is_active
    if data.shipping_company_ids is not None: constraint.shipping_company_ids = data.shipping_company_ids
    if data.custom_error_message is not None: constraint.custom_error_message = data.custom_error_message
    if data.is_custom_error_enabled is not None: constraint.is_custom_error_enabled = data.is_custom_error_enabled

    # Update conditions if provided (Full replacement)
    if data.conditions is not None:
        constraint.conditions.clear() # Triggers delete-orphan
        
        for condition_data in data.conditions:
            new_condition = ShippingConstraintCondition(
                type=condition_data.type,
                operator=condition_data.operator,
                value=condition_data.value
            )
            constraint.conditions.append(new_condition)

    await db.commit()
    await db.refresh(constraint)
    return constraint


@router.delete("/api/settings/constraints/shipping/{id}")
async def delete_shipping_constraint(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    constraint = await db.get(ShippingConstraint, id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    
    await db.delete(constraint)
    await db.commit()
    return {"message": "Constraint deleted"}


# Payment Constraints APIs

@router.get("/settings/constraints/payment/create")
async def constraints_payment_create_page(request: Request):
    return templates.TemplateResponse("settings/constraints/payment_form.html", {"request": request})

@router.get("/settings/constraints/payment/{id}/edit")
async def constraints_payment_edit_page(request: Request, id: int, db: AsyncSession = Depends(get_db)):
    constraint = await db.get(PaymentConstraint, id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    return templates.TemplateResponse("settings/constraints/payment_form.html", {"request": request, "constraint": constraint})

@router.get("/api/settings/constraints/payment", response_model=list[PaymentConstraintRead])
async def get_payment_constraints(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(PaymentConstraint).options(selectinload(PaymentConstraint.conditions))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/api/settings/constraints/payment/{id}", response_model=PaymentConstraintRead)
async def get_payment_constraint(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(PaymentConstraint).where(PaymentConstraint.id == id).options(selectinload(PaymentConstraint.conditions))
    result = await db.execute(stmt)
    constraint = result.scalar_one_or_none()
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    return constraint

@router.post("/api/settings/constraints/payment", response_model=PaymentConstraintRead)
async def create_payment_constraint(data: PaymentConstraintCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_constraint = PaymentConstraint(
        name=data.name,
        is_active=data.is_active,
        payment_method_ids=data.payment_method_ids,
        custom_error_message=data.custom_error_message,
        is_custom_error_enabled=data.is_custom_error_enabled
    )
    db.add(new_constraint)
    await db.flush() 

    for condition_data in data.conditions:
        new_condition = PaymentConstraintCondition(
            constraint_id=new_constraint.id,
            type=condition_data.type,
            operator=condition_data.operator,
            value=condition_data.value
        )
        db.add(new_condition)

    await db.commit()
    stmt = select(PaymentConstraint).where(PaymentConstraint.id == new_constraint.id).options(selectinload(PaymentConstraint.conditions))
    result = await db.execute(stmt)
    return result.scalar_one()

@router.put("/api/settings/constraints/payment/{id}", response_model=PaymentConstraintRead)
async def update_payment_constraint(id: int, data: PaymentConstraintUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(PaymentConstraint).where(PaymentConstraint.id == id).options(selectinload(PaymentConstraint.conditions))
    result = await db.execute(stmt)
    constraint = result.scalar_one_or_none()
    
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    
    if data.name is not None: constraint.name = data.name
    if data.is_active is not None: constraint.is_active = data.is_active
    if data.payment_method_ids is not None: constraint.payment_method_ids = data.payment_method_ids
    if data.custom_error_message is not None: constraint.custom_error_message = data.custom_error_message
    if data.is_custom_error_enabled is not None: constraint.is_custom_error_enabled = data.is_custom_error_enabled

    if data.conditions is not None:
        constraint.conditions.clear() 
        for condition_data in data.conditions:
            new_condition = PaymentConstraintCondition(
                type=condition_data.type,
                operator=condition_data.operator,
                value=condition_data.value
            )
            constraint.conditions.append(new_condition)

    await db.commit()
    await db.refresh(constraint)
    return constraint

@router.delete("/api/settings/constraints/payment/{id}")
async def delete_payment_constraint(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    constraint = await db.get(PaymentConstraint, id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    
    await db.delete(constraint)
    await db.commit()
    return {"message": "Constraint deleted"}

# ----------------------------------------------------------------------
# Tax Settings APIs
# ----------------------------------------------------------------------

@router.put("/api/settings/store")
async def update_store_settings(data: StoreSettingsUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(StoreSettings).limit(1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    if not settings:
        settings = StoreSettings()
        db.add(settings)
    
    settings_data = data.dict(exclude_unset=True)
    for key, value in settings_data.items():
        setattr(settings, key, value)
    
    await db.commit()
    await db.refresh(settings)
    return settings

@router.get("/settings/tax")
async def tax_settings_page(request: Request):
    return templates.TemplateResponse("settings/tax/index.html", {"request": request})

@router.get("/settings/tax/create")
async def create_tax_country_page(request: Request):
    return templates.TemplateResponse("settings/tax/create.html", {"request": request})

@router.post("/api/settings/tax/countries")
async def create_country_tax(data: CountryTaxCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check duplicate
    existing = await db.execute(select(CountryTax).where(CountryTax.country_code == data.country_code))
    if existing.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Country tax already exists")
         
    new_tax = CountryTax(**data.dict())
    db.add(new_tax)
    await db.commit()
    return new_tax

@router.get("/api/settings/tax/countries")
async def get_country_taxes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CountryTax))
    return result.scalars().all()

@router.delete("/api/settings/tax/countries/{tax_id}")
async def delete_country_tax(tax_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    tax = await db.get(CountryTax, tax_id)
    if not tax:
        raise HTTPException(status_code=404, detail="Tax rule not found")
    
    await db.delete(tax)
    await db.commit()
    await db.delete(tax)
    await db.commit()
    return {"message": "Deleted successfully"}

@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    upload_dir = Path("static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/static/uploads/{file.filename}"}


@router.get("/settings/maintenance")
async def maintenance_settings_page(request: Request):
    return templates.TemplateResponse("settings/maintenance/index.html", {"request": request})

# ----------------------------------------------------------------------
# Work Groups (Roles) Pages
# ----------------------------------------------------------------------

@router.get("/settings/team/groups")
async def team_groups_page(request: Request):
    return templates.TemplateResponse("settings/team/groups/index.html", {"request": request})

@router.get("/settings/team/groups/create")
async def create_team_group_page(request: Request):
    return templates.TemplateResponse("settings/team/groups/create.html", {"request": request})

@router.get("/settings/team/groups/{group_id}/edit")
async def edit_team_group_page(request: Request, group_id: int):
    return templates.TemplateResponse("settings/team/groups/create.html", {"request": request})

# ----------------------------------------------------------------------
# Team Members Pages
# ----------------------------------------------------------------------

@router.get("/settings/team")
async def team_list_page(request: Request):
    return templates.TemplateResponse("settings/team/index.html", {"request": request})

@router.get("/settings/team/create")
async def create_team_member_page(request: Request):
    return templates.TemplateResponse("settings/team/create.html", {"request": request})

@router.get("/settings/team/{user_id}/edit")
async def edit_team_member_page(request: Request, user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("settings/team/create.html", {"request": request, "user": user})

# ----------------------------------------------------------------------
# Team Members APIs
# ----------------------------------------------------------------------

# List Team Members
@router.get("/api/settings/team/members", response_model=List[TeamMemberResponse])
async def get_team_members(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Filter by STAFF or relevant roles if needed, or just all users for now
    # Ideally exclude customers if they are in the same table, but assume separate customer table or role check
    # Here we filter users who are NOT customers (assuming customers are in 'users' or handled elsewhere)
    # Based on UserRole enum: ADMIN, MERCHANT, STAFF
    stmt = select(User).where(User.role.in_([UserRole.STAFF, UserRole.ADMIN, UserRole.MERCHANT])).options(selectinload(User.group))
    result = await db.execute(stmt)
    return result.scalars().all()

# Create Team Member
@router.post("/api/settings/team/members", response_model=TeamMemberResponse)
async def create_team_member(data: TeamMemberCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check username/email uniqueness
    stmt = select(User).where((User.username == data.username) | (User.email == data.email))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Username or Email already exists")
    
    hashed_password = get_password_hash(data.password)
    
    new_user = User(
        username=data.username,
        email=data.email,
        password_hash=hashed_password,
        full_name=data.full_name,
        phone_number=data.phone_number,
        role=UserRole(data.role),
        group_id=data.group_id,
        is_active=data.is_active
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Reload with group for response
    stmt = select(User).where(User.id == new_user.id).options(selectinload(User.group))
    result = await db.execute(stmt)
    return result.scalar_one()

# Get Team Member
@router.get("/api/settings/team/members/{user_id}", response_model=TeamMemberResponse)
async def get_team_member(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(User).where(User.id == user_id).options(selectinload(User.group))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Update Team Member
@router.put("/api/settings/team/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member(user_id: int, data: TeamMemberUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(User).where(User.id == user_id).options(selectinload(User.group))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if data.full_name is not None: user.full_name = data.full_name
    if data.phone_number is not None: user.phone_number = data.phone_number
    if data.email is not None:
        # Check uniqueness if changed
        if data.email != user.email:
             stmt = select(User).where(User.email == data.email)
             if (await db.execute(stmt)).scalar_one_or_none():
                  raise HTTPException(status_code=400, detail="Email already exists")
        user.email = data.email
    
    if data.group_id is not None: user.group_id = data.group_id
    if data.is_active is not None: user.is_active = data.is_active
    
    if data.password:
        user.password_hash = get_password_hash(data.password)
        
    await db.commit()
    await db.refresh(user)
    return user

# Delete Team Member
@router.delete("/api/settings/team/members/{user_id}")
async def delete_team_member(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Optional: Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}

# ----------------------------------------------------------------------
# Work Groups (Roles) APIs
# ----------------------------------------------------------------------

# List Groups
@router.get("/api/settings/team/groups", response_model=List[schemas.WorkGroupResponse])
async def get_work_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(auth_models.WorkGroup).options(selectinload(auth_models.WorkGroup.users)))
    groups = result.scalars().all()
    # Populate user count (although Pydantic might not pick it up automatically from property if it's not a field, we handle it in schema default or property)
    # Schema expects users_count, we can annotate it or let the ORM handle if we added a property. 
    # For now manual population:
    for g in groups:
        g.users_count = len(g.users)
    return groups

# Create Group
@router.post("/api/settings/team/groups", response_model=schemas.WorkGroupResponse)
async def create_work_group(group_data: schemas.WorkGroupCreate, db: AsyncSession = Depends(get_db)):
    # Check name uniqueness
    existing = await db.execute(select(auth_models.WorkGroup).where(auth_models.WorkGroup.name == group_data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group name already exists")
    
    new_group = auth_models.WorkGroup(
        name=group_data.name,
        permissions=group_data.permissions
    )
    db.add(new_group)
    await db.flush() # Get ID
    
    # Assign users
    if group_data.user_ids:
        users_result = await db.execute(select(auth_models.User).where(auth_models.User.id.in_(group_data.user_ids)))
        users = users_result.scalars().all()
        # Async relationship assignment might fail if not loaded, but direct assignment usually works if we have the objects.
        # Safer to lazy load or just set the relationship.
        new_group.users = list(users) # Conversion to list for relationship
    
    await db.commit()
    await db.refresh(new_group)
    
    # Refresh to get users for count
    result = await db.execute(select(auth_models.WorkGroup).where(auth_models.WorkGroup.id == new_group.id).options(selectinload(auth_models.WorkGroup.users)))
    new_group = result.scalar_one()
    new_group.users_count = len(new_group.users)
    return new_group

# Get Group
@router.get("/api/settings/team/groups/{group_id}", response_model=schemas.WorkGroupResponse)
async def get_work_group(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(auth_models.WorkGroup).where(auth_models.WorkGroup.id == group_id).options(selectinload(auth_models.WorkGroup.users)))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    group.users_count = len(group.users)
    return group

# Update Group
@router.put("/api/settings/team/groups/{group_id}", response_model=schemas.WorkGroupResponse)
async def update_work_group(group_id: int, group_data: schemas.WorkGroupUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(auth_models.WorkGroup).where(auth_models.WorkGroup.id == group_id).options(selectinload(auth_models.WorkGroup.users)))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Check name uniqueness if changed
    if group_data.name != group.name:
        existing = await db.execute(select(auth_models.WorkGroup).where(auth_models.WorkGroup.name == group_data.name))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Group name already exists")
            
    group.name = group_data.name
    group.permissions = group_data.permissions
    
    # Update users
    if group_data.user_ids is not None: # Only update if sent
        users_result = await db.execute(select(auth_models.User).where(auth_models.User.id.in_(group_data.user_ids)))
        users = users_result.scalars().all()
        group.users = list(users)
        
    await db.commit()
    await db.refresh(group)
    group.users_count = len(group.users)
    return group

# Delete Group
@router.delete("/api/settings/team/groups/{group_id}")
async def delete_work_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await db.get(auth_models.WorkGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Manually unset user groups (if needed, or rely on nullability)
    # We should probably load users first to update them
    # But for now, let's just delete and let database handle (set null or cascade)
    # If we want to be explicit:
    # stmt = update(auth_models.User).where(auth_models.User.group_id == group_id).values(group_id=None)
    # await db.execute(stmt)
        
    await db.delete(group)
    await db.commit()
    return {"message": "Group deleted"}

# List Users for Selection
@router.get("/api/settings/team/users")
async def get_team_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(auth_models.User))
    users = result.scalars().all()
    return [{"id": u.id, "name": u.full_name or u.username, "avatar": None} for u in users]

# ----------------------------------------------------------------------
# Legal Pages APIs
# ----------------------------------------------------------------------

@router.get("/settings/legal-pages")
async def legal_pages_list_page(request: Request):
    return templates.TemplateResponse("settings/legal_pages/index.html", {"request": request})

@router.get("/settings/legal-pages/{id}")
async def legal_page_edit_page(request: Request, id: int, db: AsyncSession = Depends(get_db)):
    page = await db.get(LegalPage, id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return templates.TemplateResponse("settings/legal_pages/edit.html", {"request": request, "page": page})

@router.get("/api/settings/legal-pages", response_model=List[LegalPageResponse])
async def get_legal_pages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LegalPage))
    return result.scalars().all()

@router.put("/api/settings/legal-pages/{id}", response_model=LegalPageResponse)
async def update_legal_page(id: int, data: LegalPageUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    page = await db.get(LegalPage, id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(page, key, value)
    
    await db.commit()
    await db.refresh(page)
    return page
