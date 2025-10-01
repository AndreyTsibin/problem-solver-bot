# Tasks for Claude Code

## 📘 КАК ПОЛЬЗОВАТЬСЯ ЭТИМ ФАЙЛОМ

**Для тех, кто первый раз работает с Claude Code:**

1. **Задачи выполняются СТРОГО по порядку** (Task #1 → Task #2 → ...)
2. **Перед началом новой задачи** - проверь что предыдущая работает (есть команды для теста)
3. **Каждая задача** = отдельная ветка в Git (необязательно, но полезно)
4. **Промпты для Claude Code** - просто копируй целиком в терминал `claude-code`
5. **Если что-то не работает** - смотри секцию "Troubleshooting" внизу задачи

---

## ⚙️ ПРЕДВАРИТЕЛЬНАЯ НАСТРОЙКА (Before Task #1)

### 1. Установи Claude Code (если ещё не установлен)
```bash
# На macOS
brew install anthropic/claude/claude

# Проверь установку
claude --version
```

### 2. Получи токены

**Telegram Bot Token:**
1. Открой Telegram, найди @BotFather
2. Отправь `/newbot`
3. Придумай имя: `Problem Solver Bot`
4. Придумай username: `your_problem_solver_bot` (должен заканчиваться на `bot`)
5. Скопируй токен (выглядит так: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Claude API Key:**
1. Зайди на https://console.anthropic.com/
2. Settings → API Keys
3. Create Key → скопируй (начинается с `sk-ant-...`)

### 3. Создай структуру проекта
```bash
cd ~/Projects  # или где у тебя проекты
mkdir problem-solver-bot
cd problem-solver-bot

# Создай папки
mkdir -p bot/{handlers,services,database} methodologies docs

# Создай пустые файлы (мы их заполним через задачи)
touch bot/__init__.py bot/main.py
touch .env.example .gitignore README.md requirements.txt

# Скопируй свои .md файлы в methodologies/
# (main-problem-solver-prompt.md, 5-whys-method.md и т.д.)
```

### 4. Git init (для версионности)
```bash
git init
git add .
git commit -m "Initial project structure"
```

**Готов к Task #1? Погнали! 🚀**

---

## TASK #1: Project Setup & Dependencies
**Priority:** P0 (Блокирует всё)
**Estimated Time:** 2 hours
**Dependencies:** None

### Context
Настроим Python окружение, установим все библиотеки и создадим базовые конфигурационные файлы.

### What You'll Get
- ✅ Virtual environment настроен
- ✅ Все зависимости установлены
- ✅ `.env` файл с токенами готов
- ✅ `.gitignore` чтобы не закоммитить секреты

### Step-by-Step Instructions

**Шаг 1: Создай virtual environment**
```bash
cd ~/Projects/problem-solver-bot
python3 -m venv venv
source venv/bin/activate  # Должен появиться (venv) в начале строки

# Проверь что используется правильный Python
which python  # Должно показать: /Users/your-name/Projects/problem-solver-bot/venv/bin/python
```

**Шаг 2: Используй Claude Code для создания файлов**

Запусти Claude Code:
```bash
claude-code
```

Скопируй и вставь в Claude Code этот промпт:

```
Create project setup files for a Telegram bot with Python:

**File 1: requirements.txt**
Create with these exact dependencies:
```
aiogram==3.4.1
anthropic==0.18.1
sqlalchemy==2.0.27
aiosqlite==0.19.0
python-dotenv==1.0.1
structlog==24.1.0
```

**File 2: .gitignore**
Create standard Python .gitignore that excludes:
- venv/
- __pycache__/
- *.pyc
- .env (important!)
- *.db (SQLite databases)
- .DS_Store
- logs/

**File 3: .env.example**
Create template with:
```
# Telegram Bot API Token (get from @BotFather)
BOT_TOKEN=your_bot_token_here

# Claude API Key (get from console.anthropic.com)
CLAUDE_API_KEY=your_claude_api_key_here

# Database
DATABASE_URL=sqlite+aiosqlite:///bot_database.db

# Environment
ENVIRONMENT=development
```

**File 4: README.md**
Create basic README with:
- Project title: "Problem Solver Telegram Bot"
- Description: "AI-powered bot that helps analyze and solve problems systematically using proven methodologies"
- Installation instructions (refer to this TASKS.md)
- License: MIT

All files should be created in the project root directory.
```

**Шаг 3: Установи зависимости**
```bash
# Убедись что venv активирован (видишь (venv) в терминале)
pip install --upgrade pip
pip install -r requirements.txt

# Проверь что всё установилось
pip list | grep aiogram  # Должен показать aiogram 3.4.1
pip list | grep anthropic  # Должен показать anthropic 0.18.1
```

**Шаг 4: Создай настоящий .env файл**
```bash
cp .env.example .env
nano .env  # Или открой в любом редакторе
```

Вставь свои реальные токены:
```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz  # Твой токен от BotFather
CLAUDE_API_KEY=sk-ant-api03-...  # Твой ключ от Anthropic
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
ENVIRONMENT=development
```

Сохрани файл (Ctrl+O, Enter, Ctrl+X в nano).

### Testing Instructions
```bash
# Проверка 1: Virtual environment активирован?
echo $VIRTUAL_ENV  
# Должен показать путь к venv

# Проверка 2: Зависимости установлены?
python -c "import aiogram; import anthropic; print('✅ All imports OK')"
# Должно вывести: ✅ All imports OK

# Проверка 3: .env файл существует и содержит токены?
cat .env | grep BOT_TOKEN
# Должен показать твой токен (не пустой)

# Проверка 4: Git не трекает секреты?
git status
# .env НЕ должен быть в списке (спасибо .gitignore)
```

### Troubleshooting

**Проблема:** `python3: command not found`
**Решение:** Установи Python 3.11: `brew install python@3.11`

**Проблема:** `pip install` выдаёт ошибки
**Решение:** 
```bash
# Обнови pip
pip install --upgrade pip setuptools wheel
# Попробуй снова
pip install -r requirements.txt
```

**Проблема:** Claude Code не запускается
**Решение:** 
```bash
# Переустанови
brew uninstall claude
brew install anthropic/claude/claude
# Проверь
claude --version
```

### Acceptance Criteria
- [x] `venv` создан и активирован
- [x] Все пакеты из `requirements.txt` установлены
- [x] `.env` файл содержит реальные токены
- [x] `.gitignore` исключает `.env` из Git
- [x] Команды проверки выше отработали без ошибок

**✅ Task #1 Complete! Переходи к Task #2**

---

## TASK #2: Database Models & Setup
**Priority:** P0 (Блокирует Sprint 2)
**Estimated Time:** 4 hours
**Dependencies:** Task #1

### Context
Создадим базу данных SQLite с таблицами для пользователей, сессий, проблем и платежей. Используем SQLAlchemy ORM для работы с БД асинхронно.

### What You'll Get
- ✅ Модели БД (User, Session, Problem, Payment)
- ✅ Асинхронное подключение к SQLite
- ✅ Функции для работы с юзерами
- ✅ Автоматическое создание таблиц при старте

### Prompt for Claude Code

```bash
claude-code
```

Скопируй этот промпт:

```
Create database layer for Telegram bot using SQLAlchemy async with SQLite.

**File: bot/database/__init__.py**
Make it empty (just to make it a package).

**File: bot/database/models.py**

Create SQLAlchemy models with these exact specifications:

```python
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Integer, String, Text, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(32))
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    free_problems_left: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    problems: Mapped[list["Problem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("problems.id", ondelete="SET NULL"))
    state: Mapped[str] = mapped_column(String(50), nullable=False)  # 'diagnosis', 'questioning', 'solution'
    methodology: Mapped[Optional[str]] = mapped_column(String(50))  # '5_whys', 'fishbone', 'first_principles'
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    conversation_history: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")

class Problem(Base):
    __tablename__ = "problems"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    problem_type: Mapped[Optional[str]] = mapped_column(String(50))  # 'linear', 'multifactor', 'systemic'
    methodology: Mapped[Optional[str]] = mapped_column(String(50))
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    action_plan: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    status: Mapped[str] = mapped_column(String(20), default='active')  # 'active', 'solved', 'archived'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    solved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="problems")

class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='XTR')  # Telegram Stars
    provider: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default='pending')
    telegram_payment_id: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="payments")
```

**File: bot/database/engine.py**

Create async database engine and session factory:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.database.models import Base
import os

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Set to False in production
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Initialize database - create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session
```

**File: bot/database/crud.py**

Create CRUD operations (Create, Read, Update, Delete):

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Session, Problem, Payment
from typing import Optional

# User operations
async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    first_name: str
) -> User:
    """Get existing user or create new one"""
    # Try to find existing user
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Update user info if changed
        user.username = username
        user.first_name = first_name
        await session.commit()
        return user
    
    # Create new user
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()

async def update_user_premium(session: AsyncSession, user_id: int, is_premium: bool):
    """Update user premium status"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.is_premium = is_premium
        await session.commit()

# Problem operations
async def create_problem(
    session: AsyncSession,
    user_id: int,
    title: str,
    problem_type: Optional[str] = None,
    methodology: Optional[str] = None
) -> Problem:
    """Create new problem"""
    problem = Problem(
        user_id=user_id,
        title=title,
        problem_type=problem_type,
        methodology=methodology
    )
    session.add(problem)
    await session.commit()
    await session.refresh(problem)
    return problem

async def get_user_problems(session: AsyncSession, user_id: int, limit: int = 10):
    """Get user's recent problems"""
    result = await session.execute(
        select(Problem)
        .where(Problem.user_id == user_id)
        .order_by(Problem.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
```

Requirements:
- All code must have English comments
- Use type hints everywhere
- Follow SQLAlchemy 2.0 async patterns
- Handle potential None values properly
```

### Testing Instructions

```bash
# Проверка 1: Файлы созданы?
ls -la bot/database/
# Должны быть: __init__.py, models.py, engine.py, crud.py

# Проверка 2: Импорты работают?
python -c "from bot.database.models import User, Problem; print('✅ Models import OK')"

# Проверка 3: Создаём БД
python << EOF
import asyncio
from bot.database.engine import init_db

async def test():
    await init_db()
    print("✅ Database created successfully")

asyncio.run(test())
EOF

# Должно создаться bot_database.db в корне проекта

# Проверка 4: БД файл существует?
ls -lh bot_database.db
# Должен показать файл размером ~20KB
```

### Troubleshooting

**Проблема:** `ImportError: No module named 'bot'`
**Решение:**
```bash
# Убедись что запускаешь из корня проекта
pwd  # Должно показать: .../problem-solver-bot

# Добавь корень проекта в PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Проблема:** `sqlalchemy.exc.OperationalError`
**Решение:** Проверь что `DATABASE_URL` в `.env` правильный:
```bash
cat .env | grep DATABASE_URL
# Должно быть: sqlite+aiosqlite:///bot_database.db
```

### Acceptance Criteria
- [x] Все 4 файла созданы в `bot/database/`
- [x] Модели User, Session, Problem, Payment определены
- [x] `init_db()` создаёт таблицы без ошибок
- [x] Файл `bot_database.db` появился в проекте
- [x] CRUD функции `get_or_create_user` импортируются без ошибок

**✅ Task #2 Complete! Переходи к Task #3**

---

## TASK #3: Basic Bot Handlers (/start, /help)
**Priority:** P0
**Estimated Time:** 3 hours
**Dependencies:** Task #1, Task #2

### Context
Создадим главный файл бота с обработчиками команд `/start` и `/help`. Это точка входа - отсюда начинается взаимодействие с пользователем.

### What You'll Get
- ✅ Бот запускается и отвечает на `/start`
- ✅ Красивое приветственное сообщение с кнопками
- ✅ Команда `/help` с инструкциями
- ✅ Автоматическое создание пользователя в БД

### Prompt for Claude Code

```bash
claude-code
```

```
Create main bot file and basic command handlers for Telegram bot using aiogram 3.x.

**File: bot/config.py**

Load environment variables:

```python
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validate required settings
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file")
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY is not set in .env file")
```

**File: bot/handlers/__init__.py**

Make it empty (package marker).

**File: bot/handlers/start.py**

Create start and help command handlers:

```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_or_create_user

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    # Get or create user in database
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
    
    # Create inline keyboard with main actions
    builder = InlineKeyboardBuilder()
    builder.button(text="🆕 Новая проблема", callback_data="new_problem")
    builder.button(text="📋 Мои проблемы", callback_data="my_problems")
    builder.button(text="💎 Премиум", callback_data="premium")
    builder.button(text="ℹ️ Помощь", callback_data="help")
    builder.adjust(1)  # 1 button per row
    
    # Welcome message
    welcome_text = f"""
👋 Привет, {message.from_user.first_name}!

Я помогу тебе систематически разобрать любую проблему и найти решение.

🎯 **Как это работает:**
1. Опиши свою проблему
2. Я задам уточняющие вопросы
3. Ты получишь корневую причину и план действий

📊 **Используемые методики:**
• 5 Почему — для линейных проблем
• Fishbone — для многофакторных ситуаций
• First Principles — для системных вызовов

🎁 **Бесплатно:** {user.free_problems_left} анализа
💎 **Премиум:** безлимит + экспорт решений

Готов начать?
"""
    
    await message.answer(
        text=welcome_text,
        reply_markup=builder.as_markup()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
📚 **Как пользоваться ботом:**

1️⃣ Нажми "🆕 Новая проблема"
2️⃣ Опиши проблему в 2-3 предложениях
3️⃣ Отвечай на мои уточняющие вопросы
4️⃣ Получи детальный план решения

🔍 **Типы проблем:**

**Линейная** — прямая причина-следствие
Пример: "Не могу встать рано утром"
→ Использую методику "5 Почему"

**Многофакторная** — несколько причин
Пример: "Падают продажи в магазине"
→ Использую методику "Fishbone"

**Системная** — сложные взаимосвязи
Пример: "Как выйти на новый рынок"
→ Использую методику "First Principles"

💡 **Советы:**
• Будь конкретным в описании
• Отвечай честно на вопросы
• Не спеши — качество важнее скорости

❓ **Вопросы?** Пиши @your_username
"""
    
    await message.answer(help_text)

@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Handle help button press"""
    await callback.message.answer(cmd_help.__doc__)
    await callback.answer()
```

**File: bot/main.py**

Create main entry point:

```python
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.database.engine import init_db
from bot.handlers import start

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main bot function"""
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    
    # Create bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    # Register routers
    dp.include_router(start.router)
    
    # Start polling
    logger.info("Bot started successfully! Press Ctrl+C to stop.")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Requirements:
- All comments in English
- Use aiogram 3.x async API
- Proper error handling
- Clean code structure
```

### Testing Instructions

```bash
# Проверка 1: Файлы созданы?
ls bot/*.py
ls bot/handlers/*.py
# Должны быть: config.py, main.py, handlers/start.py

# Проверка 2: Конфиг загружается?
python -c "from bot.config import BOT_TOKEN; print('Token loaded:', BOT_TOKEN[:10] + '...')"
# Должно показать первые 10 символов токена

# Проверка 3: ГЛАВНЫЙ ТЕСТ - запуск бота!
python -m bot.main

# Ты должен увидеть:
# INFO - Initializing database...
# INFO - Bot started successfully! Press Ctrl+C to stop.

# Теперь открой Telegram, найди своего бота и напиши /start
# Ты должен получить приветственное сообщение с кнопками!

# Проверь что работает:
# - Кнопка "ℹ️ Помощь" показывает инструкции
# - /help команда тоже работает
# - Твой username появляется в приветствии

# Останови бота: Ctrl+C в терминале
```

### Troubleshooting

**Проблема:** `ValueError: BOT_TOKEN is not set`
**Решение:**
```bash
# Проверь что .env файл существует
cat .env | grep BOT_TOKEN

# Если пустой - добавь токен от BotFather
nano .env
```

**Проблема:** Бот не отвечает в Telegram
**Решение:**
```bash
# 1. Проверь что бот запущен (должно быть "Bot started")
# 2. Проверь что используешь правильного бота (username совпадает)
# 3. Попробуй /start несколько раз
# 4. Проверь логи в терминале - есть ли ошибки?
```

**Проблема:** `ModuleNotFoundError: No module named 'bot'`
**Решение:**
```bash
# Запускай бота как модуль из корня проекта:
cd ~/Projects/problem-solver-bot
python -m bot.main  # НЕ "python bot/main.py"
```

### Acceptance Criteria
- [x] Бот запускается без ошибок
- [x] `/start` показывает приветствие с 4 кнопками
- [x] `/help` показывает инструкции
- [x] Пользователь создаётся в БД (проверь: `sqlite3 bot_database.db "SELECT * FROM users;"`)
- [x] Кнопка "ℹ️ Помощь" работает
- [x] В логах нет критических ошибок

**✅ Task #3 Complete! У тебя работающий бот! 🎉**

**Сделай коммит:**
```bash
git add .
git commit -m "feat: add basic bot handlers (/start, /help)"
```

**Переходи к Task #4 (Claude API Integration)**

---

## TASK #4: Claude API Integration
**Priority:** P0 (Критично для Sprint 2)
**Estimated Time:** 5 hours
**Dependencies:** Task #1

### Context
Интегрируем Claude API для анализа проблем. Создадим сервис который умеет определять тип проблемы и генерировать вопросы.

### What You'll Get
- ✅ ClaudeService для работы с API
- ✅ Определение типа проблемы (linear/multifactor/systemic)
- ✅ Генерация вопросов по методике
- ✅ Retry логика при ошибках

### Prompt for Claude Code

```bash
claude-code
```

```
Create Claude API integration service for problem analysis bot.

**File: bot/services/__init__.py**

Empty file (package marker).

**File: bot/services/claude_service.py**

Create comprehensive Claude API wrapper:

```python
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
```

Requirements:
- All comments and docstrings in English
- Proper error handling with retries
- JSON parsing with fallbacks
- Type hints for all functions
- Handle Claude API rate limits gracefully
```

### Testing Instructions

```bash
# Проверка 1: Файл создан?
ls bot/services/
# Должен быть: claude_service.py

# Проверка 2: Импорт работает?
python -c "from bot.services.claude_service import ClaudeService; print('✅ Import OK')"

# Проверка 3: ТЕСТ API - определение типа проблемы
python << 'EOF'
import asyncio
from bot.services.claude_service import ClaudeService

async def test():
    service = ClaudeService()
    
    # Test problem analysis
    result = await service.analyze_problem_type(
        "Не могу встать рано утром, постоянно просыпаю будильник"
    )
    
    print("✅ Problem analysis result:")
    print(f"  Type: {result['type']}")
    print(f"  Methodology: {result['methodology']}")
    print(f"  Reasoning: {result['reasoning']}")
    
    # Test question generation
    question = await service.generate_question(
        methodology=result['methodology'],
        problem_description="Не могу встать рано утром",
        conversation_history=[],
        step=1
    )
    
    print(f"\n✅ Generated question:\n  {question}")

asyncio.run(test())
EOF

# Должно вывести:
# ✅ Problem analysis result:
#   Type: linear
#   Methodology: 5_whys
#   Reasoning: ...
# 
# ✅ Generated question:
#   Во сколько ты обычно ложишься спать?
```

### Troubleshooting

**Проблема:** `anthropic.AuthenticationError`
**Решение:**
```bash
# Проверь API ключ
cat .env | grep CLAUDE_API_KEY
# Должен начинаться с sk-ant-

# Проверь на сайте что ключ активен:
# https://console.anthropic.com/settings/keys
```

**Проблема:** `json.JSONDecodeError` при тестировании
**Решение:** Это нормально для первых попыток. Код автоматически retry делает. Если после 3 попыток не работает - проверь что Claude API доступен.

**Проблема:** `rate limit exceeded`
**Решение:**
```python
# В claude_service.py увеличь задержку:
time.sleep(5)  # Вместо time.sleep(1)
```

### Acceptance Criteria
- [x] `ClaudeService` класс создан
- [x] `analyze_problem_type()` возвращает валидный JSON
- [x] `generate_question()` возвращает текст вопроса
- [x] `generate_solution()` возвращает структурированное решение
- [x] Retry логика работает (проверь в логах "attempt 2/3")
- [x] Тест выше выполнился успешно

**✅ Task #4 Complete! Claude API готов к использованию! 🎉**

**Сделай коммит:**
```bash
git add .
git commit -m "feat: add Claude API integration service"
```

**Следующая задача: Task #5 - Prompt Builder с твоими методиками**

---

## TASK #5: Methodology Files & Prompt Builder
**Priority:** P0
**Estimated Time:** 2 hours  
**Dependencies:** Task #4

### Context
Создадим систему динамической загрузки твоих .md файлов с методиками и встраивания их в промпты для Claude.

### What You'll Get
- ✅ Автозагрузка всех методик при старте
- ✅ Кэширование файлов в памяти
- ✅ Динамическая сборка промптов
- ✅ Поддержка всех твоих методик

### Pre-Step: Копирование методик

**ВАЖНО! Сначала скопируй свои .md файлы:**

```bash
# Если у тебя методики в другой папке:
cp ~/path/to/your/files/*.md ~/Projects/problem-solver-bot/methodologies/

# Проверь что все файлы на месте:
ls methodologies/
# Должно быть:
# main-problem-solver-prompt.md
# 5-whys-method.md
# fishbone-method.md
# first-principles-method.md
# pdca-solution.md
# psychological-techniques.md
```

### Prompt for Claude Code

```bash
claude-code
```

```
Create prompt building system that dynamically loads methodology files.

**File: bot/services/prompt_builder.py**

Create PromptBuilder class:

```python
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
            "pdca": self._load_file("pdca-solution.md"),
            "psychological": self._load_file("psychological-techniques.md")
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
```

Requirements:
- All comments in English
- Use lru_cache for file loading
- Graceful handling of missing files
- UTF-8 encoding support
- Type hints everywhere
```

### Testing Instructions

```bash
# Проверка 1: Методики скопированы?
ls -lh methodologies/
# Должно быть 6 файлов .md

# Проверка 2: PromptBuilder работает
python << 'EOF'
from bot.services.prompt_builder import PromptBuilder

# Initialize builder
builder = PromptBuilder()

print("\n📚 Available methodologies:")
print(builder.list_available_methodologies())

print("\n📝 System prompt length (with 5_whys):")
prompt = builder.build_system_prompt(methodology="5_whys")
print(f"{len(prompt)} characters")

print("\n✅ First 200 chars of prompt:")
print(prompt[:200] + "...")

print("\n🎯 Analysis context example:")
context = builder.build_analysis_context(
    "Не могу сосредоточиться на работе"
)
print(context[:300] + "...")

print("\n✅ PromptBuilder working correctly!")
EOF

# Должно вывести:
# ✅ Loaded 5 methodology files
# 📚 Available methodologies: ['5_whys', 'fishbone', ...]
# 📝 System prompt length: ~15000 characters
# ✅ First 200 chars of prompt: # РОЛЬ: Эксперт...
# ✅ PromptBuilder working correctly!
```

### Troubleshooting

**Проблема:** `FileNotFoundError: methodologies`
**Решение:**
```bash
# Создай папку и скопируй файлы
mkdir -p methodologies
cp ~/path/to/your/*.md methodologies/

# Или создай symlink если файлы в другом месте
ln -s ~/path/to/methodologies methodologies
```

**Проблема:** Файлы не грузятся (пустой контент)
**Решение:**
```bash
# Проверь кодировку файлов
file methodologies/*.md
# Должно быть: UTF-8 Unicode text

# Если нет, конвертируй:
iconv -f ISO-8859-1 -t UTF-8 file.md > file_utf8.md
```

**Проблема:** Промпт слишком длинный (> 200K токенов)
**Решение:** Это нормально для методик. Claude поддерживает до 200K токенов в контексте. Но можем оптимизировать:
```python
# В prompt_builder.py добавь:
def _truncate_if_needed(self, text: str, max_chars: int = 50000) -> str:
    return text[:max_chars] if len(text) > max_chars else text
```

### Acceptance Criteria
- [x] Все 6 .md файлов в папке `methodologies/`
- [x] `PromptBuilder` загружает файлы без ошибок
- [x] `build_system_prompt()` возвращает полный промпт
- [x] `list_available_methodologies()` показывает 5 методик
- [x] Тест выше выполнился успешно

**✅ Task #5 Complete! Система промптов готова! 🎉**

**Сделай коммит:**
```bash
git add .
git commit -m "feat: add prompt builder with methodology files"
```

---

## 🎊 ПОЗДРАВЛЯЮ! SPRINT 1 ЗАВЕРШЁН!

Ты прошёл 5 задач и создал:
- ✅ Структуру проекта
- ✅ База данных SQLite
- ✅ Работающий бот с /start и /help
- ✅ Интеграция Claude API
- ✅ Система загрузки методик

**Что дальше:**
Sprint 2 - полный цикл решения проблем (Task #6-10)

Готов продолжить или хочешь сначала протестировать что уже есть? 🚀

---

## TASK #6: FSM States & Problem Analysis Flow
**Time:** 6h | **Dependencies:** Task #2, #3, #4, #5

### Prompt for Claude Code

```
Create FSM (Finite State Machine) states and problem analysis handlers.

**File: bot/states.py**

```python
from aiogram.fsm.state import State, StatesGroup

class ProblemSolvingStates(StatesGroup):
    waiting_for_problem = State()
    analyzing_problem = State()
    asking_questions = State()
    generating_solution = State()
```

**File: bot/handlers/problem_flow.py**

```python
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

from bot.states import ProblemSolvingStates
from bot.services.claude_service import ClaudeService
from bot.services.prompt_builder import PromptBuilder
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id, create_problem

router = Router()
claude = ClaudeService()
prompt_builder = PromptBuilder()

@router.callback_query(F.data == "new_problem")
async def start_new_problem(callback: CallbackQuery, state: FSMContext):
    """Handle 'New Problem' button"""
    # Check user limits
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        
        if not user.is_premium and user.free_problems_left <= 0:
            await callback.message.answer(
                "❌ Бесплатный лимит исчерпан!\n\n"
                "Нажми 💎 Премиум чтобы продолжить"
            )
            await callback.answer()
            return
    
    await callback.message.answer(
        "🎯 Опиши свою проблему в 2-3 предложениях.\n\n"
        "Что происходит и почему это важно решить?"
    )
    await state.set_state(ProblemSolvingStates.waiting_for_problem)
    await callback.answer()

@router.message(ProblemSolvingStates.waiting_for_problem)
async def receive_problem(message: Message, state: FSMContext):
    """Analyze problem type"""
    problem_text = message.text
    
    await message.answer("🔍 Анализирую проблему...")
    
    # Analyze with Claude
    analysis = await claude.analyze_problem_type(problem_text)
    
    # Save to state
    await state.update_data(
        problem_description=problem_text,
        problem_type=analysis['type'],
        methodology=analysis['methodology'],
        conversation_history=[],
        current_step=1
    )
    
    # Create problem in DB
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        
        problem = await create_problem(
            session, user.id, problem_text,
            analysis['type'], analysis['methodology']
        )
        await state.update_data(problem_id=problem.id)
        
        # Decrement free problems
        if not user.is_premium:
            user.free_problems_left -= 1
            await session.commit()
    
    methodology_names = {
        '5_whys': '5 Почему',
        'fishbone': 'Fishbone',
        'first_principles': 'First Principles'
    }
    
    await message.answer(
        f"✅ Тип проблемы: **{analysis['type']}**\n"
        f"📊 Методика: **{methodology_names.get(analysis['methodology'], analysis['methodology'])}**\n\n"
        f"Задам несколько вопросов для глубокого анализа 👇"
    )
    
    # Ask first question
    await state.set_state(ProblemSolvingStates.asking_questions)
    await ask_next_question(message, state)

async def ask_next_question(message: Message, state: FSMContext):
    """Generate and send next question"""
    data = await state.get_data()
    
    question = await claude.generate_question(
        methodology=data['methodology'],
        problem_description=data['problem_description'],
        conversation_history=data['conversation_history'],
        step=data['current_step']
    )
    
    # Add to history
    history = data['conversation_history']
    history.append({"role": "assistant", "content": question})
    await state.update_data(conversation_history=history)
    
    # Send with keyboard
    builder = InlineKeyboardBuilder()
    if data['current_step'] >= 3:
        builder.button(text="✅ Хватит, дай решение", callback_data="get_solution")
    builder.button(text="⏭️ Пропустить вопрос", callback_data="skip_question")
    builder.adjust(1)
    
    await message.answer(
        f"❓ Вопрос {data['current_step']}/5:\n\n{question}",
        reply_markup=builder.as_markup()
    )

@router.message(ProblemSolvingStates.asking_questions)
async def receive_answer(message: Message, state: FSMContext):
    """Process user's answer"""
    data = await state.get_data()
    
    # Add answer to history
    history = data['conversation_history']
    history.append({"role": "user", "content": message.text})
    
    step = data['current_step'] + 1
    await state.update_data(
        conversation_history=history,
        current_step=step
    )
    
    # Check if done
    if step > 5:
        await generate_final_solution(message, state)
    else:
        await ask_next_question(message, state)

@router.callback_query(F.data == "get_solution")
async def handle_get_solution(callback: CallbackQuery, state: FSMContext):
    """User wants solution now"""
    await callback.message.answer("🎯 Генерирую решение...")
    await generate_final_solution(callback.message, state)
    await callback.answer()

async def generate_final_solution(message: Message, state: FSMContext):
    """Generate and show final solution"""
    data = await state.get_data()
    
    await state.set_state(ProblemSolvingStates.generating_solution)
    
    solution = await claude.generate_solution(
        problem_description=data['problem_description'],
        methodology=data['methodology'],
        conversation_history=data['conversation_history']
    )
    
    # Format solution message
    solution_text = f"""
🎯 **КОРНЕВАЯ ПРИЧИНА:**
{solution['root_cause']}

📊 **АНАЛИЗ:**
• Методика: {solution['analysis']['methodology']}
• Факторы: {', '.join(solution['analysis']['key_factors'][:3])}

📋 **ПЛАН ДЕЙСТВИЙ:**

**Сейчас (24ч):**
{chr(10).join(['□ ' + a for a in solution['action_plan']['immediate']])}

**Эта неделя:**
{chr(10).join(['□ ' + a for a in solution['action_plan']['this_week']])}

**Долгосрочно:**
{chr(10).join(['□ ' + a for a in solution['action_plan']['long_term']])}

📈 **МЕТРИКИ:**
{chr(10).join([f"• {m['what']} → {m['target']}" for m in solution['metrics']])}
"""
    
    await message.answer(solution_text)
    
    # Save to DB
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from bot.database.models import Problem
        from datetime import datetime
        
        result = await session.execute(
            select(Problem).where(Problem.id == data['problem_id'])
        )
        problem = result.scalar_one_or_none()
        
        if problem:
            problem.root_cause = solution['root_cause']
            problem.action_plan = json.dumps(solution['action_plan'], ensure_ascii=False)
            problem.status = 'solved'
            problem.solved_at = datetime.utcnow()
            await session.commit()
    
    # Back to menu
    builder = InlineKeyboardBuilder()
    builder.button(text="🆕 Новая проблема", callback_data="new_problem")
    builder.button(text="📋 Мои проблемы", callback_data="my_problems")
    builder.adjust(1)
    
    await message.answer("Что дальше?", reply_markup=builder.as_markup())
    await state.clear()

@router.callback_query(F.data == "skip_question")
async def skip_question(callback: CallbackQuery, state: FSMContext):
    """Skip current question"""
    data = await state.get_data()
    step = data['current_step'] + 1
    await state.update_data(current_step=step)
    
    if step > 5:
        await generate_final_solution(callback.message, state)
    else:
        await ask_next_question(callback.message, state)
    
    await callback.answer("Пропущено")
```

Update bot/main.py to include new router:
```python
from bot.handlers import start, problem_flow

# In main():
dp.include_router(start.router)
dp.include_router(problem_flow.router)
```

Requirements:
- FSM for state management
- Async database operations
- Error handling
- English comments
```

### Test
```bash
python -m bot.main
# В Telegram: нажми "🆕 Новая проблема" → опиши проблему → отвечай на вопросы
```

---

## TASK #7: History & My Problems
**Time:** 3h | **Dependencies:** Task #6

### Prompt for Claude Code

```
Create history viewer for solved problems.

**File: bot/handlers/history.py**

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id, get_user_problems

router = Router()

@router.callback_query(F.data == "my_problems")
async def show_problems_list(callback: CallbackQuery):
    """Show user's problems history"""
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        problems = await get_user_problems(session, user.id, limit=10)
        
        if not problems:
            await callback.message.answer("📭 У тебя пока нет решённых проблем")
            await callback.answer()
            return
        
        builder = InlineKeyboardBuilder()
        for p in problems:
            status_emoji = "✅" if p.status == "solved" else "⏳"
            title = p.title[:40] + "..." if len(p.title) > 40 else p.title
            builder.button(
                text=f"{status_emoji} {title}",
                callback_data=f"view_problem_{p.id}"
            )
        builder.button(text="🔙 Назад", callback_data="back_to_menu")
        builder.adjust(1)
        
        await callback.message.answer(
            "📋 **Твои проблемы:**",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("view_problem_"))
async def view_problem_detail(callback: CallbackQuery):
    """Show problem details"""
    problem_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from bot.database.models import Problem
        
        result = await session.execute(
            select(Problem).where(Problem.id == problem_id)
        )
        problem = result.scalar_one_or_none()
        
        if not problem:
            await callback.answer("Проблема не найдена", show_alert=True)
            return
        
        text = f"📝 **Проблема:**\n{problem.title}\n\n"
        
        if problem.root_cause:
            text += f"🎯 **Причина:**\n{problem.root_cause}\n\n"
        
        if problem.action_plan:
            plan = json.loads(problem.action_plan)
            text += "📋 **План:**\n"
            for action in plan.get('immediate', [])[:2]:
                text += f"□ {action}\n"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 К списку", callback_data="my_problems")
        
        await callback.message.answer(text, reply_markup=builder.as_markup())
    
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Return to main menu"""
    from bot.handlers.start import cmd_start
    await cmd_start(callback.message)
    await callback.answer()
```

Add to bot/main.py:
```python
from bot.handlers import start, problem_flow, history

dp.include_router(history.router)
```
```

### Test
```bash
# Реши одну проблему, потом проверь:
# Нажми "📋 Мои проблемы" → должна показаться твоя проблема
```

---

## TASK #8: Telegram Stars Payment
**Time:** 6h | **Dependencies:** Task #3

### Prompt for Claude Code

```
Integrate Telegram Stars payments for premium access.

**File: bot/handlers/payment.py**

```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import BOT_TOKEN
from bot.database.engine import AsyncSessionLocal
from bot.database.crud import get_user_by_telegram_id, update_user_premium
from bot.database.models import Payment

router = Router()

PREMIUM_PRICE = 100  # Telegram Stars

@router.callback_query(F.data == "premium")
async def show_premium_offer(callback: CallbackQuery):
    """Show premium features and pricing"""
    text = """
💎 **Премиум подписка**

**Что получишь:**
✅ Безлимитные анализы проблем
✅ Приоритетная обработка
✅ Экспорт решений (скоро)

**Цена:** 100 ⭐️ Telegram Stars (~$2)
**Навсегда** (не подписка)
"""
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Купить за 100 ⭐️", callback_data="buy_premium")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    
    await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "buy_premium")
async def initiate_payment(callback: CallbackQuery):
    """Send invoice for premium"""
    prices = [LabeledPrice(label="Премиум доступ", amount=PREMIUM_PRICE)]
    
    await callback.message.answer_invoice(
        title="Problem Solver Premium",
        description="Безлимитные анализы проблем",
        payload=f"premium_{callback.from_user.id}",
        currency="XTR",  # Telegram Stars
        prices=prices
    )
    
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Validate payment before charging"""
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Handle successful payment"""
    payment_info = message.successful_payment
    
    # Save to database
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        
        # Create payment record
        payment = Payment(
            user_id=user.id,
            amount=payment_info.total_amount,
            currency=payment_info.currency,
            provider="telegram_stars",
            status="completed",
            telegram_payment_id=payment_info.telegram_payment_charge_id
        )
        session.add(payment)
        
        # Activate premium
        await update_user_premium(session, user.id, True)
        await session.commit()
    
    await message.answer(
        "🎉 **Спасибо за покупку!**\n\n"
        "✅ Премиум активирован\n"
        "Теперь у тебя безлимитные анализы проблем!"
    )
```

Add to bot/main.py:
```python
from bot.handlers import start, problem_flow, history, payment

dp.include_router(payment.router)
```
```

### Test
```bash
# ⚠️ ВАЖНО: Для тестов используй Telegram Test Environment
# В продакшене оплата сработает с реальными Stars
```

---

## TASK #9: Error Handling & Logging
**Time:** 4h | **Dependencies:** All previous

### Prompt for Claude Code

```
Add comprehensive error handling and structured logging.

**File: bot/middleware/errors.py**

```python
from aiogram import BaseMiddleware
from aiogram.types import Update
import logging

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error handling update: {e}", exc_info=True)
            
            # Try to notify user
            if event.message:
                await event.message.answer(
                    "❌ Произошла ошибка. Попробуй ещё раз или напиши /start"
                )
            elif event.callback_query:
                await event.callback_query.message.answer(
                    "❌ Что-то пошло не так. Попробуй снова."
                )
            
            return None
```

Update bot/main.py:
```python
from bot.middleware.errors import ErrorHandlingMiddleware

# In main():
dp.update.middleware(ErrorHandlingMiddleware())

# Better logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```
```

---

## TASK #10: VPS Deployment
**Time:** 5h | **Dependencies:** All previous

### Manual Steps

```bash
# 1. На VPS создай папку
ssh your-vps
sudo mkdir -p /opt/problem-solver-bot
sudo chown $USER:$USER /opt/problem-solver-bot

# 2. На Mac запуш код в Git
cd ~/Projects/problem-solver-bot
git add .
git commit -m "feat: complete MVP"
git remote add origin https://github.com/yourname/bot.git
git push -u origin main

# 3. На VPS склонируй
cd /opt/problem-solver-bot
git clone https://github.com/yourname/bot.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Создай .env с реальными токенами
nano .env
# Вставь BOT_TOKEN и CLAUDE_API_KEY

# 5. Тестовый запуск
python -m bot.main
# Ctrl+C когда убедишься что работает

# 6. Создай systemd service
sudo nano /etc/systemd/system/problem-solver-bot.service
```

Вставь:
```ini
[Unit]
Description=Problem Solver Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/opt/problem-solver-bot
Environment="PATH=/opt/problem-solver-bot/venv/bin"
ExecStart=/opt/problem-solver-bot/venv/bin/python -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 7. Запусти сервис
sudo systemctl daemon-reload
sudo systemctl enable problem-solver-bot
sudo systemctl start problem-solver-bot
sudo systemctl status problem-solver-bot

# 8. Проверь логи
journalctl -u problem-solver-bot -f
```

---

## 🎉 MVP COMPLETE!

**Что сделали (67 часов):**
- ✅ Sprint 1: Инфраструктура (16h)
- ✅ Sprint 2: Решение проблем (26h)  
- ✅ Sprint 3: Монетизация (20h)
- ✅ Sprint 4: Деплой (5h)

**Проверь финальный чеклист:**
- [ ] Бот работает 24/7 на VPS
- [ ] Полный цикл: проблема → вопросы → решение
- [ ] Telegram Stars оплата работает
- [ ] История проблем сохраняется
- [ ] Логи пишутся без ошибок

**Следующие шаги:**
1. Собери обратную связь от 10-20 юзеров
2. Исправь критичные баги
3. Улучши промпты для Claude
4. Добавь v2 фичи (PDF экспорт, Mini App)

Готово! 🚀
