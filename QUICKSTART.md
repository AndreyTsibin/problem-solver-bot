# 🚀 Быстрый старт — Деплой на VPS Timeweb

## Шаг 1: Создание VPS

1. Перейдите на https://timeweb.cloud/my/servers
2. Нажмите **"Создать сервер"**
3. Выберите конфигурацию:
   - **ОС**: Ubuntu 24.04
   - **CPU**: 1 x 3.3 ГГц
   - **RAM**: 2 ГБ
   - **Диск**: 30 ГБ NVMe
   - **Регион**: Нидерланды (AMS-1)
   - **Цена**: ~600₽/мес
4. Создайте сервер и сохраните IP-адрес

---

## Шаг 2: Подготовка репозитория

**ВАЖНО:** Перед деплоем отредактируйте `scripts/deploy.sh`:

```bash
# Откройте файл
nano scripts/deploy.sh

# Найдите строку (примерно строка 15):
REPO_URL="https://github.com/YOUR_USERNAME/problem-solver-bot.git"

# Замените на ваш актуальный URL репозитория:
REPO_URL="https://github.com/AndreyTsibin/problem-solver-bot.git"

# Сохраните (Ctrl+O, Enter, Ctrl+X)
```

**Затем закоммитьте и запушьте изменения:**

```bash
git add scripts/deploy.sh
git commit -m "chore: update repository URL in deployment script"
git push origin main
```

---

## Шаг 3: Подключение к VPS

```bash
ssh root@YOUR_VPS_IP
```

Введите пароль, который был выслан на email.

---

## Шаг 4: Автоматический деплой

```bash
# Клонируйте репозиторий
git clone https://github.com/AndreyTsibin/problem-solver-bot.git
cd problem-solver-bot

# Запустите скрипт автоматического деплоя
sudo bash scripts/deploy.sh
```

**Скрипт выполнит:**
1. ✅ Обновление системы
2. ✅ Установку Python 3.11 и зависимостей
3. ✅ Создание виртуального окружения
4. ✅ Установку пакетов из requirements.txt
5. ✅ Настройку .env файла (интерактивно)
6. ✅ Инициализацию базы данных
7. ✅ Настройку systemd service
8. ✅ Запуск бота

---

## Шаг 5: Настройка .env

Когда скрипт попросит создать `.env`, введите:

```env
BOT_TOKEN=ваш_токен_от_BotFather
CLAUDE_API_KEY=ваш_ключ_от_Anthropic
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
ENVIRONMENT=production
```

**Где взять токены:**
- **BOT_TOKEN**: https://t.me/BotFather → /newbot
- **CLAUDE_API_KEY**: https://console.anthropic.com/settings/keys

Сохраните файл (Ctrl+O, Enter, Ctrl+X).

---

## Шаг 6: Проверка работы

```bash
# Статус бота
sudo systemctl status problem-solver-bot

# Логи в реальном времени
sudo journalctl -u problem-solver-bot -f
```

Если статус **"Active: active (running)"** — всё работает! 🎉

---

## 🔄 Обновление бота

После внесения изменений в код:

```bash
# На VPS
cd /opt/problem-solver-bot
sudo bash scripts/update.sh
```

---

## 💾 Бэкап базы данных

```bash
# Ручной бэкап
sudo bash scripts/backup.sh

# Автоматический (каждый день в 3:00)
sudo crontab -e
# Добавьте строку:
0 3 * * * /opt/problem-solver-bot/scripts/backup.sh
```

---

## 📊 Просмотр логов

```bash
# Интерактивный просмотр
bash scripts/logs.sh

# Или напрямую:
sudo journalctl -u problem-solver-bot -f       # Реальное время
sudo journalctl -u problem-solver-bot -n 100   # Последние 100 строк
sudo journalctl -u problem-solver-bot --since today  # За сегодня
```

---

## 🛠️ Полезные команды

```bash
# Управление ботом
sudo systemctl start problem-solver-bot    # Запустить
sudo systemctl stop problem-solver-bot     # Остановить
sudo systemctl restart problem-solver-bot  # Перезапустить
sudo systemctl status problem-solver-bot   # Статус

# Мониторинг
htop                    # Использование ресурсов
df -h                   # Свободное место на диске
free -h                 # Использование памяти

# База данных
ls -lh /opt/problem-solver-bot/bot_database.db  # Размер БД
```

---

## ⚠️ Решение проблем

### Бот не запускается

```bash
# 1. Проверьте логи
sudo journalctl -u problem-solver-bot -n 50

# 2. Проверьте .env
cat /opt/problem-solver-bot/.env

# 3. Попробуйте запустить вручную
cd /opt/problem-solver-bot
source venv/bin/activate
python -m bot.main
```

### Ошибка "No module named 'bot'"

```bash
# Переустановите зависимости
cd /opt/problem-solver-bot
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
sudo systemctl restart problem-solver-bot
```

### Нехватка памяти (для 1 ГБ VPS)

```bash
# Создайте swap файл
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📚 Дополнительная документация

- **Полная инструкция по деплою**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Описание скриптов**: [scripts/README.md](scripts/README.md)
- **Инструкции для разработки**: [CLAUDE.md](CLAUDE.md)

---

## ✅ Чек-лист успешного деплоя

- [ ] VPS создан на Timeweb (Ubuntu 24.04, 2 ГБ RAM)
- [ ] URL репозитория обновлён в `scripts/deploy.sh`
- [ ] Изменения закоммичены и запушены в GitHub
- [ ] Подключение к VPS по SSH работает
- [ ] Скрипт `deploy.sh` выполнен успешно
- [ ] Файл `.env` создан с правильными токенами
- [ ] База данных инициализирована
- [ ] Systemd service запущен (Active: active)
- [ ] Бот отвечает в Telegram
- [ ] Логи не показывают ошибок

---

**Успешного деплоя! 🚀**
