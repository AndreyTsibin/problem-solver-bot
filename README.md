# Problem Solver Bot — умный коуч для решения проблем

AI-powered Telegram bot that helps analyze and solve problems systematically using Claude AI.

## Description

Problem Solver Bot — это твой личный коуч по решению проблем. Бот использует **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`) для глубокого анализа проблем и создания конкретных планов действий.

### How It Works

Claude автономно определяет лучший подход для каждой проблемы, используя свои знания психологических и аналитических техник (5 Whys, Fishbone, First Principles и др.). Не нужно выбирать методологию — AI сам решает что подходит.

Бот адаптирует общение под профиль пользователя (пол, возраст, профессия, формат работы), предлагая персонализированные решения.

## Features

- 🎯 **Умный анализ проблем** — Claude автоматически определяет тип проблемы и подход
- 👤 **Персонализация** — адаптация под профиль пользователя (пол, возраст, профессия)
- 🤖 **Интерактивный диалог** — 3-5 уточняющих вопросов для глубокого понимания
- 📊 **Структурированные решения** — готовый план действий с эмодзи для удобства
- 💳 **Гибкие тарифы** — подписки (автопродление) и разовые пакеты
- 💰 **Два способа оплаты** — Telegram Stars (международные) и YooKassa (рубли)
- 🎁 **Реферальная программа** — +1 решение за каждого приглашенного друга
- 💬 **Дополнительное обсуждение** — можно задать вопросы после получения решения
- 📋 **История решений** — все проблемы сохраняются в базе данных
- 🔒 **Безопасность данных** — SQLite база с полной конфиденциальностью
- ⚡ **Prompt Caching** — экономия ~80% токенов на повторяющихся запросах

## Tech Stack

- **Python 3.11+**
- **aiogram 3.x** — async Telegram bot framework
- **Anthropic Python SDK** — Claude API integration
- **SQLAlchemy 2.0** — async ORM with SQLite
- **structlog** — structured logging

## Installation

### Prerequisites

- Python 3.11 or higher
- Telegram Bot Token (from @BotFather)
- Claude API Key (from console.anthropic.com)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/AndreyTsibin/problem-solver-bot.git
cd problem-solver-bot
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your BOT_TOKEN and CLAUDE_API_KEY
```

5. Run the bot:
```bash
python -m bot.main
```

## Project Structure

```
problem-solver-bot/
├── bot/
│   ├── database/               # Database layer
│   │   ├── models.py          # SQLAlchemy models (User, Problem, Payment, Subscription, Referral)
│   │   ├── crud.py            # CRUD operations
│   │   ├── crud_subscriptions.py  # Subscription-specific operations
│   │   └── engine.py          # Database connection and initialization
│   ├── handlers/              # Telegram message handlers
│   │   ├── start.py           # /start command and onboarding
│   │   ├── profile.py         # User profile management
│   │   ├── problem_flow.py    # Main problem-solving flow (FSM)
│   │   ├── payment.py         # Payment processing (Stars + YooKassa)
│   │   ├── subscription.py    # Subscription management
│   │   ├── history.py         # Problem history
│   │   ├── referral.py        # Referral program
│   │   └── settings.py        # User settings
│   ├── services/              # Business logic
│   │   ├── claude_service.py  # Claude API integration (questions, solutions, discussion)
│   │   ├── prompt_builder.py  # Gender-adaptive prompt construction
│   │   ├── subscription_renewal.py  # Background scheduler for auto-renewal
│   │   └── yookassa_service.py     # YooKassa payment integration
│   ├── middleware/            # Middleware
│   │   └── errors.py          # Global error handling
│   ├── keyboards.py           # Persistent keyboards (is_persistent=True)
│   ├── states.py              # FSM states (ProblemSolvingStates, OnboardingStates, ProfileEditStates)
│   ├── config.py              # Environment configuration and pricing
│   ├── logging_config.py      # Structlog setup
│   └── main.py                # Bot entry point
├── scripts/                   # Deployment scripts
│   ├── deploy.sh              # Automated VPS deployment
│   ├── update.sh              # Update bot after changes
│   ├── backup.sh              # Database backup
│   └── logs.sh                # Interactive log viewer
├── CLAUDE.md                  # Instructions for Claude Code
├── TESTING.md                 # Testing guide
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables (not in git)
```

## Usage

1. Start a conversation with the bot in Telegram
2. Press "🚀 Решить проблему" (Solve Problem)
3. Describe your problem in detail
4. Answer 3-5 clarifying questions from Claude
5. Receive a structured solution with action plan
6. (Optional) Ask follow-up questions if you have discussion credits

## Key Architecture Features

### 1. User Personalization
Бот собирает профиль пользователя (опционально):
- Пол (male/female) — адаптирует стиль общения
- Возраст — рассчитывается из даты рождения
- Профессия — контекст для решений
- Формат работы (remote/office/hybrid/student)

Все параметры передаются в Claude через `user_context` для персонализированных промптов.

### 2. Gender-Adaptive Prompts
- **Male**: метрики, логика, минимум эмпатии
- **Female**: контекст, эмоции, краткая валидация + инструменты

Реализовано в [bot/services/prompt_builder.py](bot/services/prompt_builder.py).

### 3. FSM States
- `ProblemSolvingStates` — основной флоу (waiting_for_problem → asking_questions → generating_solution → discussing_solution)
- `OnboardingStates` — сбор профиля (gender → birth_date → occupation → work_format)
- `ProfileEditStates` — редактирование профиля

### 4. Dual Payment System
- **Telegram Stars** — международные платежи (~2₽ за звезду)
- **YooKassa** — российские карты (рубли)

Оба поддерживают подписки с автопродлением и разовые пакеты.

### 5. Prompt Caching
Все запросы к Claude используют `cache_control: {"type": "ephemeral"}` для системных промптов. Экономия ~80% токенов на повторяющихся промптах.

### 6. Free Tier
- 1 бесплатное решение (оптимизировано для конверсии)
- 5 вопросов для обсуждения

### 7. Background Subscription Renewal
Асинхронный планировщик ([bot/services/subscription_renewal.py](bot/services/subscription_renewal.py)) автоматически продлевает подписки и начисляет кредиты.

## Development

**ВАЖНО:** Всегда запускайте бота через `-m` флаг:
```bash
python -m bot.main  # ✓ Correct
python bot/main.py  # ✗ Wrong (import errors)
```

Подробная документация для разработчиков:
- [CLAUDE.md](CLAUDE.md) — инструкции для Claude Code
- [TESTING.md](TESTING.md) — руководство по тестированию

## Deployment

### Quick VPS Deployment (Timeweb Cloud)

**Recommended VPS Configuration:**
- **CPU**: 1 x 3.3 ГГц
- **RAM**: 2 ГБ
- **Disk**: 30 ГБ NVMe
- **Price**: 600₽/мес
- **OS**: Ubuntu 24.04
- **Region**: Netherlands (best latency for Telegram/Claude API)

#### Automated Deployment

```bash
# On your VPS:
git clone https://github.com/AndreyTsibin/problem-solver-bot.git
cd problem-solver-bot
sudo bash scripts/deploy.sh
```

#### Manual Deployment

See detailed instructions in [DEPLOYMENT.md](DEPLOYMENT.md)

#### Available Scripts

- `scripts/deploy.sh` — Full automated deployment
- `scripts/update.sh` — Update bot after code changes
- `scripts/backup.sh` — Backup database
- `scripts/logs.sh` — View logs interactively

#### Useful Commands

```bash
# Service management
sudo systemctl status problem-solver-bot
sudo systemctl restart problem-solver-bot
sudo journalctl -u problem-solver-bot -f

# Update bot
sudo bash scripts/update.sh

# Create backup
sudo bash scripts/backup.sh
```

For complete deployment guide, see [DEPLOYMENT.md](DEPLOYMENT.md)

## Environment Variables

Создайте файл `.env` в корне проекта:

```env
# Required
BOT_TOKEN=your_telegram_bot_token
CLAUDE_API_KEY=your_claude_api_key
YOOKASSA_SHOP_ID=your_yookassa_shop_id
YOOKASSA_SECRET_KEY=your_yookassa_secret_key

# Optional
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

## Team

**Lead Developer & Project Architect**
- Andrew T.

**AI Development Assistant**
- Claude (Anthropic) - AI pair programming and architecture design

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

For issues and questions, please open an issue on GitHub.
