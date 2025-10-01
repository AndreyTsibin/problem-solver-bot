# Development Roadmap: Problem Solver Bot

## Project Timeline
**Total Duration:** 3-4 недели (MVP)
**Team Size:** 1 Full-Stack Developer + Claude Code
**Release Strategy:** MVP → Beta Testing → Production

---

## Sprint 1: Foundation & Bot Infrastructure (Week 1)
**Goal:** Базовая структура бота + интеграция Claude API

### User Story #1
```
As a user
I want to start the bot and see welcome message
So that I understand what the bot can do

Acceptance Criteria:
- [ ] /start shows welcome message with features list
- [ ] Inline keyboard with "🆕 Новая проблема" button
- [ ] /help explains how to use the bot
- [ ] Bot responds within 1 second
```

### Tasks Breakdown

**Task 1.1: Project Setup** (2h)
- Dependencies: none
- Deliverable: Project structure + virtual environment
- Details:
  - Create folder structure (bot/, methodologies/, docs/)
  - Setup venv + requirements.txt
  - Install aiogram, anthropic, sqlalchemy, python-dotenv
  - Create .env.example

**Task 1.2: Basic Bot Handlers** (3h)
- Dependencies: Task 1.1
- Deliverable: /start, /help commands working
- Details:
  - Create main.py with aiogram Bot initialization
  - Handler for /start with inline keyboard
  - Handler for /help with instructions
  - Simple message logging

**Task 1.3: Database Setup** (4h)
- Dependencies: Task 1.1
- Deliverable: SQLite database with all tables
- Details:
  - Create models (User, Session, Problem, Payment)
  - SQLAlchemy async engine setup
  - Alembic migrations (optional for MVP)
  - Helper functions: get_or_create_user()

**Task 1.4: Claude API Integration** (5h)
- Dependencies: Task 1.1
- Deliverable: Working Claude API wrapper
- Details:
  - Create ClaudeService class
  - Method: analyze_problem_type(text) → returns type + methodology
  - Method: ask_question(context) → returns next question
  - Method: generate_solution(history) → returns final plan
  - Error handling + retry logic (3 attempts)
  - Token counting and limits

**Task 1.5: Methodology Files Loader** (2h)
- Dependencies: Task 1.4
- Deliverable: Dynamic prompt builder
- Details:
  - Create PromptBuilder class
  - Load all .md files from methodologies/ folder
  - build_system_prompt(methodology) method
  - build_user_message(session_data) method
  - Cache loaded files in memory

**Sprint 1 Total:** 16 hours

---

## Sprint 2: Problem Analysis Flow (Week 2)
**Goal:** Полный цикл работы с проблемой (от описания до решения)

### User Story #2
```
As a user
I want to describe my problem and get guided analysis
So that I can find the root cause systematically

Acceptance Criteria:
- [ ] User can describe problem in free text
- [ ] Bot determines problem type (linear/multifactor/systemic)
- [ ] Bot asks 3-5 clarifying questions based on methodology
- [ ] Questions are relevant and help dig deeper
- [ ] Bot acknowledges each answer before next question
```

### Tasks Breakdown

**Task 2.1: FSM States Setup** (2h)
- Dependencies: Task 1.2
- Deliverable: aiogram FSM states configured
- Details:
  - Create ProblemSolvingStates class
  - States: waiting_for_problem, analyzing, asking_questions, showing_solution
  - State storage in memory (Redis optional for scale)

**Task 2.2: Problem Type Analysis** (4h)
- Dependencies: Task 1.4, Task 1.5, Task 2.1
- Deliverable: Automatic problem categorization
- Details:
  - Handler: user sends problem description
  - Call Claude API with main-problem-solver-prompt.md
  - Parse response to get problem_type + methodology
  - Save to session in DB
  - Show user: "Определил тип проблемы: {type}, использую методику: {method}"

**Task 2.3: Question-Answer Loop** (6h)
- Dependencies: Task 2.2
- Deliverable: Interactive questioning flow
- Details:
  - Load specific methodology file (5-whys/fishbone/first-principles)
  - Build prompt with conversation history
  - Claude generates next question
  - Save user answer to session.conversation_history (JSON)
  - Repeat until methodology steps completed (3-5 questions)
  - Inline keyboard: "Продолжить" / "Хватит, дай решение"

**Task 2.4: Solution Generation** (5h)
- Dependencies: Task 2.3
- Deliverable: Final action plan
- Details:
  - Trigger: user clicks "Дай решение" or all questions answered
  - Build prompt with full conversation history + PDCA template
  - Claude generates formatted solution (root cause + action plan + metrics)
  - Parse and format output with emojis
  - Save to problems table as solved
  - Show solution in nice formatted message

**Task 2.5: History & Navigation** (3h)
- Dependencies: Task 2.4
- Deliverable: User can view past problems
- Details:
  - Button "📋 Мои проблемы" in main menu
  - List last 10 problems with status (active/solved)
  - Click problem → show full solution
  - Inline keyboard: "Вернуться в меню"

**Sprint 2 Total:** 20 hours

---

## Sprint 3: Monetization & Polish (Week 3)
**Goal:** Freemium модель + Telegram Stars payment

### User Story #3
```
As a user
I want to get 3 free problem analyses
So that I can try the bot before paying

Acceptance Criteria:
- [ ] New user gets 3 free problems
- [ ] Counter shows: "Осталось бесплатных: 2/3"
- [ ] After limit → show premium offer
- [ ] Premium user has unlimited problems
```

### User Story #4
```
As a user
I want to buy premium access via Telegram Stars
So that I can solve unlimited problems

Acceptance Criteria:
- [ ] Button "💎 Премиум" shows pricing
- [ ] Payment via Telegram Stars works
- [ ] After payment → is_premium = True instantly
- [ ] Payment receipt saved in database
```

### Tasks Breakdown

**Task 3.1: Freemium Logic** (3h)
- Dependencies: Task 2.4
- Deliverable: Free problems counter
- Details:
  - Middleware: check free_problems_left before analysis
  - If 0 and not premium → show paywall message
  - Decrement counter after problem created
  - Show remaining count in /start message

**Task 3.2: Telegram Stars Payment** (6h)
- Dependencies: Task 3.1
- Deliverable: Working payment flow
- Details:
  - Create invoice via Bot API (100 Stars = ~$2)
  - Handler for pre_checkout_query (validation)
  - Handler for successful_payment (activate premium)
  - Update user.is_premium = True
  - Save payment to payments table
  - Send confirmation message

**Task 3.3: Premium Features** (2h)
- Dependencies: Task 3.2
- Deliverable: Premium perks
- Details:
  - Unlimited problems
  - Priority badge in messages
  - "Export в PDF" button (заглушка на будущее)

**Task 3.4: Error Handling & UX** (4h)
- Dependencies: All previous
- Deliverable: Robust error handling
- Details:
  - Try-catch блоки вокруг Claude API calls
  - Friendly error messages ("Упс, что-то пошло не так...")
  - Retry button when API fails
  - Timeout handling (if Claude response > 30s)
  - Logging all errors to file

**Task 3.5: Testing & Bug Fixes** (5h)
- Dependencies: All previous
- Deliverable: Stable bot ready for beta
- Details:
  - Manual testing всех сценариев
  - Edge cases: empty messages, long text (>4096 chars)
  - Payment flow testing (Telegram Test Mode)
  - Database queries optimization
  - Fix found bugs

**Sprint 3 Total:** 20 hours

---

## Sprint 4: Deployment & Launch (Week 4)
**Goal:** Production-ready bot на твоём VPS

### User Story #5
```
As a developer
I want to deploy bot to VPS with auto-restart
So that bot runs 24/7 reliably

Acceptance Criteria:
- [ ] Bot runs as systemd service
- [ ] Auto-restart on crash
- [ ] Logs are accessible and structured
- [ ] Can deploy updates via git pull
```

### Tasks Breakdown

**Task 4.1: VPS Deployment** (3h)
- Dependencies: All previous sprints
- Deliverable: Bot running on server
- Details:
  - SSH to your VPS
  - Clone repo to /opt/problem-solver-bot
  - Setup venv + install requirements
  - Create .env with real tokens
  - Test run: python -m bot.main

**Task 4.2: Systemd Service** (2h)
- Dependencies: Task 4.1
- Deliverable: Auto-start bot service
- Details:
  - Create /etc/systemd/system/problem-solver-bot.service
  - Enable service: systemctl enable
  - Start service: systemctl start
  - Check logs: journalctl -u problem-solver-bot -f

**Task 4.3: Monitoring Setup** (2h)
- Dependencies: Task 4.2
- Deliverable: Basic monitoring
- Details:
  - Integrate Sentry (free tier) for error tracking
  - Healthcheck script (cron job every 5 min)
  - Log rotation setup (logrotate)
  - Create simple dashboard: active users count

**Task 4.4: Documentation** (2h)
- Dependencies: none (parallel)
- Deliverable: Updated README.md
- Details:
  - Project description
  - Features list
  - Installation instructions
  - Environment variables
  - How to contribute

**Task 4.5: Beta Launch** (2h)
- Dependencies: All previous
- Deliverable: First real users
- Details:
  - Share bot link with 10-20 friends
  - Create feedback form (Google Forms)
  - Monitor first sessions
  - Quick fixes if critical bugs found

**Sprint 4 Total:** 11 hours

---

## Dependency Graph

```
Task 1.1 (Project Setup)
  ├─→ Task 1.2 (Bot Handlers)
  │     └─→ Task 2.1 (FSM States)
  │           └─→ Task 2.2 (Problem Analysis)
  │                 └─→ Task 2.3 (Q&A Loop)
  │                       └─→ Task 2.4 (Solution Gen)
  │                             └─→ Task 2.5 (History)
  │                                   └─→ Task 3.1 (Freemium)
  │                                         └─→ Task 3.2 (Payment)
  │                                               └─→ Task 3.3 (Premium)
  ├─→ Task 1.3 (Database)
  │     └─→ Task 2.2 (uses DB)
  ├─→ Task 1.4 (Claude API)
  │     └─→ Task 1.5 (Prompt Builder)
  │           └─→ Task 2.2 (uses prompts)
  └─→ Task 4.1 (Deployment - can start early)

Task 3.4, 3.5 → Can run in parallel with Sprint 4
Task 4.4 (Docs) → Independent, can do anytime
```

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Claude API лимиты достигнуты | High | Medium | Мониторить usage, купить больше кредитов заранее |
| Telegram Bot API rate limits | Medium | Low | Implement message queue, не спамить |
| Database performance деградация | Medium | Low | SQLite → PostgreSQL миграция готова |
| VPS падает | High | Low | Healthcheck + auto-restart, backup БД раз в день |
| Пользователи не платят | Medium | Medium | A/B тест цен (50/100/200 Stars), улучшить value proposition |

---

## Success Metrics (MVP)

- [ ] Бот отвечает < 3 секунды на /start
- [ ] Claude API успешность > 95% (less than 5% errors)
- [ ] Полный цикл проблема → решение < 5 минут
- [ ] Минимум 1 платёж в первую неделю (валидация монетизации)
- [ ] Zero критических багов (крашей бота)
- [ ] 5+ положительных отзывов в бета-тестинге

---

## Post-MVP Roadmap (Optional)

**v2.0 (Month 2):**
- [ ] Telegram Mini App с красивым UI
- [ ] Export решений в PDF/Notion
- [ ] Голосовые заметки (speech-to-text)
- [ ] ЮKassa интеграция (рубли вместо Stars)

**v3.0 (Month 3):**
- [ ] Групповой режим (командные проблемы)
- [ ] Analytics dashboard для юзера
- [ ] Реферальная программа (10% от оплат)
- [ ] Integration с календарём (напоминания о действиях)

---

## Time Allocation Summary

| Sprint | Hours | Days (4h/day) | Week |
|--------|-------|---------------|------|
| Sprint 1 | 16h | 4 дня | Week 1 |
| Sprint 2 | 20h | 5 дней | Week 2 |
| Sprint 3 | 20h | 5 дней | Week 3 |
| Sprint 4 | 11h | 3 дня | Week 4 |
| **Total** | **67h** | **~17 дней** | **3-4 недели** |

*При темпе 4 часа в день (вечера после работы)*

---

**Status:** ✅ Planning Ready
**Next Step:** TASKS.md (детальные задачи для Claude Code)