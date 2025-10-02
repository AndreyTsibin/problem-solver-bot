# Деплой бота на VPS Timeweb

## 📋 Рекомендованная конфигурация VPS

### Оптимальная конфигурация (600₽/мес):
- **CPU**: 1 x 3.3 ГГц
- **RAM**: 2 ГБ
- **Диск**: 30 ГБ NVMe
- **Канал**: 200 Мбит/с
- **ОС**: Ubuntu 24.04
- **Регион**: Нидерланды (лучшая связь с Telegram/Claude API)

### Альтернатива для экономии (350₽/мес):
- **RAM**: 1 ГБ (требует настройки swap)
- Риск нехватки памяти при обновлениях
- Не рекомендуется для production

---

## 🚀 Пошаговая инструкция по деплою

### Шаг 1: Создание VPS на Timeweb

1. Перейдите на https://timeweb.cloud/my/servers
2. Нажмите "Создать сервер"
3. Выберите параметры:
   - **ОС**: Ubuntu 24.04
   - **Конфигурация**: 2 ГБ RAM, 30 ГБ NVMe
   - **Регион**: Нидерланды (AMS-1)
4. Сохраните SSH ключ или root пароль
5. Дождитесь создания сервера (1-2 минуты)
6. Скопируйте IP-адрес сервера

### Шаг 2: Первое подключение и обновление системы

```bash
# Подключитесь к серверу
ssh root@<IP-адрес>

# Обновите систему
apt update && apt upgrade -y

# Установите необходимые пакеты
apt install python3.11 python3-pip python3-venv git nano htop -y
```

### Шаг 3: Создание пользователя для бота (опционально, для безопасности)

```bash
# Создайте пользователя
adduser botuser

# Добавьте в sudo группу
usermod -aG sudo botuser

# Переключитесь на пользователя
su - botuser
```

### Шаг 4: Клонирование репозитория

```bash
# Перейдите в /opt (или /home/botuser)
cd /opt

# Клонируйте репозиторий (замените на ваш URL)
sudo git clone https://github.com/<ваш-username>/problem-solver-bot.git

# Дайте права пользователю (если используете botuser)
sudo chown -R botuser:botuser problem-solver-bot

# Перейдите в директорию проекта
cd problem-solver-bot
```

### Шаг 5: Настройка виртуального окружения

```bash
# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте окружение
source venv/bin/activate

# Обновите pip
pip install --upgrade pip

# Установите зависимости
pip install -r requirements.txt
```

### Шаг 6: Настройка переменных окружения

```bash
# Создайте .env файл
nano .env
```

Вставьте следующее содержимое (замените на ваши реальные значения):

```env
BOT_TOKEN=your_bot_token_here
CLAUDE_API_KEY=your_claude_api_key_here
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
ENVIRONMENT=production
```

Сохраните (Ctrl+O, Enter, Ctrl+X)

### Шаг 7: Инициализация базы данных

```bash
# Находясь в директории проекта с активированным venv
python << EOF
import asyncio
from bot.database.engine import init_db
asyncio.run(init_db())
EOF
```

Вы должны увидеть сообщение: `Database initialized successfully`

### Шаг 8: Тестовый запуск бота

```bash
# Запустите бота вручную для проверки
python -m bot.main
```

Если всё работает, вы увидите:
```
INFO Initializing database...
INFO Error handling middleware registered
INFO Bot started successfully! Press Ctrl+C to stop.
```

Протестируйте бота в Telegram, затем остановите (Ctrl+C)

### Шаг 9: Создание systemd service для автозапуска

```bash
# Создайте service файл
sudo nano /etc/systemd/system/problem-solver-bot.service
```

Вставьте содержимое (замените пути при необходимости):

```ini
[Unit]
Description=Problem Solver Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/problem-solver-bot
ExecStart=/opt/problem-solver-bot/venv/bin/python -m bot.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=problem-solver-bot

[Install]
WantedBy=multi-user.target
```

Если используете пользователя `botuser`, замените `User=root` на `User=botuser`

Сохраните файл (Ctrl+O, Enter, Ctrl+X)

### Шаг 10: Запуск и настройка автозапуска

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable problem-solver-bot

# Запустите сервис
sudo systemctl start problem-solver-bot

# Проверьте статус
sudo systemctl status problem-solver-bot
```

Вы должны увидеть `Active: active (running)`

### Шаг 11: Просмотр логов

```bash
# Просмотр логов в реальном времени
sudo journalctl -u problem-solver-bot -f

# Просмотр последних 100 строк
sudo journalctl -u problem-solver-bot -n 100

# Просмотр логов за сегодня
sudo journalctl -u problem-solver-bot --since today
```

---

## 🔄 Обновление бота после изменений

### Автоматическое обновление (рекомендуется)

```bash
# Создайте скрипт обновления
sudo nano /opt/update-bot.sh
```

Вставьте:

```bash
#!/bin/bash
set -e

echo "Stopping bot..."
sudo systemctl stop problem-solver-bot

echo "Updating code..."
cd /opt/problem-solver-bot
sudo git pull origin main

echo "Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Starting bot..."
sudo systemctl start problem-solver-bot

echo "Bot updated successfully!"
sudo systemctl status problem-solver-bot
```

Сделайте скрипт исполняемым:

```bash
sudo chmod +x /opt/update-bot.sh
```

Теперь для обновления просто выполните:

```bash
sudo /opt/update-bot.sh
```

### Ручное обновление

```bash
# Остановите бота
sudo systemctl stop problem-solver-bot

# Обновите код
cd /opt/problem-solver-bot
sudo git pull origin main

# Обновите зависимости (если изменился requirements.txt)
source venv/bin/activate
pip install -r requirements.txt

# Запустите бота
sudo systemctl start problem-solver-bot

# Проверьте статус
sudo systemctl status problem-solver-bot
```

---

## 🔧 Полезные команды

### Управление сервисом

```bash
# Запуск
sudo systemctl start problem-solver-bot

# Остановка
sudo systemctl stop problem-solver-bot

# Перезапуск
sudo systemctl restart problem-solver-bot

# Статус
sudo systemctl status problem-solver-bot

# Отключить автозапуск
sudo systemctl disable problem-solver-bot

# Включить автозапуск
sudo systemctl enable problem-solver-bot
```

### Мониторинг

```bash
# Использование ресурсов
htop

# Использование диска
df -h

# Размер базы данных
ls -lh /opt/problem-solver-bot/bot_database.db

# Логи в реальном времени
sudo journalctl -u problem-solver-bot -f
```

### Бэкап базы данных

```bash
# Создание бэкапа
cp /opt/problem-solver-bot/bot_database.db /opt/problem-solver-bot/bot_database_backup_$(date +%Y%m%d).db

# Автоматический бэкап (добавьте в crontab)
sudo crontab -e
# Добавьте строку для ежедневного бэкапа в 3:00
0 3 * * * cp /opt/problem-solver-bot/bot_database.db /opt/problem-solver-bot/backups/bot_database_$(date +\%Y\%m\%d).db
```

---

## 🛡️ Безопасность

### Настройка firewall (UFW)

```bash
# Установите UFW
sudo apt install ufw

# Разрешите SSH
sudo ufw allow 22/tcp

# Включите firewall
sudo ufw enable

# Проверьте статус
sudo ufw status
```

### Защита .env файла

```bash
# Убедитесь, что .env недоступен для чтения другими пользователями
chmod 600 /opt/problem-solver-bot/.env
```

### Автоматические обновления безопасности

```bash
# Установите unattended-upgrades
sudo apt install unattended-upgrades

# Включите автообновления
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 🐛 Решение проблем

### Бот не запускается

```bash
# Проверьте логи
sudo journalctl -u problem-solver-bot -n 50

# Проверьте .env файл
cat /opt/problem-solver-bot/.env

# Попробуйте запустить вручную
cd /opt/problem-solver-bot
source venv/bin/activate
python -m bot.main
```

### Ошибки импорта модулей

```bash
# Переустановите зависимости
cd /opt/problem-solver-bot
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

### База данных заблокирована

```bash
# Остановите бота
sudo systemctl stop problem-solver-bot

# Проверьте процессы
ps aux | grep python

# Убейте зависшие процессы (замените PID)
sudo kill -9 <PID>

# Запустите бота
sudo systemctl start problem-solver-bot
```

### Нехватка памяти (для VPS с 1 ГБ RAM)

```bash
# Создайте swap файл
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Сделайте постоянным
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📊 Мониторинг производительности

### Проверка использования памяти

```bash
# Общая информация
free -h

# Топ процессов по памяти
ps aux --sort=-%mem | head -10
```

### Проверка использования диска

```bash
# Общая информация
df -h

# Топ директорий по размеру
du -h /opt/problem-solver-bot | sort -rh | head -10
```

### Проверка логов

```bash
# Размер логов systemd
sudo journalctl --disk-usage

# Очистка старых логов (оставить последние 7 дней)
sudo journalctl --vacuum-time=7d
```

---

## 🔄 Миграция на другой сервер

```bash
# На старом сервере: создайте бэкап
cd /opt/problem-solver-bot
tar -czf bot_backup.tar.gz bot_database.db .env

# Скачайте бэкап
scp root@<старый-IP>:/opt/problem-solver-bot/bot_backup.tar.gz .

# На новом сервере: загрузите бэкап
scp bot_backup.tar.gz root@<новый-IP>:/opt/problem-solver-bot/

# Распакуйте
cd /opt/problem-solver-bot
tar -xzf bot_backup.tar.gz

# Перезапустите бота
sudo systemctl restart problem-solver-bot
```

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u problem-solver-bot -n 100`
2. Проверьте статус: `sudo systemctl status problem-solver-bot`
3. Проверьте .env файл и токены
4. Убедитесь, что все зависимости установлены

---

**Успешного деплоя! 🚀**
