#!/bin/bash
# Скрипт обновления бота на VPS
set -e

echo "======================================"
echo "Problem Solver Bot - Update Script"
echo "======================================"
echo ""

# Переменные
INSTALL_DIR="/opt/problem-solver-bot"
SERVICE_NAME="problem-solver-bot"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "Ошибка: Этот скрипт должен быть запущен с правами root"
    echo "Используйте: sudo bash update.sh"
    exit 1
fi

# Проверка существования директории
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Ошибка: Директория $INSTALL_DIR не найдена"
    echo "Сначала выполните деплой: sudo bash deploy.sh"
    exit 1
fi

echo "Шаг 1/5: Остановка бота..."
systemctl stop "$SERVICE_NAME"

echo "Шаг 2/5: Обновление кода из Git..."
cd "$INSTALL_DIR"
git pull origin main

echo "Шаг 3/5: Обновление зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Шаг 4/5: Обновление systemd service (если изменился)..."
if [ -f "$INSTALL_DIR/problem-solver-bot.service" ]; then
    cp "$INSTALL_DIR/problem-solver-bot.service" "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload
fi

echo "Шаг 5/5: Запуск бота..."
systemctl start "$SERVICE_NAME"

echo ""
echo "======================================"
echo "Обновление завершено успешно!"
echo "======================================"
echo ""
echo "Статус бота:"
systemctl status "$SERVICE_NAME" --no-pager
echo ""
echo "Просмотр логов: sudo journalctl -u $SERVICE_NAME -f"
