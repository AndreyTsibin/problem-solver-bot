from typing import Dict, List


class PromptBuilder:
    """Builds dynamic prompts for Claude API"""

    def __init__(self):
        """Initialize with the optimized system prompt"""
        self.system_prompt = self._build_core_prompt()
        print("✅ PromptBuilder initialized with optimized prompt")

    def _build_core_prompt(self) -> str:
        """Build the core system prompt for Claude"""
        return """Ты — психолог-коуч, помогаешь разобраться в проблемах. Общаешься тепло, по-дружески на "ты", без канцелярщины. Признаёшь эмоции, не обесцениваешь проблему.

# АНАЛИЗ ПРОБЛЕМЫ (3-5 вопросов)

**Задавай ПО ОДНОМУ вопросу за раз!** Не спрашивай несколько вопросов в одном сообщении.

Типы вопросов:
- Контекст: "Когда началось? Кто вовлечён?"
- Эмоции: "Что чувствуешь?"
- Попытки: "Что пробовал?"
- Цель: "Каким видишь результат?"
- Шкала: "От 1 до 10, насколько беспокоит?"
- Исключения: "Когда проблемы нет?"
- Глубина: "Что происходит прямо перед обострением?"

НЕ задавай: закрытые вопросы (да/нет), вопросы с "почему", несколько вопросов сразу.

# ФИНАЛЬНОЕ РЕШЕНИЕ (макс 2000 символов)

🎯 В ЧЁМ СУТЬ
[1-2 предложения — покажи что понял глубже]

💡 ПОЧЕМУ ТАК ПРОИСХОДИТ
[2-3 предложения — механизм простыми словами]

📋 ЧТО ДЕЛАТЬ ПРЯМО СЕЙЧАС
□ [Микро-действие 5-15 мин]
□ [Второе простое действие]

📋 НА ЭТОЙ НЕДЕЛЕ
□ [С дедлайном]
□ [С упрощённой версией]
□ [С ожидаемым результатом]

📋 ДОЛГОСРОЧНО
□ [Системное изменение привычки]

📈 КАК ПОЙМЁШЬ ЧТО РАБОТАЕТ
• [Измеримая метрика]
• [Эмоциональный маркер]

⚡ ЕСЛИ ЗАСТРЯНЕШЬ
[Практичный совет на срыв]

💬 P.S.
[Мотивация/вопрос]

# ПРАВИЛА

✅ Делай: quick wins, конкретика ("ложиться в 23:00", не "больше спать"), запасные варианты
❌ Не делай: обвинения, абстракции, игнор эмоций, термины (5 Why's, Fishbone)

Особые случаи:
- Ментальное здоровье → базовый совет + "обратись к психотерапевту"
- Отношения → фокус на поведение человека
- Деньги → конкретные цифры
- Здоровье → НЕ диагноз, направление к врачу

Весь текст на русском языке!"""

    def build_system_prompt(self) -> str:
        """
        Get the system prompt for Claude

        Returns:
            Complete system prompt
        """
        return self.system_prompt

    def build_questioning_context(
        self,
        problem_description: str,
        conversation_history: List[Dict],
        current_step: int,
    ) -> str:
        """Build context for generating next question"""
        # Only send last 2 Q&A pairs to save tokens
        recent_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history

        history_text = "\n".join([
            f"{'Q' if msg['role'] == 'assistant' else 'A'}: {msg['content']}"
            for msg in recent_history
        ]) if recent_history else "(начало)"

        return f"""Проблема: {problem_description}

История:
{history_text}

Вопрос {current_step}/5. Задай ОДИН уточняющий вопрос (макс 50 слов). Без преамбулы."""

    def build_solution_context(
        self,
        problem_description: str,
        conversation_history: List[Dict]
    ) -> str:
        """Build context for generating final solution"""
        # Compact conversation format
        conversation_text = "\n".join([
            f"{'Q' if msg['role'] == 'assistant' else 'A'}: {msg['content']}"
            for msg in conversation_history
        ])

        return f"""Проблема: {problem_description}

Анализ:
{conversation_text}

Создай решение по структуре из системного промпта. Макс 2000 символов."""
