# Problem Solver Bot — умный коуч для решения проблем

AI-powered Telegram bot that helps analyze and solve problems systematically using Claude AI.

## Description

Problem Solver Bot — это твой личный коуч по решению проблем. Бот использует Claude Sonnet 4.5 (последнюю модель Anthropic) для глубокого анализа проблем и создания конкретных планов действий.

### How It Works

Claude автономно определяет лучший подход для каждой проблемы, используя свои знания психологических и аналитических техник (5 Whys, Fishbone, First Principles и др.). Не нужно выбирать методологию — AI сам решает что подходит.

## Features

- 🎯 **Умный анализ проблем** — Claude автоматически определяет тип проблемы и подход
- 🤖 **Интерактивный диалог** — 3-5 уточняющих вопросов для глубокого понимания
- 📊 **Структурированные решения** — готовый план действий с эмодзи для удобства
- 💳 **Гибкие тарифы** — подписки (автопродление) и разовые пакеты
- 💰 **Два способа оплаты** — Telegram Stars и банковские карты (YooKassa)
- 🎁 **Реферальная программа** — +1 решение за каждого приглашенного друга
- 💬 **Дополнительное обсуждение** — можно задать вопросы после получения решения
- 📋 **История решений** — все проблемы сохраняются
- 🔒 **Безопасность данных** — SQLite база с полной конфиденциальностью

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
│   ├── database/          # SQLAlchemy models and CRUD
│   ├── handlers/          # Telegram message handlers
│   ├── services/          # Business logic (Claude API, prompts)
│   ├── middleware/        # Error handling
│   ├── keyboards.py       # Persistent ReplyKeyboard UI
│   ├── states.py          # FSM state definitions
│   ├── config.py          # Environment configuration
│   └── main.py           # Bot entry point
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables (not in git)
```

## Usage

1. Start a conversation with the bot in Telegram
2. Press "🚀 Решить проблему" (Solve Problem)
3. Describe your problem in detail
4. Answer 3-5 clarifying questions from Claude
5. Receive a structured solution with action plan
6. (Optional) Ask follow-up questions if you have discussion credits

## Development

For detailed development instructions, see [docs/TASKS.md](docs/TASKS.md).

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
