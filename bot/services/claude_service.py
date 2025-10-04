import anthropic
from typing import Dict, List
import time
from bot.config import CLAUDE_API_KEY
from bot.services.prompt_builder import PromptBuilder


class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"  # Updated to latest model
        self.max_retries = 3
        self.prompt_builder = PromptBuilder()

    async def generate_question(
        self,
        problem_description: str,
        conversation_history: List[Dict],
        step: int,
        gender: str = None
    ) -> str:
        """Generate next question with prompt caching and gender awareness"""
        context = self.prompt_builder.build_questioning_context(
            problem_description=problem_description,
            conversation_history=conversation_history,
            current_step=step
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                system=[
                    {
                        "type": "text",
                        "text": self.prompt_builder.build_system_prompt(gender=gender),
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{"role": "user", "content": context}]
            )

            question = message.content[0].text.strip()
            return question

        except Exception as e:
            print(f"❌ Error generating question: {e}")
            return f"Расскажи подробнее о ситуации (вопрос {step}/5)"

    async def generate_solution(
        self,
        problem_description: str,
        conversation_history: List[Dict],
        gender: str = None
    ) -> str:
        """Generate final solution with prompt caching and gender awareness"""
        context = self.prompt_builder.build_solution_context(
            problem_description=problem_description,
            conversation_history=conversation_history
        )

        for attempt in range(self.max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=2500,
                    system=[
                        {
                            "type": "text",
                            "text": self.prompt_builder.build_system_prompt(gender=gender),
                            "cache_control": {"type": "ephemeral"}
                        }
                    ],
                    messages=[{"role": "user", "content": context}]
                )

                solution = message.content[0].text.strip()
                return solution

            except Exception as e:
                print(f"❌ Error generating solution (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return """🎯 В ЧЁМ СУТЬ
Не удалось сгенерировать решение из-за технической ошибки.

💡 ПОЧЕМУ ТАК ПРОИСХОДИТ
Возможно временные проблемы с API. Попробуй через несколько минут.

📋 ЧТО ДЕЛАТЬ ПРЯМО СЕЙЧАС
□ Нажми "🚀 Решить проблему" и попробуй снова

💬 P.S.
Извини за неудобства!"""
                time.sleep(2 ** attempt)
