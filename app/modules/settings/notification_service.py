
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.settings.models import NotificationTemplate, NotificationChannel, NotificationEventType
from app.modules.sales.models import Order
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def render_message(template: str, order: Order, store_name: str = "My Store") -> str:
        """
        Replaces placeholders in the template with actual order data.
        """
        if not template:
            return ""
            
        # Basic variables
        customer_name = order.customer.name if order.customer else "Customer"
        order_id = str(order.id)
        order_status = order.status.value
        # For simplicity, we assume a standard URL structure. In a real app, use a proper URL generator.
        order_url = f"https://mystore.com/orders/{order.id}" 
        
        message = template.replace("{customer_name}", customer_name)
        message = message.replace("{order_id}", order_id)
        message = message.replace("{order_status}", order_status)
        message = message.replace("{order_url}", order_url)
        message = message.replace("{store_name}", store_name)
        
        return message

    @staticmethod
    async def send_notification(
        db: AsyncSession, 
        order: Order, 
        event_type: NotificationEventType, 
        store_name: str = "Zid Store"
    ):
        """
        Checks for enabled templates for the given event type and sends notifications via configured channels.
        """
        logger.info(f"Checking notifications for Order #{order.id}, Event: {event_type}")
        
        # Fetch enabled templates for this event type
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.event_type == event_type,
            NotificationTemplate.is_enabled == True
        )
        result = await db.execute(stmt)
        templates = result.scalars().all()
        
        if not templates:
            logger.info("No enabled templates found for this event.")
            return

        for template in templates:
            # Determine language based on something? 
            # For now, let's assume we send the Arabic message if available, else English.
            # Or send both? Usually depends on customer preference. 
            # Let's default to sending Arabic content for now as it's a Saudi platform context.
            
            message_text = ""
            if template.message_template_ar:
                message_text = NotificationService.render_message(template.message_template_ar, order, store_name)
            elif template.message_template_en:
                 message_text = NotificationService.render_message(template.message_template_en, order, store_name)
            
            if not message_text:
                continue
                
            # Simulate Sending
            channel = template.channel
            await NotificationService._dispatch(channel, order.customer.phone if order.customer else "", message_text)

    @staticmethod
    async def _dispatch(channel: NotificationChannel, recipient: str, message: str):
        """
        Simulates the actual sending process.
        """
        if channel == NotificationChannel.SMS:
            # Call SMS Gateway API here
            logger.info(f"([SIMULATED] SMS SENT TO {recipient}: {message}")
            print(f" >>> [SMS] To {recipient}: {message}")
            
        elif channel == NotificationChannel.WHATSAPP:
            # Call WhatsApp API here
            logger.info(f"[SIMULATED] WHATSAPP SENT TO {recipient}: {message}")
            print(f" >>> [WHATSAPP] To {recipient}: {message}")
        
        elif channel == NotificationChannel.EMAIL:
            # Call Email API here
            logger.info(f"[SIMULATED] EMAIL SENT TO {recipient}: {message}")
            print(f" >>> [EMAIL] To {recipient}: {message}")
    
    @staticmethod
    async def send_staff_notification(db: AsyncSession, order: Order, status_key: str, store_settings):
        """
        Sends notifications to staff members based on store settings
        """
        try:
            if not store_settings.staff_emails:
                logger.info("No staff emails configured")
                return
            
            staff_emails = store_settings.staff_emails if isinstance(store_settings.staff_emails, list) else []
            
            message = f"تنبيه: تحديث حالة الطلب #{order.id} إلى {status_key}"
            
            for email in staff_emails:
                await NotificationService._dispatch(
                    channel=NotificationChannel.EMAIL,
                    recipient=email,
                    message=message
                )
            
            logger.info(f"Staff notifications sent for order #{order.id}, status: {status_key}")
            
        except Exception as e:
            logger.error(f"Error sending staff notification: {e}")
