# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Language

**IMPORTANT:** All responses to the user must be in Russian (Русский язык).
Code comments, variable names, and function names must be in English (industry standard).

Example:
- ✓ Response to user: "Создаю файл models.py..." (Russian)
- ✓ Code comment: "# Create database session" (English)

## Project Overview

**Problem Solver Bot** — Telegram bot-coach for systematic problem-solving using AI-powered analysis. Claude autonomously determines the best approach for each problem using its knowledge of psychological and analytical techniques.

**Tech Stack:**
- Python 3.11+ with aiogram 3.x (async Telegram bot framework)
- Anthropic Python SDK (Claude Sonnet 4.5 - latest model)
- SQLAlchemy 2.0 with SQLite (async ORM)
- Structlog (structured logging)

## Development Workflow

**CRITICAL: Git Commit Policy**
- **IMPORTANT:** After EVERY completed task or fix, ALWAYS create a git commit immediately
- This is mandatory to avoid errors and enable easy rollback if needed
- Never accumulate multiple changes without committing
- Commit message format: descriptive, in English, following project style
- Example: `fix: remove skip button` or `feat: add payment validation`

**Using Context7 MCP for Documentation:**
- **IMPORTANT:** Before writing code for new features, ALWAYS fetch current documentation via Context7 MCP server
- Use `mcp__context7__resolve-library-id` to find the library (e.g., "aiogram", "sqlalchemy", "anthropic")
- Use `mcp__context7__get-library-docs` with specific topic to get relevant code examples and best practices
- This ensures you use current API syntax and avoid deprecated patterns
- Example workflow:
  1. Task requires aiogram FSM implementation
  2. Call `resolve-library-id` with "aiogram" → get `/websites/aiogram_dev-en-v3.21.0`
  3. Call `get-library-docs` with topic "FSM handlers" → get current examples
  4. Implement code using fetched documentation patterns

## Common Commands

### Development

**IMPORTANT:** The bot is currently running locally on the development machine. It is NOT deployed to a VPS yet. VPS deployment will be done later.

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
    question = await service.generate_question(
        problem_description="Sample problem",
        conversation_history=[],
        step=1
    )
    print(question)
asyncio.run(test())
EOF

# Check database contents
sqlite3 bot_database.db "SELECT * FROM users;"
```

### Deployment (VPS)

**Production deployment is ready!** Complete VPS deployment infrastructure is available.

**Quick Deploy (on fresh Ubuntu 24.04 VPS):**
```bash
git clone https://github.com/AndreyTsibin/problem-solver-bot.git
cd problem-solver-bot
sudo bash scripts/deploy.sh
```

**Common Operations:**
```bash
# Update bot after code changes
sudo bash scripts/update.sh

# Create database backup
sudo bash scripts/backup.sh

# View logs interactively
bash scripts/logs.sh

# Service management
sudo systemctl status problem-solver-bot
sudo systemctl restart problem-solver-bot
sudo journalctl -u problem-solver-bot -f
```

**Documentation:**
- [DEPLOYMENT.md](DEPLOYMENT.md) — Complete deployment guide
- [QUICKSTART.md](QUICKSTART.md) — 6-step quick start
- [scripts/README.md](scripts/README.md) — Scripts documentation

**Recommended VPS Configuration (Timeweb Cloud):**
- CPU: 1 x 3.3 GHz
- RAM: 2 GB (recommended for stable operation)
- Disk: 30 GB NVMe
- OS: Ubuntu 24.04
- Region: Netherlands (best latency for Telegram/Claude API)
- Price: ~600₽/month

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
│   │   ├── start.py       # /start, /help commands + menu button handlers
│   │   ├── problem_flow.py # Problem analysis FSM flow (simplified)
│   │   ├── history.py     # Problem history viewer
│   │   └── payment.py     # Telegram Stars payment
│   ├── services/          # Business logic
│   │   ├── claude_service.py    # Claude API wrapper (optimized)
│   │   └── prompt_builder.py    # Unified system prompt
│   ├── middleware/        # Bot middleware
│   │   └── errors.py      # Global error handling
│   ├── keyboards.py       # Persistent ReplyKeyboard for UI navigation
│   ├── states.py          # FSM state definitions
│   ├── config.py          # Environment configuration + limits
│   └── main.py           # Bot entry point
└── docs/                 # Architecture documentation
```

### Key Design Patterns

#### 1. FSM-based Conversation Flow
The bot uses aiogram's Finite State Machine to manage multi-step dialogues:
- `waiting_for_problem` → User describes problem
- `analyzing_problem` → Claude analyzes problem type
- `asking_questions` → Interactive Q&A (3-5 questions, Claude decides count)
- `generating_solution` → Claude generates structured solution with emojis
- `discussing_solution` → Additional discussion after solution (if user has discussion credits)

State data is stored in FSM context, conversation history saved to database.

#### 2. Optimized Prompt System
The `PromptBuilder` class contains a single, comprehensive system prompt (~5K tokens):
- One unified prompt with all coaching techniques and guidelines
- No external files loaded (massive token savings vs old 50K approach)
- Claude uses its internal knowledge of methodologies (5 Why's, Fishbone, First Principles, etc.)
- All prompts support UTF-8 Russian text

#### 3. Claude API Integration (Optimized)
`ClaudeService` provides two streamlined operations:
- `generate_question()` → Returns next clarifying question (no pre-determined methodology)
- `generate_solution()` → Returns formatted solution text with emoji structure

**Model:** `claude-sonnet-4-5-20250929` (latest Claude Sonnet 4.5)

**Important:** All methods include:
- 3-attempt retry logic with exponential backoff
- Graceful degradation on API errors
- Direct text responses (no JSON parsing complexity)

#### 4. Persistent Keyboard UI
The bot uses `ReplyKeyboardMarkup` for persistent navigation:
- **Location:** `bot/keyboards.py` → `get_main_menu_keyboard()`
- **Parameters:** `is_persistent=True`, `resize_keyboard=True`
- **Buttons:**
  - 🚀 Решить проблему
  - 📖 История
  - 💳 Премиум
  - ℹ️ Помощь

**Handler Logic:**
- Text button handlers in `bot/handlers/start.py` use `F.text == "..."` filters
- Keyboard always visible - no need for "Back to menu" inline buttons
- Inline buttons only for context-specific actions (skip question, buy package, etc.)

**UX Improvements:**
- Uses `ChatActionSender.typing()` instead of text messages ("Думаю...")
- Shows "печатает..." indicator at top of chat during Claude API calls
- Creates natural conversation feel as if chatting with real person

#### 5. Database Schema
**Users table:**
- `telegram_id` (unique) - User identifier
- `problems_remaining` (int) - Solution credits (default: 1, optimized for conversion)
- `discussion_credits` (int) - Extra discussion questions
- `last_purchased_package` - 'starter', 'medium', or 'large'
- `subscription_id` (int, nullable) - Link to active subscription
- `referred_by` (int, nullable) - Referrer user ID
- `referral_code` (str, unique) - User's referral code
- `referral_credits` (int) - Bonus credits from referrals

**Subscriptions table:**
- `plan` (str) - 'standard' or 'premium'
- `price` (int) - Monthly price in Telegram Stars
- `solutions_per_month` (int) - Solutions renewed monthly
- `discussion_limit` (int) - Questions per session
- `status` (str) - 'active', 'cancelled', 'expired'
- `next_billing_date` (datetime) - Next renewal date

**Referrals table:**
- `referrer_id` (int) - User who referred
- `referred_id` (int) - User who was referred
- `reward_given` (bool) - Whether reward was granted
- `reward_amount` (int) - Credits rewarded

**Sessions table:**
- Tracks active FSM state per user
- `conversation_history` (TEXT) - JSON array of messages
- No methodology field (Claude decides internally)

**Problems table:**
- Archives completed analyses
- `root_cause` (TEXT) - First 500 chars of solution
- `action_plan` (TEXT) - Full solution text
- `status` - 'active', 'solved', 'archived'

**Payments table:**
- Telegram Stars payment records
- Links to package purchases

### Monetization System (Optimized)

**Free tier (new users):**
- **1 free solution** (optimized for conversion)
- 5 discussion questions per session (base limit)
- Can get +1 solution by inviting a friend (referral program)

**Monthly Subscriptions (NEW):**
- **Standard** (299⭐️ ≈ 599₽/мес):
  - 15 solutions per month (renewed automatically)
  - 15 discussion questions per session
  - History for 3 months

- **Premium** (499⭐️ ≈ 999₽/мес):
  - 30 solutions per month (renewed automatically)
  - 25 discussion questions per session
  - Full history
  - Priority processing

**One-time Packages:**
- **Starter** (125⭐️ ≈ 250₽): +5 solutions, 10 discussion questions/session
- **Medium** (300⭐️ ≈ 600₽): +15 solutions, 15 discussion questions/session
- **Large** (600⭐️ ≈ 1200₽): +30 solutions, 25 discussion questions/session

**Discussion Credits:**
- **Small pack** (50⭐️ ≈ 100₽): +5 questions
- **Medium pack** (120⭐️ ≈ 240₽): +15 questions

**Referral Program:**
- Both referrer and referred user get +1 free solution
- Referral code: `/referral` command generates unique code
- Share link: `t.me/YourBot?start=ref_CODE`

**Economic Model:**
- Server cost: 1,000₽/month
- API cost per session: ~6.6₽ (with prompt caching)
- Gross margin: ~80-85% on all tiers
- Break-even point: 3-4 paying users/month

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

### Prompt System (Optimized)
- Single comprehensive system prompt loaded at startup
- ~5K tokens (vs old 50K from methodology files)
- Claude uses internal knowledge of analytical techniques
- No external file dependencies

### Payment Flow (Telegram Stars)
1. User clicks "💳 Премиум"
2. Bot sends invoice via `send_invoice()`
3. `pre_checkout_query` validates payment
4. `successful_payment` handler activates premium + saves to DB

### Deployment Infrastructure
**Current Status:** Production-ready VPS deployment infrastructure available.

**Deployment Features:**
- Automated one-command deployment (`scripts/deploy.sh`)
- Systemd service for auto-restart and boot startup
- Automated update script (`scripts/update.sh`)
- Database backup with rotation (`scripts/backup.sh`)
- Interactive log viewer (`scripts/logs.sh`)

**Architecture:**
- Bot runs as systemd service with auto-restart
- Database: SQLite for MVP (sufficient for 1000s of users, migrate to PostgreSQL for scaling)
- Logs: journalctl + file logging (`bot.log`)
- Environment: `.env` file (never committed, in `.gitignore`)

**Deployment Options Comparison:**

| Option | VPS (Recommended) | Cloud Apps |
|--------|-------------------|------------|
| **Stability** | High | Unstable (CPU spikes, log loss) |
| **Database** | SQLite works | Requires PostgreSQL migration |
| **Control** | Full SSH access | Limited |
| **Price** | 600₽/month | 244₽/month |
| **Best For** | Long-polling bots | Stateless web apps |

**Recommendation:** Use VPS for production deployment. Cloud Apps requires database migration and has stability issues for long-polling Telegram bots.

## Deployment Scripts

### Available Scripts

All scripts are located in `scripts/` directory and are executable:

1. **deploy.sh** — Full automated deployment
   - Updates system packages
   - Installs Python 3.11 and dependencies
   - Creates virtual environment
   - Sets up .env interactively
   - Initializes database
   - Configures systemd service
   - Starts bot

2. **update.sh** — Update bot after code changes
   - Stops bot
   - Pulls latest code from Git
   - Updates dependencies
   - Restarts bot
   - Shows status

3. **backup.sh** — Database backup with rotation
   - Creates timestamped backup
   - Stores in `backups/` directory
   - Deletes backups older than 30 days
   - Shows list of all backups

4. **logs.sh** — Interactive log viewer
   - Real-time logs
   - Last 100 lines
   - Logs for today
   - Last hour
   - Error search

### Usage Examples

```bash
# Initial deployment
sudo bash scripts/deploy.sh

# Update after git push
sudo bash scripts/update.sh

# Manual backup
sudo bash scripts/backup.sh

# Setup automatic daily backup (3:00 AM)
sudo crontab -e
# Add: 0 3 * * * /opt/problem-solver-bot/scripts/backup.sh

# View logs
bash scripts/logs.sh
```

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

### Claude API call
```python
from bot.services.claude_service import ClaudeService

claude = ClaudeService()

# Generate question
question = await claude.generate_question(
    problem_description=problem,
    conversation_history=history,
    step=3
)

# Generate solution
solution_text = await claude.generate_solution(
    problem_description=problem,
    conversation_history=history
)
# Returns formatted text with emojis, ready to send
```

## Critical Files

### Core Application
- [bot/config.py](bot/config.py) - Environment variables (BOT_TOKEN, CLAUDE_API_KEY)
- [bot/main.py](bot/main.py) - Entry point, router registration
- [bot/states.py](bot/states.py) - FSM state definitions
- [bot/services/claude_service.py](bot/services/claude_service.py) - Claude API wrapper
- [bot/services/prompt_builder.py](bot/services/prompt_builder.py) - Prompt construction
- [bot/database/models.py](bot/database/models.py) - SQLAlchemy ORM models

### Deployment Infrastructure
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete VPS deployment guide (12 KB)
- [QUICKSTART.md](QUICKSTART.md) - Quick 6-step deployment (6.4 KB)
- [problem-solver-bot.service](problem-solver-bot.service) - Systemd service file
- [scripts/deploy.sh](scripts/deploy.sh) - Automated deployment script
- [scripts/update.sh](scripts/update.sh) - Update automation
- [scripts/backup.sh](scripts/backup.sh) - Database backup
- [scripts/logs.sh](scripts/logs.sh) - Interactive log viewer
- [scripts/README.md](scripts/README.md) - Scripts documentation

## Troubleshooting

**Bot not responding:**
- Check service status: `sudo systemctl status problem-solver-bot`
- View logs: `journalctl -u problem-solver-bot -f`
- Verify tokens in `.env`

**Claude API errors:**
- Check API key validity at console.anthropic.com
- Verify model name: `claude-sonnet-4-5-20250929` (latest Sonnet 4.5)
- Check rate limits (retry logic handles this automatically)

**Database issues:**
- Ensure `DATABASE_URL` in `.env` is correct
- For SQLite: `sqlite+aiosqlite:///bot_database.db`
- Reinitialize: `python -c "import asyncio; from bot.database.engine import init_db; asyncio.run(init_db())"`

**Import errors:**
- Always run from project root: `python -m bot.main`
- Add to PYTHONPATH if needed: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`
