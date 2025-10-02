#!/bin/bash
# Скрипт автоматического деплоя бота на VPS
set -e

echo "======================================"
echo "Problem Solver Bot - Deployment Script"
echo "======================================"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "Ошибка: Этот скрипт должен быть запущен с правами root"
    echo "Используйте: sudo bash deploy.sh"
    exit 1
fi

# Переменные
INSTALL_DIR="/opt/problem-solver-bot"
REPO_URL="https://github.com/AndreyTsibin/problem-solver-bot.git"
SERVICE_NAME="problem-solver-bot"

echo "Шаг 1/8: Обновление системы..."
apt update && apt upgrade -y

echo "Шаг 2/8: Установка необходимых пакетов..."
apt install -y python3.11 python3-pip python3-venv git nano htop

echo "Шаг 3/8: Клонирование репозитория..."
if [ -d "$INSTALL_DIR" ]; then
    echo "Директория $INSTALL_DIR уже существует. Удалить и клонировать заново? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
    else
        echo "Использую существующую директорию..."
    fi
else
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

echo "Шаг 4/8: Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

echo "Шаг 5/8: Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Шаг 6/8: Настройка переменных окружения..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo "Файл .env не найден. Создайте его вручную:"
    echo "  nano $INSTALL_DIR/.env"
    echo ""
    echo "Пример содержимого:"
    echo "  BOT_TOKEN=your_bot_token_here"
    echo "  CLAUDE_API_KEY=your_claude_api_key_here"
    echo "  DATABASE_URL=sqlite+aiosqlite:///bot_database.db"
    echo "  ENVIRONMENT=production"
    echo ""
    echo "Создать .env сейчас? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        nano "$INSTALL_DIR/.env"
    fi
else
    echo "Файл .env уже существует"
fi

echo "Шаг 7/8: Инициализация базы данных..."
python << EOF
import asyncio
from bot.database.engine import init_db
asyncio.run(init_db())
print("База данных инициализирована успешно!")
EOF

echo "Шаг 8/8: Настройка systemd service..."
cp "$INSTALL_DIR/problem-solver-bot.service" "/etc/systemd/system/$SERVICE_NAME.service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

echo ""
echo "======================================"
echo "Деплой завершен успешно!"
echo "======================================"
echo ""
echo "Полезные команды:"
echo "  Статус бота:     sudo systemctl status $SERVICE_NAME"
echo "  Логи:            sudo journalctl -u $SERVICE_NAME -f"
echo "  Перезапуск:      sudo systemctl restart $SERVICE_NAME"
echo "  Остановка:       sudo systemctl stop $SERVICE_NAME"
echo ""
echo "Проверьте статус бота:"
systemctl status "$SERVICE_NAME" --no-pager
echo ""
echo "Просмотр логов: sudo journalctl -u $SERVICE_NAME -f"
