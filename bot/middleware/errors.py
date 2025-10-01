"""
Error handling middleware for the bot.

This middleware catches all exceptions that occur during update processing
and provides user-friendly error messages while logging detailed error information.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from anthropic import (
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Middleware for handling errors in bot operations.

    Catches exceptions during update processing and:
    - Logs detailed error information
    - Sends user-friendly error messages
    - Handles specific error types (API errors, rate limits, etc.)
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Process the event through error handling.

        Args:
            handler: The next handler in the chain
            event: The Telegram event (Update, Message, etc.)
            data: Additional data passed through middleware chain

        Returns:
            Result from handler or None if error occurred
        """
        try:
            # Call the next handler
            return await handler(event, data)

        except APIConnectionError as e:
            # Claude API connection error
            logger.error(
                "Claude API connection error: %s",
                str(e),
                exc_info=True,
                extra={"error_type": "api_connection"}
            )
            await self._send_error_message(
                event,
                "⚠️ Проблема с подключением к AI сервису. Попробуй через минуту."
            )

        except RateLimitError as e:
            # Claude API rate limit
            logger.warning(
                "Claude API rate limit exceeded: %s",
                str(e),
                extra={"error_type": "rate_limit"}
            )
            await self._send_error_message(
                event,
                "⏱ Слишком много запросов. Подожди немного и попробуй снова."
            )

        except APIStatusError as e:
            # Other Claude API errors
            logger.error(
                "Claude API error (status %s): %s",
                e.status_code,
                str(e),
                exc_info=True,
                extra={"error_type": "api_status", "status_code": e.status_code}
            )
            await self._send_error_message(
                event,
                "❌ Ошибка AI сервиса. Мы уже работаем над решением."
            )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(
                "Unexpected error handling update: %s - %s",
                type(e).__name__,
                str(e),
                exc_info=True,
                extra={"error_type": "unexpected"}
            )
            await self._send_error_message(
                event,
                "❌ Что-то пошло не так. Попробуй /start или напиши нам."
            )

        return None

    async def _send_error_message(self, event: TelegramObject, message: str) -> None:
        """
        Send error message to user.

        Args:
            event: The Telegram event
            message: Error message text
        """
        try:
            # Extract message or callback query from event
            if isinstance(event, Update):
                if event.message:
                    await event.message.answer(message)
                elif event.callback_query:
                    await event.callback_query.message.answer(message)
                    await event.callback_query.answer("Ошибка")
            elif isinstance(event, Message):
                await event.answer(message)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(message)
                await event.answer("Ошибка")
        except Exception as e:
            # If we can't send error message, just log it
            logger.error(
                "Failed to send error message to user: %s",
                str(e),
                exc_info=True
            )
