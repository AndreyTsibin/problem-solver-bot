# Развертывание кредитной системы монетизации

## Что изменилось

### 1. **Модель данных (User)**
- ❌ Удалено: `is_premium`, `free_problems_left`
- ✅ Добавлено:
  - `problems_remaining` — доступные кредиты на решения (по умолчанию: 1)
  - `discussion_credits` — дополнительные вопросы для обсуждения
  - `last_purchased_package` — последний купленный пакет ('starter', 'medium', 'large')

### 2. **Пакеты решений**

| Пакет | Решений | Цена | Базовых вопросов в обсуждении |
|-------|---------|------|-------------------------------|
| **Starter** | 5 | 100⭐ (~$2) | 3 |
| **Medium** | 15 | 250⭐ (~$5) | 5 |
| **Large** | 50 | 700⭐ (~$14) | 10 |

### 3. **Пакеты вопросов для обсуждения**

| Пакет | Вопросов | Цена |
|-------|----------|------|
| Малый | 5 | 50⭐ (~$1) |
| Средний | 15 | 120⭐ (~$2.4) |

### 4. **Система обсуждений**

После получения решения пользователь может:
- Задать базовые вопросы (лимит зависит от купленного пакета)
- Купить дополнительные вопросы
- Начать новую сессию (тратит 1 кредит решения)

**Логика вопросов:**
- Базовый лимит определяется по `last_purchased_package`
- Дополнительные вопросы списываются из `discussion_credits`

## Инструкция по развертыванию

### Шаг 1: Миграция базы данных

```bash
# На VPS или локально
cd /opt/problem-solver-bot  # или путь к проекту
source venv/bin/activate
python3 migrate_to_credits.py
```

**Результат:**
- Старые пользователи с `is_premium=True` получат 50 кредитов (Large пакет)
- Старые пользователи с `free_problems_left=N` получат N кредитов
- Создастся резервная таблица `users_backup_old_schema`

### Шаг 2: Обновление кода

```bash
git pull origin main
pip install -r requirements.txt  # если были изменения в зависимостях
```

### Шаг 3: Перезапуск бота

```bash
# На VPS через systemd
sudo systemctl restart problem-solver-bot
sudo systemctl status problem-solver-bot

# Локально
python -m bot.main
```

### Шаг 4: Проверка работы

1. **Проверка стартового экрана:**
   - Отправь `/start`
   - Должны отобразиться: "Доступно решений: N", "Доступно вопросов: M"

2. **Проверка покупки:**
   - Нажми "💳 Купить решения"
   - Должны появиться 3 пакета решений + кнопка "Купить вопросы"

3. **Проверка обсуждения:**
   - Реши проблему до конца
   - После решения должна быть кнопка "💬 Продолжить обсуждение"
   - Задай вопрос → должен показать счётчик "Вопросов осталось: X/Y"

## Откат в случае проблем

Если что-то пошло не так:

```bash
cd /opt/problem-solver-bot
sqlite3 bot_database.db

# Восстановить из бэкапа
DROP TABLE users;
ALTER TABLE users_backup_old_schema RENAME TO users;
.quit

# Откатить код
git checkout <previous-commit-hash>
sudo systemctl restart problem-solver-bot
```

## Проверка данных в БД

```bash
# Посмотреть пользователей
sqlite3 bot_database.db "SELECT telegram_id, problems_remaining, discussion_credits, last_purchased_package FROM users;"

# Посмотреть платежи
sqlite3 bot_database.db "SELECT user_id, amount, currency, status, created_at FROM payments ORDER BY created_at DESC LIMIT 10;"
```

## Изменения в bot/handlers/

### start.py
- Обновлён текст приветствия (показывает кредиты вместо премиум-статуса)
- Кнопка "💎 Премиум" → "💳 Купить решения"

### payment.py
- Полностью переписан под систему пакетов
- Добавлены обработчики для 5 типов покупок (3 пакета решений + 2 пакета вопросов)

### problem_flow.py
- Проверка лимита изменена с `is_premium / free_problems_left` на `problems_remaining`
- Добавлен режим обсуждения (`discussing_solution` state)
- После решения предлагается "💬 Продолжить обсуждение"

### states.py
- Добавлено новое состояние: `discussing_solution`

### crud.py
- Функция `update_user_premium()` → `update_user_credits()`

## Рекомендации по мониторингу

После развертывания отслеживай:
1. **Конверсию в покупку** — сколько юзеров покупают после использования бесплатного кредита
2. **Популярность пакетов** — какой пакет чаще всего покупают
3. **Использование обсуждений** — задают ли пользователи дополнительные вопросы
4. **Отток** — возвращаются ли пользователи после покупки

```sql
-- Статистика покупок
SELECT
    CASE
        WHEN payload LIKE 'starter%' THEN 'Starter'
        WHEN payload LIKE 'medium%' THEN 'Medium'
        WHEN payload LIKE 'large%' THEN 'Large'
        WHEN payload LIKE 'discussion%' THEN 'Discussions'
    END as package_type,
    COUNT(*) as purchases,
    SUM(amount) as total_revenue
FROM payments
WHERE status = 'completed'
GROUP BY package_type;
```

## FAQ

**Q: Что будет с текущими премиум-пользователями?**
A: Они получат 50 кредитов (эквивалент Large пакета) + пакет 'large' для базовых вопросов.

**Q: Сгорают ли кредиты?**
A: Нет, все кредиты сохраняются навсегда.

**Q: Можно ли купить несколько пакетов подряд?**
A: Да, кредиты суммируются.

**Q: Как работает счётчик вопросов в обсуждении?**
A: Сначала тратятся базовые вопросы (из пакета), потом дополнительные (`discussion_credits`).
