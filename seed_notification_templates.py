"""
Script to seed default notification templates
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.core.database import AsyncSessionLocal
from app.modules.settings.models import NotificationTemplate, NotificationEventType, NotificationChannel


async def seed_templates():
    async with AsyncSessionLocal() as db:

        # Define default templates
        templates = [
            # SMS Templates
            {
                "event_type": NotificationEventType.ORDER_CREATED,
                "channel": NotificationChannel.SMS,
                "message_template_ar": "مرحباً {customer_name}، تم استلام طلبك #{order_id} بنجاح. شكراً لثقتك بنا!",
                "message_template_en": "Hello {customer_name}, your order #{order_id} has been received successfully. Thank you!"
            },
            {
                "event_type": NotificationEventType.ORDER_PROCESSING,
                "channel": NotificationChannel.SMS,
                "message_template_ar": "طلبك #{order_id} قيد التجهيز الآن. سنقوم بإشعارك عند شحنه.",
                "message_template_en": "Your order #{order_id} is now being processed. We'll notify you when it ships."
            },
            {
                "event_type": NotificationEventType.ORDER_READY,
                "channel": NotificationChannel.SMS,
                "message_template_ar": "طلبك #{order_id} جاهز للشحن!",
                "message_template_en": "Your order #{order_id} is ready for shipping!"
            },
            {
                "event_type": NotificationEventType.ORDER_SHIPPED,
                "channel": NotificationChannel.SMS,
                "message_template_ar": "تم شحن طلبك #{order_id}. سيصلك قريباً!",
                "message_template_en": "Your order #{order_id} has been shipped. It will arrive soon!"
            },
            {
                "event_type": NotificationEventType.ORDER_COMPLETED,
                "channel": NotificationChannel.SMS,
                "message_template_ar": "تم تسليم طلبك #{order_id} بنجاح. نتمنى أن تكون راضياً عن تجربتك!",
                "message_template_en": "Your order #{order_id} has been delivered successfully. We hope you enjoyed your experience!"
            },
            {
                "event_type": NotificationEventType.ORDER_CANCELLED,
                "channel": NotificationChannel.SMS,
                "message_template_ar": "تم إلغاء طلبك #{order_id}. إذا كان لديك أي استفسار، يرجى التواصل معنا.",
                "message_template_en": "Your order #{order_id} has been cancelled. If you have any questions, please contact us."
            },
            
            # WhatsApp Templates
            {
                "event_type": NotificationEventType.ORDER_CREATED,
                "channel": NotificationChannel.WHATSAPP,
                "message_template_ar": "🎉 مرحباً {customer_name}!\n\nتم استلام طلبك #{order_id} بنجاح.\nسنقوم بمعالجته في أقرب وقت.\n\nشكراً لاختيارك {store_name}",
                "message_template_en": "🎉 Hello {customer_name}!\n\nYour order #{order_id} has been received.\nWe'll process it shortly.\n\nThank you for choosing {store_name}"
            },
            {
                "event_type": NotificationEventType.ORDER_PROCESSING,
                "channel": NotificationChannel.WHATSAPP,
                "message_template_ar": "⏳ طلبك #{order_id} قيد التجهيز\n\nنحن نعمل على تجهيز طلبك الآن.\nسنشعرك عندما يكون جاهزاً للشحن!",
                "message_template_en": "⏳ Your order #{order_id} is being processed\n\nWe're working on preparing your order.\nWe'll notify you when it's ready to ship!"
            },
            {
                "event_type": NotificationEventType.ORDER_READY,
                "channel": NotificationChannel.WHATSAPP,
                "message_template_ar": "✅ طلبك #{order_id} جاهز!\n\nطلبك جاهز الآن للشحن.\nسيتم إرساله قريباً.",
                "message_template_en": "✅ Your order #{order_id} is ready!\n\nYour order is now ready for shipping.\nIt will be sent soon."
            },
            {
                "event_type": NotificationEventType.ORDER_SHIPPED,
                "channel": NotificationChannel.WHATSAPP,
                "message_template_ar": "🚚 تم شحن طلبك #{order_id}!\n\nطلبك في الطريق إليك.\nسيصلك خلال الأيام القادمة.",
                "message_template_en": "🚚 Your order #{order_id} has shipped!\n\nYour order is on its way.\nIt will arrive in the coming days."
            },
            {
                "event_type": NotificationEventType.ORDER_COMPLETED,
                "channel": NotificationChannel.WHATSAPP,
                "message_template_ar": "🎁 تم تسليم طلبك #{order_id}\n\nنأمل أن تكون راضياً عن طلبك!\nشكراً لثقتك بنا.",
                "message_template_en": "🎁 Your order #{order_id} delivered\n\nWe hope you're satisfied with your order!\nThank you for trusting us."
            },
            {
                "event_type": NotificationEventType.ORDER_CANCELLED,
                "channel": NotificationChannel.WHATSAPP,
                "message_template_ar": "❌ تم إلغاء طلبك #{order_id}\n\nإذا كان لديك أي استفسار، لا تتردد في التواصل معنا.",
                "message_template_en": "❌ Your order #{order_id} cancelled\n\nIf you have any questions, don't hesitate to contact us."
            },
            
            # Email Templates (disabled by default)
            {
                "event_type": NotificationEventType.ORDER_CREATED,
                "channel": NotificationChannel.EMAIL,
                "is_enabled": False,
                "message_template_ar": "مرحباً {customer_name}، تم استلام طلبك #{order_id}",
                "message_template_en": "Hello {customer_name}, your order #{order_id} received"
            },
            {
                "event_type": NotificationEventType.ORDER_PROCESSING,
                "channel": NotificationChannel.EMAIL,
                "is_enabled": False,
                "message_template_ar": "طلبك #{order_id} قيد التجهيز",
                "message_template_en": "Your order #{order_id} is processing"
            },
            {
                "event_type": NotificationEventType.ORDER_SHIPPED,
                "channel": NotificationChannel.EMAIL,
                "is_enabled": False,
                "message_template_ar": "تم شحن طلبك #{order_id}",
                "message_template_en": "Your order #{order_id} shipped"
            },
            {
                "event_type": NotificationEventType.ORDER_COMPLETED,
                "channel": NotificationChannel.EMAIL,
                "is_enabled": False,
                "message_template_ar": "تم تسليم طلبك #{order_id}",
                "message_template_en": "Your order #{order_id} delivered"
            },
            {
                "event_type": NotificationEventType.ORDER_CANCELLED,
                "channel": NotificationChannel.EMAIL,
                "is_enabled": False,
                "message_template_ar": "تم إلغاء طلبك #{order_id}",
                "message_template_en": "Your order #{order_id} cancelled"
            },
        ]
        
        # Create templates
        for template_data in templates:
            template = NotificationTemplate(**template_data)
            db.add(template)
        
        await db.commit()
        print(f"✅ تم إنشاء {len(templates)} قالب إشعار بنجاح!")


if __name__ == "__main__":
    print("جاري إنشاء قوالب الإشعارات الافتراضية...")
    asyncio.run(seed_templates())
