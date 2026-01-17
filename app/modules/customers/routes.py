from fastapi import APIRouter, Depends, Query, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from . import service, schemas
from .models import CustomerType, Gender
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Stock Notifications Routes ---
from app.modules.catalog.schemas import StockNotificationCreate, StockNotificationSettingUpdate, StockNotificationResponse, StockNotificationStats

@router.get("/customers/stock-notifications", response_class=HTMLResponse)
async def list_stock_notifications_page(request: Request):
    return templates.TemplateResponse("customers/stock_notifications/list.html", {"request": request})

@router.get("/customers/stock-notifications/settings", response_class=HTMLResponse)
async def stock_notifications_settings_page(request: Request):
    return templates.TemplateResponse("customers/stock_notifications/settings.html", {"request": request})

@router.get("/api/stock-notifications/stats")
async def get_stock_notifications_stats(db: AsyncSession = Depends(get_db)):
    from app.modules.catalog.services import StockNotificationService
    service = StockNotificationService(db)
    return await service.get_stats()

@router.get("/api/stock-notifications")
async def list_stock_notifications(
    status: Optional[str] = None,
    search: Optional[str] = None,
    period: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    from app.modules.catalog.services import StockNotificationService
    service = StockNotificationService(db)
    return await service.get_all(status, search, period)

@router.post("/api/stock-notifications")
async def create_stock_notification(
    data: StockNotificationCreate,
    db: AsyncSession = Depends(get_db)
):
    from app.modules.catalog.services import StockNotificationService
    service = StockNotificationService(db)
    return await service.create(data)

@router.post("/api/stock-notifications/{notification_id}/send")
async def send_stock_notification(
    notification_id: str,
    channel: str = Query("email"), # email or sms
    db: AsyncSession = Depends(get_db)
):
    from app.modules.catalog.services import StockNotificationService
    service = StockNotificationService(db)
    success = await service.send_notification(notification_id, channel)
    return {"success": success}

@router.get("/api/stock-notifications/settings")
async def get_stock_notification_settings(db: AsyncSession = Depends(get_db)):
    from app.modules.catalog.services import StockNotificationService
    service = StockNotificationService(db)
    return await service.get_settings()

@router.put("/api/stock-notifications/settings")
async def update_stock_notification_settings(
    data: StockNotificationSettingUpdate,
    db: AsyncSession = Depends(get_db)
):
    from app.modules.catalog.services import StockNotificationService
    service = StockNotificationService(db)
    return await service.update_settings(data)

# --- Questions Routes ---
from app.modules.catalog.schemas import QuestionCreate, QuestionUpdate, QuestionStatusUpdate, QuestionResponse

@router.get("/customers/questions", response_class=HTMLResponse)
async def list_questions_page(request: Request):
    # Check if enabled (mocked logic or check existing questions count to decide intro vs list)
    # For now, we'll use a query param or default to list, assuming 'enable' action sets a flag or we just link to intro initially
    # Simplification: /customers/questions shows list. /customers/questions/intro shows intro.
    return templates.TemplateResponse("customers/questions/list.html", {"request": request})

@router.get("/customers/questions/intro", response_class=HTMLResponse)
async def questions_intro_page(request: Request):
    return templates.TemplateResponse("customers/questions/intro.html", {"request": request})

@router.get("/api/customers/questions")
async def list_questions_api(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = ReviewService(db) # We need QuestionService here, importing it
    # Dynamic import to avoid circular issues or just use the one from catalog.services
    from app.modules.catalog.services import QuestionService
    service = QuestionService(db)
    return await service.get_all(status, search)

@router.post("/api/customers/questions")
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    from app.modules.catalog.services import QuestionService
    service = QuestionService(db)
    return await service.create(data)

@router.put("/api/customers/questions/{question_id}/answer")
async def answer_question(
    question_id: str,
    data: QuestionUpdate,
    db: AsyncSession = Depends(get_db)
):
    from app.modules.catalog.services import QuestionService
    service = QuestionService(db)
    success = await service.answer_question(question_id, data.answer_text)
    return {"success": success}

@router.put("/api/customers/questions/{question_id}/status")
async def update_question_status(
    question_id: str,
    data: QuestionStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    from app.modules.catalog.services import QuestionService
    service = QuestionService(db)
    success = await service.update_status(question_id, data.status)
    return {"success": success}

@router.delete("/api/customers/questions/{question_id}")
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db)
):
    from app.modules.catalog.services import QuestionService
    service = QuestionService(db)
    success = await service.delete(question_id)
    return {"success": success}

# --- Reviews Routes ---
from app.modules.catalog.services import ReviewService
from app.modules.catalog.schemas import ReviewUpdateStatus, ReviewResponse

@router.get("/customers/reviews", response_class=HTMLResponse)
async def list_reviews_page(request: Request):
    return templates.TemplateResponse("customers/reviews/list.html", {"request": request})

@router.get("/customers/reviews/settings", response_class=HTMLResponse)
async def reviews_settings_page(request: Request):
    return templates.TemplateResponse("customers/reviews/settings.html", {"request": request})

@router.get("/api/customers/reviews")
async def list_reviews_api(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = ReviewService(db)
    return await service.get_all(status, search)

@router.put("/api/customers/reviews/{review_id}/status")
async def update_review_status(
    review_id: str,
    data: ReviewUpdateStatus,
    db: AsyncSession = Depends(get_db)
):
    service = ReviewService(db)
    success = await service.update_status(review_id, data.status)
    return {"success": success}

@router.delete("/api/customers/reviews/{review_id}")
async def delete_review(
    review_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = ReviewService(db)
    success = await service.delete(review_id)
    return {"success": success}

# --- HTML Routes ---
@router.get("/customers", response_class=HTMLResponse)
async def customers_list_page(request: Request):
    # JavaScript will load customers dynamically
    return templates.TemplateResponse("customers/list.html", {"request": request, "total": 0})

@router.get("/customers/create", response_class=HTMLResponse)
async def customer_create_page(request: Request):
    return templates.TemplateResponse("customers/create.html", {"request": request})

@router.get("/customers/{customer_id}", response_class=HTMLResponse)
async def customer_details_page(request: Request, customer_id: int, db: AsyncSession = Depends(get_db)):
    customer = await service.get_customer(db, customer_id)
    return templates.TemplateResponse("customers/details.html", {"request": request, "customer": customer})

@router.get("/customers/{customer_id}/edit", response_class=HTMLResponse)
async def customer_edit_page(request: Request, customer_id: int, db: AsyncSession = Depends(get_db)):
    customer = await service.get_customer(db, customer_id)
    return templates.TemplateResponse("customers/create.html", {"request": request, "customer": customer})

# --- API Routes ---
@router.post("/api/customers", response_model=schemas.CustomerResponse)
async def create_customer(customer: schemas.CustomerCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_customer(db, customer)

@router.get("/api/customers")
async def list_customers(
    status: Optional[str] = None,
    search: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    gender: Optional[str] = None,
    customer_type: Optional[str] = None,
    channel: Optional[str] = None,
    birth_month: Optional[int] = None,
    orders_condition: Optional[str] = None,
    orders_value: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Advanced customer listing with filtering"""
    skip = (page - 1) * limit
    return await service.get_customers_with_filters(
        db,
        status=status,
        search=search,
        country=country,
        city=city,
        gender=gender,
        customer_type=customer_type,
        channel=channel,
        birth_month=birth_month,
        orders_condition=orders_condition,
        orders_value=orders_value,
        skip=skip,
        limit=limit
    )

@router.put("/api/customers/{customer_id}", response_model=schemas.CustomerResponse)
async def update_customer(customer_id: int, customer: schemas.CustomerUpdate, db: AsyncSession = Depends(get_db)):
    return await service.update_customer(db, customer_id, customer)

@router.delete("/api/customers/{customer_id}")
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Soft delete a customer"""
    success = await service.soft_delete_customer(db, customer_id)
    return {"success": success}

# --- Customer Orders & Stats ---
@router.get("/api/customers/{customer_id}/orders")
async def get_customer_orders(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Get all orders for a customer"""
    orders = await service.get_customer_orders(db, customer_id)
    # Convert to dict for JSON serialization
    return [
        {
            "id": order.id,
            "status": order.status,
            "total_amount": order.total_amount,
            "created_at": order.created_at.isoformat()
        }
        for order in orders
    ]

@router.get("/api/customers/{customer_id}/stats")
async def get_customer_stats(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Get customer statistics"""
    return await service.get_customer_stats(db, customer_id)

# --- Export/Import ---
@router.get("/api/customers/export")
async def export_customers(db: AsyncSession = Depends(get_db)):
    """Export all customers to CSV"""
    csv_content = await service.export_customers_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers.csv"}
    )

@router.post("/api/customers/import")
async def import_customers(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Import customers from CSV"""
    content = await file.read()
    file_content = content.decode('utf-8')
    result = await service.import_customers_csv(db, file_content)
    return result

# --- Groups Routes ---
@router.get("/customers/groups/list", response_class=HTMLResponse)
async def customer_groups_list_page(request: Request, db: AsyncSession = Depends(get_db)):
    groups = await service.get_customer_groups(db)
    return templates.TemplateResponse("customers/groups/list.html", {"request": request, "groups": groups})

@router.get("/customers/groups/create", response_class=HTMLResponse)
async def customer_group_create_page(request: Request):
    return templates.TemplateResponse("customers/groups/create.html", {"request": request})

@router.post("/api/customers/groups", response_model=schemas.CustomerGroupResponse)
async def create_customer_group(group: schemas.CustomerGroupCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_customer_group(db, group)

@router.delete("/api/customers/groups/{group_id}")
async def delete_customer_group(group_id: int, db: AsyncSession = Depends(get_db)):
    success = await service.delete_customer_group(db, group_id)
    return {"success": success}

@router.get("/api/customers/groups", response_model=List[schemas.CustomerGroupResponse])
async def list_customer_groups_api(db: AsyncSession = Depends(get_db)):
    """API endpoint to get all customer groups"""
    return await service.get_customer_groups(db)



