import anthropic
from typing import Dict, List
import time
import structlog
from bot.config import CLAUDE_API_KEY
from bot.services.prompt_builder import PromptBuilder

logger = structlog.get_logger(__name__)


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
        user_context: Dict = None
    ) -> str:
        """Generate next question with prompt caching and user context"""
        # Extract user context
        gender = user_context.get('gender') if user_context else None
        age = user_context.get('age') if user_context else None
        occupation = user_context.get('occupation') if user_context else None
        work_format = user_context.get('work_format') if user_context else None

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
                        "text": self.prompt_builder.build_system_prompt(
                            gender=gender,
                            age=age,
                            occupation=occupation,
                            work_format=work_format
                        ),
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{"role": "user", "content": context}]
            )

            # Log token usage
            logger.info(
                "question_generated",
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                cache_creation_input_tokens=getattr(message.usage, 'cache_creation_input_tokens', 0),
                cache_read_input_tokens=getattr(message.usage, 'cache_read_input_tokens', 0)
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
        user_context: Dict = None
    ) -> str:
        """Generate final solution with prompt caching and user context"""
        # Extract user context
        gender = user_context.get('gender') if user_context else None
        age = user_context.get('age') if user_context else None
        occupation = user_context.get('occupation') if user_context else None
        work_format = user_context.get('work_format') if user_context else None

        context = self.prompt_builder.build_solution_context(
            problem_description=problem_description,
            conversation_history=conversation_history
        )

        # Build and log system prompt
        system_prompt = self.prompt_builder.build_system_prompt(
            gender=gender,
            age=age,
            occupation=occupation,
            work_format=work_format
        )

        # Log solution generation with structured context
        logger.info(
            "generating_solution",
            user_gender=gender,
            user_age=age,
            user_occupation=occupation,
            user_work_format=work_format
        )

        for attempt in range(self.max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=2500,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"}
                        }
                    ],
                    messages=[{"role": "user", "content": context}]
                )

                # Log token usage
                logger.info(
                    "solution_generated",
                    input_tokens=message.usage.input_tokens,
                    output_tokens=message.usage.output_tokens,
                    cache_creation_input_tokens=getattr(message.usage, 'cache_creation_input_tokens', 0),
                    cache_read_input_tokens=getattr(message.usage, 'cache_read_input_tokens', 0)
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

    async def generate_discussion_answer(
        self,
        problem_description: str,
        conversation_history: List[Dict],
        user_question: str,
        user_context: Dict = None
    ) -> str:
        """Generate answer for discussion mode with FULL context"""
        # Extract user context
        gender = user_context.get('gender') if user_context else None
        age = user_context.get('age') if user_context else None
        occupation = user_context.get('occupation') if user_context else None
        work_format = user_context.get('work_format') if user_context else None

        context = self.prompt_builder.build_discussion_context(
            problem_description=problem_description,
            conversation_history=conversation_history,
            user_question=user_question
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,  # Discussion answers are shorter
                system=[
                    {
                        "type": "text",
                        "text": self.prompt_builder.build_system_prompt(
                            gender=gender,
                            age=age,
                            occupation=occupation,
                            work_format=work_format
                        ),
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{"role": "user", "content": context}]
            )

            # Log token usage
            logger.info(
                "discussion_answer_generated",
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                cache_creation_input_tokens=getattr(message.usage, 'cache_creation_input_tokens', 0),
                cache_read_input_tokens=getattr(message.usage, 'cache_read_input_tokens', 0)
            )

            answer = message.content[0].text.strip()
            return answer

        except Exception as e:
            print(f"❌ Error generating discussion answer: {e}")
            return "Извини, возникла техническая ошибка. Попробуй переформулировать вопрос."
