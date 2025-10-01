# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Language

**IMPORTANT:** All responses to the user must be in Russian (Русский язык).
Code comments, variable names, and function names must be in English (industry standard).

Example:
- ✓ Response to user: "Создаю файл models.py..." (Russian)
- ✓ Code comment: "# Create database session" (English)

## Project Overview

Telegram bot-coach for systematic problem-solving using proven methodologies (5 Why's, Fishbone, First Principles). Integrates Claude API for intelligent analysis and user dialogue.

**Tech Stack:**
- Python 3.11+ with aiogram 3.x (async Telegram bot framework)
- Anthropic Python SDK (Claude API integration)
- SQLAlchemy 2.0 with SQLite (async ORM)
- Structlog (structured logging)

## Task Management Workflow

**Before starting any task:**
1. Read [docs/TRACK.md](docs/TRACK.md) to see current progress and status
2. Read the specific task details from [docs/TASKS.md](docs/TASKS.md)
3. Check which task is marked as "⏳ In Progress" or "⏭️ Next"
4. After completing a task, update checkboxes in [docs/TRACK.md](docs/TRACK.md)

**Task progression:**
- Tasks must be completed in order (Task #1 → Task #2 → ...)
- Each task has specific acceptance criteria and test commands
- Mark tasks as complete only when all checklist items are verified

## Common Commands

### Development
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the bot locally
python -m bot.main

# Run from project root (always use -m flag, NOT direct path)
python -m bot.main  # ✓ Correct
python bot/main.py  # ✗ Wrong (import issues)
```

### Testing
```bash
# Test database creation
python << EOF
import asyncio
from bot.database.engine import init_db
asyncio.run(init_db())
EOF

# Test Claude API integration
python << 'EOF'
import asyncio
from bot.services.claude_service import ClaudeService
async def test():
    service = ClaudeService()
    result = await service.analyze_problem_type("Sample problem description")
    print(result)
asyncio.run(test())
EOF

# Check database contents
sqlite3 bot_database.db "SELECT * FROM users;"
```

### Deployment (VPS)
```bash
# On VPS: Update code
cd /opt/problem-solver-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart problem-solver-bot

# Check service status
sudo systemctl status problem-solver-bot
journalctl -u problem-solver-bot -f  # View logs
```

## Architecture

### Project Structure
```
problem-solver-bot/
├── bot/
│   ├── database/          # SQLAlchemy models and CRUD operations
│   │   ├── models.py      # User, Session, Problem, Payment models
│   │   ├── engine.py      # Async DB engine and session factory
│   │   └── crud.py        # Database operations
│   ├── handlers/          # Telegram message handlers
│   │   ├── start.py       # /start, /help commands
│   │   ├── problem_flow.py # Problem analysis FSM flow
│   │   ├── history.py     # Problem history viewer
│   │   └── payment.py     # Telegram Stars payment
│   ├── services/          # Business logic
│   │   ├── claude_service.py    # Claude API wrapper
│   │   └── prompt_builder.py    # Dynamic prompt construction
│   ├── middleware/        # Bot middleware
│   │   └── errors.py      # Global error handling
│   ├── states.py          # FSM state definitions
│   ├── config.py          # Environment configuration
│   └── main.py           # Bot entry point
├── methodologies/         # Methodology instruction files
│   ├── main-problem-solver-prompt.md
│   ├── 5-whys-method.md
│   ├── fishbone-method.md
│   ├── first-principles-method.md
│   ├── pdca-solution.md
│   └── psychological-techniques.md
└── docs/                 # Architecture documentation
```

### Key Design Patterns

#### 1. FSM-based Conversation Flow
The bot uses aiogram's Finite State Machine to manage multi-step dialogues:
- `waiting_for_problem` → User describes problem
- `analyzing_problem` → Claude determines problem type and methodology
- `asking_questions` → Interactive Q&A based on chosen methodology (3-5 questions)
- `generating_solution` → Claude generates action plan using PDCA framework

State data is stored in FSM context, conversation history saved to database.

#### 2. Dynamic Prompt Construction
The `PromptBuilder` class loads methodology files once at startup (using `@lru_cache`) and builds context-aware prompts:
- Base system prompt from `main-problem-solver-prompt.md`
- Methodology-specific instructions loaded based on problem type
- Conversation history formatted and injected into prompts
- All prompts support UTF-8 Russian text

#### 3. Claude API Integration
`ClaudeService` provides three main operations:
- `analyze_problem_type()` → Returns `{type, methodology, reasoning}` JSON
- `generate_question()` → Returns next clarifying question based on methodology
- `generate_solution()` → Returns structured solution with root cause and action plan

**Important:** All methods include:
- 3-attempt retry logic with exponential backoff
- JSON parsing with fallbacks (handles Claude's markdown wrapping)
- Graceful degradation on API errors

#### 4. Database Schema
**Users table:**
- `telegram_id` (unique) - User identifier
- `is_premium` (bool) - Premium status
- `free_problems_left` (int) - Freemium counter (default: 3)

**Sessions table:**
- Tracks active FSM state per user
- `conversation_history` (TEXT) - JSON array of messages
- `methodology` - Active analysis method

**Problems table:**
- Archives completed analyses
- `root_cause` (TEXT) - Final diagnosis
- `action_plan` (TEXT) - JSON structured action steps
- `status` - 'active', 'solved', 'archived'

**Payments table:**
- Telegram Stars payment records
- Links to premium activation

### Freemium Logic
- New users get 3 free problem analyses
- Counter checked before starting new problem (middleware in `problem_flow.py`)
- Decremented after problem creation
- Premium users (`is_premium=True`) have unlimited access

## Important Development Notes

### Async Patterns
- **Always use async/await** for database operations
- SQLAlchemy sessions created with `async with AsyncSessionLocal() as session:`
- Never block the event loop - use `asyncio` for I/O operations

### Error Handling
- Global error middleware catches all exceptions
- Claude API calls wrapped in try-except with retries
- User-friendly error messages (no stack traces to users)
- All errors logged to `bot.log` with structured format

### Methodology File Management
- Files loaded once at startup (performance optimization)
- Located in `methodologies/` directory
- UTF-8 encoding required (Russian text support)
- Missing files trigger warnings but don't crash the bot

### Payment Flow (Telegram Stars)
1. User clicks "💎 Премиум"
2. Bot sends invoice via `answer_invoice()`
3. `pre_checkout_query` validates payment
4. `successful_payment` handler activates premium + saves to DB

### Deployment Considerations
- Bot runs as systemd service with auto-restart
- Database: SQLite for MVP (migrate to PostgreSQL for 1000+ users)
- Logs: journalctl + file logging (`bot.log`)
- `.env` file must never be committed (in `.gitignore`)

## Common Patterns

### Adding a new handler
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "button_id")
async def handle_button(callback: CallbackQuery):
    await callback.message.answer("Response")
    await callback.answer()

# Register in bot/main.py:
# from bot.handlers import new_handler
# dp.include_router(new_handler.router)
```

### Database operations
```python
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user

async def handler():
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session, telegram_id, username, first_name
        )
        # Modify user...
        await session.commit()
```

### Claude API call with context
```python
from bot.services.claude_service import ClaudeService
from bot.services.prompt_builder import PromptBuilder

claude = ClaudeService()
builder = PromptBuilder()

# Build context
context = builder.build_questioning_context(
    problem_description=problem,
    methodology="5_whys",
    conversation_history=history,
    current_step=3
)

# Call API
response = await claude.generate_question(...)
```

## Critical Files

- [bot/config.py](bot/config.py) - Environment variables (BOT_TOKEN, CLAUDE_API_KEY)
- [bot/main.py](bot/main.py) - Entry point, router registration
- [bot/states.py](bot/states.py) - FSM state definitions
- [bot/services/claude_service.py](bot/services/claude_service.py) - Claude API wrapper
- [bot/services/prompt_builder.py](bot/services/prompt_builder.py) - Prompt construction
- [bot/database/models.py](bot/database/models.py) - SQLAlchemy ORM models

## Troubleshooting

**Bot not responding:**
- Check service status: `sudo systemctl status problem-solver-bot`
- View logs: `journalctl -u problem-solver-bot -f`
- Verify tokens in `.env`

**Claude API errors:**
- Check API key validity at console.anthropic.com
- Verify model name: `claude-sonnet-4-20250514`
- Check rate limits (retry logic handles this automatically)

**Database issues:**
- Ensure `DATABASE_URL` in `.env` is correct
- For SQLite: `sqlite+aiosqlite:///bot_database.db`
- Reinitialize: `python -c "import asyncio; from bot.database.engine import init_db; asyncio.run(init_db())"`

**Import errors:**
- Always run from project root: `python -m bot.main`
- Add to PYTHONPATH if needed: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`
