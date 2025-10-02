#!/bin/bash
# Скрипт просмотра логов бота

SERVICE_NAME="problem-solver-bot"

echo "======================================"
echo "Problem Solver Bot - Logs Viewer"
echo "======================================"
echo ""
echo "Выберите действие:"
echo "1) Просмотр логов в реальном времени"
echo "2) Последние 100 строк логов"
echo "3) Логи за сегодня"
echo "4) Логи за последний час"
echo "5) Поиск ошибок в логах"
echo "6) Выход"
echo ""
read -p "Введите номер: " choice

case $choice in
    1)
        echo "Просмотр логов в реальном времени (Ctrl+C для выхода)..."
        sudo journalctl -u "$SERVICE_NAME" -f
        ;;
    2)
        echo "Последние 100 строк логов:"
        sudo journalctl -u "$SERVICE_NAME" -n 100 --no-pager
        ;;
    3)
        echo "Логи за сегодня:"
        sudo journalctl -u "$SERVICE_NAME" --since today --no-pager
        ;;
    4)
        echo "Логи за последний час:"
        sudo journalctl -u "$SERVICE_NAME" --since "1 hour ago" --no-pager
        ;;
    5)
        echo "Поиск ошибок в логах:"
        sudo journalctl -u "$SERVICE_NAME" | grep -i "error\|exception\|critical" | tail -50
        ;;
    6)
        echo "Выход..."
        exit 0
        ;;
    *)
        echo "Неверный выбор"
        exit 1
        ;;
esac
