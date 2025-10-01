# Project Architecture: Problem Solver Telegram Bot

## 1. Technical Context
**Описание:** Telegram бот-коуч для систематического решения проблем с использованием проверенных методик (5 Why's, Fishbone, First Principles). Интеграция Claude API для интеллектуального анализа и диалога с пользователем.

**Ключевые требования:** 
- Многошаговые диалоги с сохранением контекста
- Динамическая загрузка методик в зависимости от типа проблемы
- Монетизация через Telegram Stars (MVP) + внешние платежи (v2)
- Поддержка до 200 одновременных пользователей
- Хранение истории решений пользователя

---

## 2. Technology Stack

### Backend
- **Language:** Python 3.11+
- **Bot Framework:** aiogram 3.x (асинхронный, современный API)
- **AI Integration:** Anthropic Python SDK (Claude API)
- **Database:** SQLite (MVP) → PostgreSQL (production scale)
- **ORM:** SQLAlchemy 2.0 (async support)
- **Environment:** python-dotenv (secrets management)

**Обоснование:** Python + aiogram - оптимальный выбор для быстрого старта ботов с кнопками. SQLite достаточно для 200 пользователей (легко мигрировать на Postgres позже). Claude API через официальный SDK упрощает интеграцию.

### Infrastructure
- **Hosting:** VPS Ubuntu 22.04 / Railway.app (простой deploy)
- **Process Manager:** systemd / PM2
- **Logs:** structlog (структурированное логирование)
- **Monitoring:** Sentry (ошибки) + простой health check endpoint

**Обоснование:** VPS даёт полный контроль за небольшие деньги (~$5/мес). Railway.app - альтернатива для zero-config деплоя.

### Payment
- **MVP:** Telegram Stars (встроенная оплата, комиссия 30%)
- **v2:** ЮKassa/Stripe через webhook

---

## 3. System Architecture

```
┌─────────────────────────────────────────────┐
│         Telegram User Interface             │
│    (кнопки, текст, inline keyboard)         │
└──────────────────┬──────────────────────────┘
                   │ Telegram Bot API
                   ▼
┌─────────────────────────────────────────────┐
│          aiogram Bot Handler                │
│  ┌────────────────────────────────────────┐ │
│  │  Routers:                              │ │
│  │  • /start, /help (commands)            │ │
│  │  • Problem Analysis Flow               │ │
│  │  • Payment Flow                        │ │
│  │  • History Management                  │ │
│  └────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐      ┌──────────────────┐
│ Claude API   │      │  SQLite Database │
│  Integration │      │                  │
│              │      │  Tables:         │
│ • System     │      │  • users         │
│   Prompt     │      │  • sessions      │
│ • Dynamic    │      │  • problems      │
│   Context    │      │  • payments      │
│ • Methodolo- │      └──────────────────┘
│   gies Files │
└──────────────┘
        │
        └─→ Prompt Builder
            ┌────────────────────────────┐
            │ main-problem-solver.md     │
            │ 5-whys-method.md          │
            │ fishbone-method.md        │
            │ first-principles.md       │
            │ pdca-solution.md          │
            │ psychological-tech.md     │
            └────────────────────────────┘
```

---

## 4. Database Schema Design

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(32),
    first_name VARCHAR(64),
    is_premium BOOLEAN DEFAULT FALSE,
    free_problems_left INTEGER DEFAULT 3, -- freemium limit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Active sessions (multi-step dialog state)
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    problem_id INTEGER, -- FK after problem created
    state VARCHAR(50) NOT NULL, -- 'diagnosis', 'questioning', 'solution'
    methodology VARCHAR(50), -- '5_whys', 'fishbone', 'first_principles'
    current_step INTEGER DEFAULT 1,
    conversation_history TEXT, -- JSON array of messages
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Problems and solutions archive
CREATE TABLE problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL, -- user's problem description
    problem_type VARCHAR(50), -- 'linear', 'multifactor', 'systemic'
    methodology VARCHAR(50),
    root_cause TEXT, -- final analysis result
    action_plan TEXT, -- JSON of solution steps
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'solved', 'archived'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    solved_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Payments history
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'XTR', -- Telegram Stars
    provider VARCHAR(50), -- 'telegram_stars', 'yookassa'
    status VARCHAR(20) DEFAULT 'pending',
    telegram_payment_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_problems_user_id ON problems(user_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);
```

---

## 5. Key Design Decisions

### 5.1 State Management (FSM)
```python
# aiogram FSM states for dialog flow
from aiogram.fsm.state import State, StatesGroup

class ProblemSolvingStates(StatesGroup):
    # Initial state
    waiting_for_problem = State()
    
    # Diagnosis phase
    analyzing_problem_type = State()
    
    # Questioning phase
    asking_questions = State()
    collecting_answers = State()
    
    # Solution phase
    generating_solution = State()
    showing_solution = State()
```

**Почему так:** aiogram FSM позволяет отслеживать состояние каждого пользователя независимо. Это критично для многошаговых диалогов.

### 5.2 Claude API Prompt Builder
```python
# Dynamic prompt construction
class PromptBuilder:
    def __init__(self):
        # Load methodology files once at startup
        self.methodologies = {
            '5_whys': self._load_file('5-whys-method.md'),
            'fishbone': self._load_file('fishbone-method.md'),
            'first_principles': self._load_file('first-principles.md'),
            'pdca': self._load_file('pdca-solution.md')
        }
        self.base_prompt = self._load_file('main-problem-solver-prompt.md')
    
    def build_system_prompt(self, methodology: str = None) -> str:
        """Build system prompt with optional methodology context"""
        prompt = self.base_prompt
        
        if methodology and methodology in self.methodologies:
            prompt += f"\n\n# ACTIVE METHODOLOGY:\n{self.methodologies[methodology]}"
        
        return prompt
    
    def build_user_message(self, session_data: dict) -> str:
        """Build user message with conversation history"""
        context = f"""
Current problem: {session_data['problem_description']}
Methodology: {session_data['methodology']}
Step: {session_data['current_step']}

Conversation history:
{self._format_history(session_data['conversation_history'])}

Continue the analysis based on the methodology.
"""
        return context
```

**Обоснование:** Методики загружаются один раз при старте бота (эффективность). Промпт собирается динамически в зависимости от фазы диалога.

### 5.3 Conversation Flow
```python
# Example handler for problem analysis
@router.message(ProblemSolvingStates.waiting_for_problem)
async def handle_problem_description(message: Message, state: FSMContext):
    # Save problem description
    await state.update_data(problem_description=message.text)
    
    # Call Claude API to determine problem type
    problem_type = await analyze_problem_type(message.text)
    
    # Save methodology and transition state
    await state.update_data(
        methodology=problem_type['methodology'],
        problem_type=problem_type['type']
    )
    await state.set_state(ProblemSolvingStates.asking_questions)
    
    # Inform user about chosen approach
    methodology_names = {
        '5_whys': '5 Почему',
        'fishbone': 'Fishbone (многофакторный анализ)',
        'first_principles': 'First Principles (системный подход)'
    }
    
    await message.answer(
        f"📊 Анализирую проблему...\n\n"
        f"Определил тип: {problem_type['type']}\n"
        f"Буду использовать методику: {methodology_names[problem_type['methodology']]}\n\n"
        f"Задам несколько уточняющих вопросов 👇"
    )
    
    # Ask first question from Claude
    await ask_next_question(message, state)
```

### 5.4 Free vs Premium Logic
```python
async def check_user_access(user: User, action: str) -> bool:
    """Check if user can perform action (freemium gate)"""
    if action == 'new_problem':
        if user.is_premium:
            return True
        
        if user.free_problems_left > 0:
            user.free_problems_left -= 1
            await user.save()
            return True
        
        # Show premium offer
        return False
    
    if action == 'export_pdf':
        return user.is_premium  # Premium-only feature
    
    return True  # Default allow
```

---

## 6. Security Measures

- [x] **Environment variables** - API keys в .env (не в коде!)
- [x] **Rate limiting** - max 10 сообщений/минуту от юзера (защита от спама)
- [x] **SQL injection protection** - SQLAlchemy ORM (parameterized queries)
- [x] **User input sanitization** - экранирование спецсимволов перед отправкой в Claude
- [x] **Telegram webhook validation** - проверка подписи запросов от Telegram
- [x] **API key rotation** - процедура смены ключей без downtime

---

## 7. Performance Optimization

### Caching Strategy
```python
# Cache frequently used data in memory
from functools import lru_cache

@lru_cache(maxsize=128)
def get_methodology_content(name: str) -> str:
    """Cache methodology files (they don't change)"""
    with open(f'methodologies/{name}.md', 'r') as f:
        return f.read()
```

### Claude API Optimization
- **Streaming responses** - для длинных ответов (лучше UX)
- **Token limits** - max_tokens=1500 для вопросов, 3000 для финального плана
- **Retry logic** - 3 попытки с exponential backoff при 429/500 ошибках

### Database
- **Connection pooling** - переиспользование соединений
- **Batch updates** - группировка обновлений сессий
- **Lazy loading** - подгрузка истории только при запросе

---

## 8. Monitoring & Logging

```python
# Structured logging example
import structlog

logger = structlog.get_logger()

# Log critical events
logger.info(
    "problem_analysis_started",
    user_id=user.telegram_id,
    problem_type=problem_type,
    methodology=methodology
)

logger.error(
    "claude_api_error",
    user_id=user.telegram_id,
    error_type=str(type(e)),
    retry_attempt=retry_count
)
```

**Metrics to track:**
- Claude API response time (p50, p95, p99)
- Number of active sessions per hour
- Conversion rate (free → premium)
- Average problem resolution time
- API error rate

**Tools:**
- Sentry для exception tracking
- Простой healthcheck endpoint: `/health` (для мониторинга uptime)

---

## 9. Deployment Strategy (VPS)

### Production Setup на твоём сервере
```bash
# 1. Install dependencies (если ещё нет)
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3-pip python3-venv git -y

# 2. Create project directory
sudo mkdir -p /opt/problem-solver-bot
sudo chown $USER:$USER /opt/problem-solver-bot
cd /opt/problem-solver-bot

# 3. Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 4. Clone repo and install packages
git clone https://github.com/your-repo/bot.git .
pip install -r requirements.txt

# 5. Create .env file
nano .env
# Add:
# BOT_TOKEN=your_telegram_bot_token
# CLAUDE_API_KEY=your_claude_api_key
# DATABASE_URL=sqlite:///bot_database.db
```

### Systemd Service (авто-запуск и restart)
```bash
# Create service file
sudo nano /etc/systemd/system/problem-solver-bot.service
```

```ini
[Unit]
Description=Problem Solver Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/problem-solver-bot
Environment="PATH=/opt/problem-solver-bot/venv/bin"
ExecStart=/opt/problem-solver-bot/venv/bin/python -m bot.main
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/problem-solver-bot/output.log
StandardError=append:/var/log/problem-solver-bot/error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/problem-solver-bot
sudo chown your_username:your_username /var/log/problem-solver-bot

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable problem-solver-bot
sudo systemctl start problem-solver-bot

# Check status
sudo systemctl status problem-solver-bot

# View logs
tail -f /var/log/problem-solver-bot/output.log
```

### Git Deployment Workflow
```bash
# On your Mac - push updates
git add .
git commit -m "feat: add new feature"
git push origin main

# On VPS - pull and restart
cd /opt/problem-solver-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # if dependencies changed
sudo systemctl restart problem-solver-bot
```

### Health Check Script (optional)
```bash
# Create monitoring script
nano /opt/problem-solver-bot/healthcheck.sh
```

```bash
#!/bin/bash
# Check if bot process is running
if systemctl is-active --quiet problem-solver-bot; then
    echo "✅ Bot is running"
    exit 0
else
    echo "❌ Bot is down, restarting..."
    sudo systemctl restart problem-solver-bot
    exit 1
fi
```

```bash
chmod +x /opt/problem-solver-bot/healthcheck.sh

# Add to crontab (check every 5 minutes)
crontab -e
# Add line:
# */5 * * * * /opt/problem-solver-bot/healthcheck.sh >> /var/log/problem-solver-bot/healthcheck.log 2>&1
```

---

## 10. Cost Estimation (monthly)

**MVP (до 200 пользователей):**
- Railway.app hosting: $5-10
- Claude API (20K активных диалогов): ~$30-50
- Domain + SSL: $2
- **Total: ~$40-65/месяц**

**При росте (1000+ юзеров):**
- VPS (4GB RAM): $20
- Claude API: $150-200
- PostgreSQL managed: $15
- **Total: ~$200/месяц**

**Монетизация покроет расходы:** 10 премиум подписок по 500₽ = 5000₽ (~$50)

---

## 11. Future Enhancements (Post-MVP)

- [ ] **Telegram Mini App UI** - красивый веб-интерфейс внутри Telegram
- [ ] **Voice notes support** - распознавание голоса → текст
- [ ] **Export в PDF/Notion** - сохранение решений
- [ ] **Групповой режим** - решение командных проблем
- [ ] **Analytics dashboard** - статистика для юзера
- [ ] **Referral program** - привлечение новых пользователей

---

**Status:** ✅ Architecture Ready
**Next Step:** PLANNING.md (разбивка на спринты)
