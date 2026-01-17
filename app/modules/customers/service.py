from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .models import Customer
from . import schemas, models
from .schemas import CustomerCreate, CustomerUpdate
from typing import List, Optional

async def get_customers(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Customer]:
    stmt = select(Customer).where(Customer.is_active == True).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_customer(session: AsyncSession, customer_id: int) -> Optional[Customer]:
    result = await session.execute(select(Customer).where(Customer.id == customer_id))
    return result.scalar_one_or_none()

async def create_customer(session: AsyncSession, customer_in: CustomerCreate) -> Customer:
    customer = Customer(**customer_in.model_dump())
    session.add(customer)
    await session.commit()
    await session.refresh(customer)
    return customer

async def update_customer(session: AsyncSession, customer_id: int, customer_in: CustomerUpdate) -> Optional[Customer]:
    customer = await get_customer(session, customer_id)
    if not customer:
        return None
    
    update_data = customer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
        
    await session.commit()
    await session.refresh(customer)
    return customer

async def create_customer_group(session: AsyncSession, group_in: schemas.CustomerGroupCreate):
    db_group = models.CustomerGroup(**group_in.model_dump())
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)
    return db_group

async def get_customer_groups(session: AsyncSession):
    result = await session.execute(select(models.CustomerGroup))
    groups = result.scalars().all()
    
    groups_with_counts = []
    for group in groups:
        count = await count_customers_in_group(session, group.criteria)
        group.customer_count = count
        groups_with_counts.append(group)
        
    return groups_with_counts

async def count_customers_in_group(session: AsyncSession, criteria: dict) -> int:
    query = select(func.count(models.Customer.id))
    
    if criteria.get("min_orders"):
        query = query.where(models.Customer.total_orders >= int(criteria["min_orders"]))
    
    if criteria.get("max_orders"):
         query = query.where(models.Customer.total_orders <= int(criteria["max_orders"]))
         
    if criteria.get("city"):
        query = query.where(models.Customer.city == criteria["city"])
        
    if criteria.get("gender"):
        query = query.where(models.Customer.gender == criteria["gender"])

    result = await session.execute(query)
    return result.scalar()

async def delete_customer_group(session: AsyncSession, group_id: int) -> bool:
    result = await session.execute(select(models.CustomerGroup).where(models.CustomerGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if group:
        await session.delete(group)
        await session.commit()
        return True
    return False

# --- Advanced Filtering ---
async def get_customers_with_filters(
    session: AsyncSession,
    status: str = None,
    search: str = None,
    country: str = None,
    city: str = None,
    gender: str = None,
    customer_type: str= None,
    channel: str = None,
    birth_month: int = None,
    orders_condition: str = None,
    orders_value: int = None,
    skip: int = 0,
    limit: int = 20
):
    """Get customers with advanced filtering"""
    query = select(Customer).where(Customer.deleted_at == None)
    
    # Status filter
    if status == 'active':
        query = query.where(Customer.is_active == True)
    elif status == 'blocked':
        query = query.where(Customer.is_active == False)
    
    # Search across name, email, mobile
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Customer.name.ilike(search_term)) |
            (Customer.email.ilike(search_term)) |
            (Customer.mobile.ilike(search_term))
        )
    
    # Country & City
    if country:
        query = query.where(Customer.country == country)
    if city:
        query = query.where(Customer.city == city)
    
    # Gender, Type, Channel
    if gender:
        query = query.where(Customer.gender == gender)
    if customer_type:
        query = query.where(Customer.customer_type == customer_type)
    if channel:
        query = query.where(Customer.channel == channel)
    
    # Birth month
    if birth_month:
        from sqlalchemy.sql import extract
        query = query.where(extract('month', Customer.dob) == birth_month)
    
    # Orders filtering
    if orders_condition and orders_value is not None:
        if orders_condition == 'gt':
            query = query.where(Customer.total_orders > orders_value)
        elif orders_condition == 'lt':
            query = query.where(Customer.total_orders < orders_value)
        elif orders_condition == 'eq':
            query = query.where(Customer.total_orders == orders_value)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    customers = result.scalars().all()
    
    return {
        "customers": customers,
        "total": total,
        "page": (skip // limit) + 1,
        "pages": (total + limit - 1) // limit
    }

# --- Soft Delete ---
async def soft_delete_customer(session: AsyncSession, customer_id: int) -> bool:
    """Soft delete a customer by setting deleted_at"""
    from datetime import datetime
    customer = await get_customer(session, customer_id)
    if not customer:
        return False
    
    customer.deleted_at = datetime.utcnow()
    await session.commit()
    return True

# --- Customer Orders ---
async def get_customer_orders(session: AsyncSession, customer_id: int):
    """Get all orders for a specific customer"""
    from app.modules.sales.models import Order
    stmt = select(Order).where(Order.customer_id == customer_id).order_by(Order.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()

# --- Customer Stats ---
async def get_customer_stats(session: AsyncSession, customer_id: int):
    """Get statistics for a customer"""
    from app.modules.sales.models import Order
    from sqlalchemy import and_
    
    # Total orders
    total_stmt = select(func.count(Order.id)).where(Order.customer_id == customer_id)
    total_result = await session.execute(total_stmt)
    total_orders = total_result.scalar()
    
    # Completed orders
    completed_stmt = select(func.count(Order.id)).where(
        and_(Order.customer_id == customer_id, Order.status == 'completed')
    )
    completed_result = await session.execute(completed_stmt)
    completed_orders = completed_result.scalar()
    
    # Total spent
    spent_stmt = select(func.sum(Order.total_amount)).where(
        and_(Order.customer_id == customer_id, Order.status == 'completed')
    )
    spent_result = await session.execute(spent_stmt)
    total_spent = spent_result.scalar() or 0
    
    # Average order value
    avg_order_value = total_spent / completed_orders if completed_orders > 0 else 0
    
    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "total_spent": total_spent,
        "average_order_value": avg_order_value
    }

# --- Export/Import (CSV) ---
async def export_customers_csv(session: AsyncSession):
    """Export all customers to CSV"""
    import csv
    import io
    
    customers = await get_customers(session, skip=0, limit=100000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Name', 'Email', 'Mobile', 'Country', 'City', 'Type', 'Gender', 'Channel', 'Points', 'Total Orders'])
    
    # Data
    for customer in customers:
        writer.writerow([
            customer.id,
            customer.name,
            customer.email or '',
            customer.mobile or '',
            customer.country,
            customer.city or '',
            customer.customer_type.value,
            customer.gender.value if customer.gender else '',
            customer.channel,
            customer.points,
            customer.total_orders
        ])
    
    return output.getvalue()

async def import_customers_csv(session: AsyncSession, file_content: str):
    """Import customers from CSV"""
    import csv
    import io
    
    reader = csv.DictReader(io.StringIO(file_content))
    imported_count = 0
    errors = []
    
    for row in reader:
        try:
            customer_data = {
                "name": row['Name'],
                "email": row.get('Email') or None,
                "mobile": row.get('Mobile') or None,
                "country": row.get('Country', 'Saudi Arabia'),
                "city": row.get('City') or None,
                "customer_type": row.get('Type', 'individual'),
                "gender": row.get('Gender') or None,
                "channel": row.get('Channel', 'Store')
            }
            
            customer = Customer(**customer_data)
            session.add(customer)
            imported_count += 1
        except Exception as e:
            errors.append(f"Row {reader.line_num}: {str(e)}")
    
    if not errors:
        await session.commit()
    
    return {
        "imported": imported_count,
        "errors": errors
    }
