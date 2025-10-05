"""
Error handling middleware for the bot.

This middleware catches all exceptions that occur during update processing
and provides user-friendly error messages while logging detailed error information.
"""

import structlog
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from anthropic import (
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

logger = structlog.get_logger(__name__)


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
                "claude_api_connection_error",
                error=str(e),
                error_type="api_connection",
                exc_info=True
            )
            await self._send_error_message(
                event,
                "⚠️ Проблема с подключением к AI сервису. Попробуй через минуту."
            )

        except RateLimitError as e:
            # Claude API rate limit
            logger.warning(
                "claude_api_rate_limit",
                error=str(e),
                error_type="rate_limit"
            )
            await self._send_error_message(
                event,
                "⏱ Слишком много запросов. Подожди немного и попробуй снова."
            )

        except APIStatusError as e:
            # Other Claude API errors
            logger.error(
                "claude_api_status_error",
                error=str(e),
                error_type="api_status",
                status_code=e.status_code,
                exc_info=True
            )
            await self._send_error_message(
                event,
                "❌ Ошибка AI сервиса. Мы уже работаем над решением."
            )

        except TelegramBadRequest as e:
            # Telegram API errors (invalid markdown, etc.)
            error_msg = str(e)
            if "can't parse entities" in error_msg.lower() or "can't find end" in error_msg.lower():
                logger.error(
                    "telegram_parse_error",
                    error=error_msg,
                    error_type="telegram_parse",
                    exc_info=True
                )
                await self._send_error_message(
                    event,
                    "⚠️ Ошибка форматирования текста. Попробуй ещё раз или обратись в поддержку."
                )
            else:
                logger.error(
                    "telegram_bad_request",
                    error=error_msg,
                    error_type="telegram_bad_request",
                    exc_info=True
                )
                await self._send_error_message(
                    event,
                    "❌ Ошибка при отправке сообщения. Попробуй позже."
                )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(
                "unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
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
                "failed_to_send_error_message",
                error=str(e),
                exc_info=True
            )
