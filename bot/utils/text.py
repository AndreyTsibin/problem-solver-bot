"""Text utilities for safe message formatting"""
import re
from typing import Optional


def strip_markdown(text: str) -> str:
    """
    Remove all markdown formatting from text to prevent Telegram parse errors.

    Args:
        text: Text with markdown formatting

    Returns:
        Clean text without markdown symbols
    """
    if not text:
        return ""

    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Remove italic (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remove strikethrough (~~text~~)
    text = re.sub(r'~~(.+?)~~', r'\1', text)

    # Remove code (`text` or ```text```)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'```(.+?)```', r'\1', text, flags=re.DOTALL)

    # Remove links [text](url)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

    return text


def truncate_at_sentence(text: str, max_length: int = 300, min_length: int = 100) -> str:
    """
    Truncate text at sentence boundary for clean cutoff.

    Args:
        text: Text to truncate
        max_length: Maximum length
        min_length: Minimum length (don't cut if sentence end is before this)

    Returns:
        Truncated text with "..." if needed
    """
    if not text or len(text) <= max_length:
        return text

    # Try to find last sentence end before max_length
    cutoff_text = text[:max_length]

    # Look for sentence endings (., !, ?)
    last_period = max(
        cutoff_text.rfind('.'),
        cutoff_text.rfind('!'),
        cutoff_text.rfind('?')
    )

    # If found good cutoff point, use it
    if last_period > min_length:
        return text[:last_period + 1] + "..."

    # Otherwise just cut at max_length
    return cutoff_text + "..."


def safe_format_text(text: str, parse_mode: Optional[str] = None) -> str:
    """
    Format text safely for Telegram, removing markdown if needed.

    Args:
        text: Input text
        parse_mode: If None, strips markdown. If "HTML" or "Markdown", keeps it.

    Returns:
        Safe text for Telegram
    """
    if not text:
        return ""

    # If no parse_mode specified, strip all markdown
    if parse_mode is None:
        text = strip_markdown(text)

    # Always escape special characters that could break parsing
    # But only if we're not using parse_mode
    if parse_mode is None:
        # Escape HTML-like tags
        text = text.replace('<', '&lt;').replace('>', '&gt;')

    return text


def prepare_problem_text(
    title: str,
    root_cause: Optional[str] = None,
    action_plan: Optional[str] = None,
    max_plan_length: int = 300
) -> str:
    """
    Prepare problem text for display in history, safely handling markdown.

    Args:
        title: Problem title
        root_cause: Root cause analysis
        action_plan: Action plan (may contain markdown)
        max_plan_length: Maximum length for action plan

    Returns:
        Formatted text without problematic markdown
    """
    text = f"📝 Проблема:\n{strip_markdown(title)}\n\n"

    if root_cause:
        # Strip markdown and truncate root_cause too (can be long)
        clean_cause = strip_markdown(root_cause)
        truncated_cause = truncate_at_sentence(clean_cause, 200, 50)
        text += f"🎯 Причина:\n{truncated_cause}\n\n"

    if action_plan:
        # Strip markdown and truncate safely
        clean_plan = strip_markdown(action_plan)
        truncated_plan = truncate_at_sentence(clean_plan, max_plan_length)
        text += f"💡 Решение:\n{truncated_plan}"

    return text
