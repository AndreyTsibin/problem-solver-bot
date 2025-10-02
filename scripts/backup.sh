#!/bin/bash
# Скрипт бэкапа базы данных бота
set -e

echo "======================================"
echo "Problem Solver Bot - Backup Script"
echo "======================================"
echo ""

# Переменные
INSTALL_DIR="/opt/problem-solver-bot"
BACKUP_DIR="$INSTALL_DIR/backups"
DB_FILE="$INSTALL_DIR/bot_database.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bot_database_$DATE.db"

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

# Проверка существования базы данных
if [ ! -f "$DB_FILE" ]; then
    echo "Ошибка: База данных не найдена: $DB_FILE"
    exit 1
fi

echo "Создание бэкапа базы данных..."
cp "$DB_FILE" "$BACKUP_FILE"

# Проверка успешности копирования
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Бэкап создан успешно: $BACKUP_FILE (размер: $SIZE)"
else
    echo "Ошибка: Не удалось создать бэкап"
    exit 1
fi

# Удаление старых бэкапов (старше 30 дней)
echo "Удаление старых бэкапов (старше 30 дней)..."
find "$BACKUP_DIR" -name "bot_database_*.db" -type f -mtime +30 -delete

# Список всех бэкапов
echo ""
echo "Доступные бэкапы:"
ls -lh "$BACKUP_DIR"

echo ""
echo "Бэкап завершен успешно!"
