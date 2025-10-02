# Deployment Scripts

Автоматизированные скрипты для деплоя и управления ботом на VPS.

## 📋 Доступные скрипты

### 1. `deploy.sh` — Полный автоматический деплой

Выполняет полную установку бота на чистый VPS.

**Использование:**
```bash
sudo bash scripts/deploy.sh
```

**Что делает:**
1. Обновляет систему (apt update && upgrade)
2. Устанавливает Python 3.11, pip, git, утилиты
3. Клонирует репозиторий в /opt/problem-solver-bot
4. Создаёт виртуальное окружение
5. Устанавливает зависимости
6. Создаёт .env (интерактивно)
7. Инициализирует базу данных
8. Настраивает systemd service
9. Запускает бота

**Требования:**
- Чистый Ubuntu 24.04 VPS
- Root доступ
- Интернет соединение

---

### 2. `update.sh` — Обновление бота

Обновляет бот после изменений в Git репозитории.

**Использование:**
```bash
sudo bash scripts/update.sh
```

**Что делает:**
1. Останавливает бота
2. Выполняет `git pull origin main`
3. Обновляет зависимости из requirements.txt
4. Обновляет systemd service (если изменился)
5. Перезапускает бота
6. Показывает статус

**Когда использовать:**
- После внесения изменений в код
- После обновления зависимостей
- После изменения конфигурации

---

### 3. `backup.sh` — Бэкап базы данных

Создаёт резервную копию базы данных SQLite.

**Использование:**
```bash
sudo bash scripts/backup.sh
```

**Что делает:**
1. Копирует bot_database.db в backups/
2. Добавляет дату и время в имя файла
3. Удаляет бэкапы старше 30 дней
4. Показывает список всех бэкапов

**Формат имени:**
```
bot_database_20250102_143025.db
```

**Автоматизация (cron):**
```bash
# Бэкап каждый день в 3:00
sudo crontab -e
# Добавьте:
0 3 * * * /opt/problem-solver-bot/scripts/backup.sh
```

---

### 4. `logs.sh` — Интерактивный просмотр логов

Удобный интерфейс для просмотра логов бота.

**Использование:**
```bash
bash scripts/logs.sh
```

**Доступные опции:**
1. **Реальное время** — непрерывный поток логов (journalctl -f)
2. **Последние 100 строк** — быстрый просмотр недавних событий
3. **Логи за сегодня** — всё с начала дня
4. **Последний час** — события за последние 60 минут
5. **Поиск ошибок** — только ERROR, EXCEPTION, CRITICAL

**Прямые команды:**
```bash
# Реальное время
sudo journalctl -u problem-solver-bot -f

# Последние 100 строк
sudo journalctl -u problem-solver-bot -n 100

# За сегодня
sudo journalctl -u problem-solver-bot --since today

# Только ошибки
sudo journalctl -u problem-solver-bot | grep -i error
```

---

## 🚀 Быстрый старт

### Первый деплой:

```bash
# 1. Создайте VPS (Ubuntu 24.04, 2GB RAM)
# 2. Подключитесь по SSH
ssh root@YOUR_VPS_IP

# 3. Клонируйте репозиторий
git clone https://github.com/YOUR_USERNAME/problem-solver-bot.git
cd problem-solver-bot

# 4. Запустите автоматический деплой
sudo bash scripts/deploy.sh

# 5. Следуйте инструкциям для настройки .env
```

### Обновление после изменений:

```bash
# На VPS
cd /opt/problem-solver-bot
sudo bash scripts/update.sh
```

### Регулярный бэкап:

```bash
# Ручной бэкап
sudo bash scripts/backup.sh

# Автоматический (каждый день в 3:00)
sudo crontab -e
# Добавьте:
0 3 * * * /opt/problem-solver-bot/scripts/backup.sh
```

---

## 🔧 Требования

- **ОС**: Ubuntu 24.04 (или совместимый Debian-based)
- **Права**: Root или sudo доступ
- **Память**: Минимум 1 ГБ RAM (рекомендуется 2 ГБ)
- **Диск**: Минимум 5 ГБ свободного места

---

## ⚠️ Важные замечания

### URL репозитория

В `deploy.sh` замените URL на ваш:
```bash
REPO_URL="https://github.com/YOUR_USERNAME/problem-solver-bot.git"
```

### Пути установки

По умолчанию бот устанавливается в `/opt/problem-solver-bot`.
Если нужно изменить, отредактируйте переменную `INSTALL_DIR` в скриптах.

### Переменные окружения

Скрипт `deploy.sh` попросит создать `.env` файл.
Обязательные переменные:
- `BOT_TOKEN` — токен от @BotFather
- `CLAUDE_API_KEY` — ключ от console.anthropic.com
- `DATABASE_URL` — путь к БД (по умолчанию SQLite)
- `ENVIRONMENT` — production

---

## 🐛 Решение проблем

### Скрипт не запускается

```bash
# Проверьте права
ls -la scripts/
# Должно быть: -rwxr-xr-x

# Если нет, сделайте исполняемым
chmod +x scripts/*.sh
```

### Ошибка "command not found"

```bash
# Используйте bash явно
bash scripts/deploy.sh
# или
sudo bash scripts/update.sh
```

### Git pull конфликты

```bash
# Сохраните локальные изменения
cd /opt/problem-solver-bot
git stash

# Обновите
sudo bash scripts/update.sh

# Верните изменения (если нужно)
git stash pop
```

---

## 📚 Дополнительная информация

Подробная документация по деплою: [DEPLOYMENT.md](../DEPLOYMENT.md)

Вопросы и предложения: https://t.me/andrejtsibin
