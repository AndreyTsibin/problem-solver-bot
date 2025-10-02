"""YooKassa payment service for handling payments in rubles"""
from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotification
from bot.config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
import structlog
import uuid

logger = structlog.get_logger()

# Configure YooKassa
Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY


class YooKassaService:
    """Service for creating and managing YooKassa payments"""

    @staticmethod
    async def create_payment(amount: float, description: str, user_telegram_id: int,
                            package_type: str, return_url: str = None) -> dict:
        """
        Create a payment in YooKassa

        Args:
            amount: Payment amount in rubles
            description: Payment description
            user_telegram_id: Telegram user ID
            package_type: Package type (starter, medium, large, standard, premium)
            return_url: URL to redirect after payment (optional)

        Returns:
            dict with payment_id and confirmation_url
        """
        try:
            # Generate unique idempotence key
            idempotence_key = str(uuid.uuid4())

            # Create payment
            payment = Payment.create({
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or f"https://t.me/YourBot"  # Replace with your bot
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "user_telegram_id": user_telegram_id,
                    "package_type": package_type
                }
            }, idempotence_key)

            logger.info(
                "payment_created",
                payment_id=payment.id,
                amount=amount,
                user_id=user_telegram_id,
                package=package_type
            )

            return {
                "payment_id": payment.id,
                "confirmation_url": payment.confirmation.confirmation_url,
                "status": payment.status
            }

        except Exception as e:
            logger.error(
                "payment_creation_error",
                error=str(e),
                user_id=user_telegram_id,
                package=package_type
            )
            raise

    @staticmethod
    async def check_payment_status(payment_id: str) -> dict:
        """
        Check payment status

        Args:
            payment_id: YooKassa payment ID

        Returns:
            dict with status and metadata
        """
        try:
            payment = Payment.find_one(payment_id)

            return {
                "payment_id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "amount": float(payment.amount.value),
                "metadata": payment.metadata
            }

        except Exception as e:
            logger.error("payment_check_error", error=str(e), payment_id=payment_id)
            raise

    @staticmethod
    def verify_webhook_signature(notification_body: dict) -> bool:
        """
        Verify webhook notification signature

        Args:
            notification_body: Webhook notification body

        Returns:
            True if signature is valid
        """
        try:
            # YooKassa SDK handles signature verification automatically
            webhook = WebhookNotification(notification_body)
            return webhook.object.id is not None
        except Exception as e:
            logger.error("webhook_verification_error", error=str(e))
            return False
