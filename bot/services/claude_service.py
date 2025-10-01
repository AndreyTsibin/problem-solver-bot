import anthropic
from typing import Dict, List, Optional
import json
import time
from bot.config import CLAUDE_API_KEY


class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        self.model = "claude-sonnet-4-20250514"
        self.max_retries = 3

    async def analyze_problem_type(self, problem_description: str) -> Dict[str, str]:
        """
        Analyze problem and determine its type and methodology

        Returns:
            {
                "type": "linear|multifactor|systemic",
                "methodology": "5_whys|fishbone|first_principles",
                "reasoning": "explanation why this methodology"
            }
        """
        prompt = f"""Analyze this problem and determine its type:

Problem: {problem_description}

Classify it as one of:
1. **linear** - direct cause-effect relationship → use "5_whys" methodology
2. **multifactor** - multiple causes → use "fishbone" methodology
3. **systemic** - complex interconnections → use "first_principles" methodology

Respond ONLY with valid JSON in this exact format:
{{
    "type": "linear",
    "methodology": "5_whys",
    "reasoning": "This is a linear problem because..."
}}

DO NOT include any text outside the JSON. DO NOT use markdown code blocks.
"""

        for attempt in range(self.max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Extract response text
                response_text = message.content[0].text.strip()

                # Parse JSON (Claude might wrap in ```json sometimes)
                if response_text.startswith("```"):
                    # Remove markdown code blocks
                    response_text = response_text.replace("```json", "").replace("```", "").strip()

                result = json.loads(response_text)

                # Validate response structure
                required_keys = ["type", "methodology", "reasoning"]
                if all(key in result for key in required_keys):
                    return result
                else:
                    raise ValueError(f"Invalid response structure: {result}")

            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error (attempt {attempt+1}/{self.max_retries}): {e}")
                print(f"Response was: {response_text}")
                if attempt == self.max_retries - 1:
                    # Fallback to default
                    return {
                        "type": "linear",
                        "methodology": "5_whys",
                        "reasoning": "Default methodology due to parsing error"
                    }
                time.sleep(1)  # Wait before retry

            except Exception as e:
                print(f"❌ API error (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    async def generate_question(
        self,
        methodology: str,
        problem_description: str,
        conversation_history: List[Dict],
        step: int
    ) -> str:
        """
        Generate next question based on methodology and conversation history

        Args:
            methodology: "5_whys", "fishbone", or "first_principles"
            problem_description: Original problem statement
            conversation_history: List of {"role": "user|assistant", "content": "..."}
            step: Current question number (1-5)

        Returns:
            Next question to ask user
        """

        # Build context from conversation
        history_text = "\n".join([
            f"{'Q' if msg['role'] == 'assistant' else 'A'}: {msg['content']}"
            for msg in conversation_history
        ])

        prompt = f"""You are a problem-solving coach using the {methodology} methodology.

Original problem: {problem_description}

Conversation so far:
{history_text if history_text else "(no questions asked yet)"}

Current step: {step}/5

Generate the next clarifying question to dig deeper into the problem.
- Ask ONE specific question
- Focus on uncovering root causes
- Be empathetic but direct
- Keep it under 100 words

Respond with ONLY the question text, nothing else.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            question = message.content[0].text.strip()
            return question

        except Exception as e:
            print(f"❌ Error generating question: {e}")
            # Fallback generic question
            return f"Расскажи подробнее о проблеме (шаг {step}/5)"

    async def generate_solution(
        self,
        problem_description: str,
        methodology: str,
        conversation_history: List[Dict]
    ) -> Dict[str, any]:
        """
        Generate final solution with action plan

        Returns:
            {
                "root_cause": "One sentence core issue",
                "analysis": {
                    "methodology": "...",
                    "key_factors": ["factor1", "factor2"],
                    "leverage_points": ["point1", "point2"]
                },
                "action_plan": {
                    "immediate": ["action1", "action2"],
                    "this_week": ["step1", "step2"],
                    "long_term": ["strategic_change"]
                },
                "metrics": [
                    {"what": "...", "target": "..."},
                    {"what": "...", "target": "..."}
                ]
            }
        """

        # Build full conversation
        history_text = "\n".join([
            f"{'Question' if msg['role'] == 'assistant' else 'Answer'}: {msg['content']}"
            for msg in conversation_history
        ])

        prompt = f"""Based on this conversation, generate a complete solution:

Original problem: {problem_description}
Methodology used: {methodology}

Full conversation:
{history_text}

Create a comprehensive solution in JSON format:

{{
    "root_cause": "One clear sentence describing the core issue",
    "analysis": {{
        "methodology": "{methodology}",
        "key_factors": ["factor 1", "factor 2", "factor 3"],
        "leverage_points": ["where you can influence 1", "where you can influence 2"]
    }},
    "action_plan": {{
        "immediate": ["specific action 1 (24h)", "specific action 2 (24h)"],
        "this_week": ["step 1 with deadline", "step 2 with deadline"],
        "long_term": ["strategic change for lasting impact"]
    }},
    "metrics": [
        {{"what": "metric to measure", "target": "target value"}},
        {{"what": "what to track", "target": "success criteria"}}
    ]
}}

RESPOND ONLY WITH VALID JSON. NO MARKDOWN. NO EXTRA TEXT.
"""

        for attempt in range(self.max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )

                response_text = message.content[0].text.strip()

                # Remove markdown if present
                if response_text.startswith("```"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()

                solution = json.loads(response_text)
                return solution

            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error in solution: {e}")
                if attempt == self.max_retries - 1:
                    # Return fallback structure
                    return {
                        "root_cause": "Не удалось определить корневую причину",
                        "analysis": {
                            "methodology": methodology,
                            "key_factors": ["Требуется дополнительный анализ"],
                            "leverage_points": []
                        },
                        "action_plan": {
                            "immediate": ["Переформулировать проблему"],
                            "this_week": ["Собрать больше информации"],
                            "long_term": []
                        },
                        "metrics": []
                    }
                time.sleep(1)

            except Exception as e:
                print(f"❌ Error generating solution: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
