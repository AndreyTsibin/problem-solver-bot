import os
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache


class PromptBuilder:
    """Builds dynamic prompts for Claude API with methodology files"""

    def __init__(self):
        self.methodologies_dir = Path("methodologies")

        # Verify directory exists
        if not self.methodologies_dir.exists():
            raise FileNotFoundError(
                f"Methodologies directory not found: {self.methodologies_dir}"
            )

        # Load all methodology files
        self.main_prompt = self._load_file("main-problem-solver-prompt.md")
        self.methodologies = {
            "5_whys": self._load_file("5-whys-method.md"),
            "fishbone": self._load_file("fishbone-method.md"),
            "first_principles": self._load_file("first-principles-method.md"),
            "pdca": self._load_file("pdca_solution.md"),
            "psychological": self._load_file("psychological_techniques.md")
        }

        print(f"✅ Loaded {len(self.methodologies)} methodology files")

    @lru_cache(maxsize=10)
    def _load_file(self, filename: str) -> str:
        """Load and cache methodology file content"""
        filepath = self.methodologies_dir / filename

        if not filepath.exists():
            print(f"⚠️  Warning: {filename} not found, using empty content")
            return ""

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"📄 Loaded: {filename} ({len(content)} chars)")
            return content
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
            return ""

    def build_system_prompt(self, methodology: Optional[str] = None) -> str:
        """
        Build system prompt with optional methodology context

        Args:
            methodology: "5_whys", "fishbone", "first_principles", or None

        Returns:
            Complete system prompt for Claude
        """
        # Start with main prompt
        prompt = self.main_prompt

        # Add specific methodology if requested
        if methodology and methodology in self.methodologies:
            prompt += f"\n\n# ACTIVE METHODOLOGY:\n{self.methodologies[methodology]}"

        # Always include psychological techniques
        prompt += f"\n\n# COMMUNICATION TECHNIQUES:\n{self.methodologies['psychological']}"

        return prompt

    def build_analysis_context(
        self,
        problem_description: str,
        methodology: Optional[str] = None
    ) -> str:
        """
        Build context for problem type analysis

        Returns prompt for Claude to analyze and classify problem
        """
        return f"""Analyze this problem and determine the best methodology:

PROBLEM:
{problem_description}

INSTRUCTIONS:
1. Read the problem carefully
2. Classify as: linear, multifactor, or systemic
3. Choose methodology: 5_whys, fishbone, or first_principles
4. Explain your reasoning

Respond ONLY with JSON:
{{
    "type": "linear|multifactor|systemic",
    "methodology": "5_whys|fishbone|first_principles",
    "reasoning": "Brief explanation"
}}
"""

    def build_questioning_context(
        self,
        problem_description: str,
        methodology: str,
        conversation_history: List[Dict],
        current_step: int,
        max_steps: int = 5
    ) -> str:
        """
        Build context for generating next question

        Args:
            problem_description: Original problem
            methodology: Active methodology name
            conversation_history: List of {"role": "...", "content": "..."}
            current_step: Current question number
            max_steps: Maximum questions to ask
        """
        # Format conversation
        history_lines = []
        for i, msg in enumerate(conversation_history, 1):
            prefix = "❓ Question" if msg['role'] == 'assistant' else "💬 Answer"
            history_lines.append(f"{prefix} {i}: {msg['content']}")

        history_text = "\n".join(history_lines) if history_lines else "(Starting conversation)"

        return f"""You are analyzing a problem using the {methodology} methodology.

ORIGINAL PROBLEM:
{problem_description}

CONVERSATION HISTORY:
{history_text}

PROGRESS: Question {current_step}/{max_steps}

TASK:
Generate the next clarifying question based on the methodology.
- Focus on uncovering root causes
- Be specific and actionable
- Build on previous answers
- Keep under 100 words

Respond with ONLY the question text.
"""

    def build_solution_context(
        self,
        problem_description: str,
        methodology: str,
        conversation_history: List[Dict]
    ) -> str:
        """
        Build context for generating final solution
        """
        # Format full conversation
        conversation_text = "\n\n".join([
            f"{'QUESTION' if msg['role'] == 'assistant' else 'ANSWER'}:\n{msg['content']}"
            for msg in conversation_history
        ])

        return f"""Generate a comprehensive solution based on this analysis:

ORIGINAL PROBLEM:
{problem_description}

METHODOLOGY USED:
{methodology}

FULL CONVERSATION:
{conversation_text}

INSTRUCTIONS:
Create actionable solution using PDCA framework.

Respond with JSON:
{{
    "root_cause": "One sentence core issue",
    "analysis": {{
        "methodology": "{methodology}",
        "key_factors": ["factor1", "factor2", "factor3"],
        "leverage_points": ["point1", "point2"]
    }},
    "action_plan": {{
        "immediate": ["action1 (24h)", "action2 (24h)"],
        "this_week": ["step1", "step2"],
        "long_term": ["strategic change"]
    }},
    "metrics": [
        {{"what": "measure1", "target": "goal1"}},
        {{"what": "measure2", "target": "goal2"}}
    ]
}}

ONLY JSON. NO MARKDOWN. NO EXTRA TEXT.
"""

    def list_available_methodologies(self) -> List[str]:
        """Get list of loaded methodology names"""
        return list(self.methodologies.keys())
