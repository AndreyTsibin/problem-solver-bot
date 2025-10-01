# 📱 Быстрый запуск для тестирования

## 1️⃣ Запусти бот

```bash
source venv/bin/activate
python -m bot.main
```

**Ожидаемый вывод:**
```
✅ Loaded 5 methodology files
[INFO] __main__: Initializing database...
[INFO] __main__: Error handling middleware registered
[INFO] __main__: Bot started successfully! Press Ctrl+C to stop.
[INFO] aiogram.dispatcher: Start polling
```

⚠️ **Оставь терминал открытым!**

---

## 2️⃣ Открой бот в Telegram

1. Открой Telegram на телефоне
2. Найди своего бота (username из BOT_TOKEN)
3. Нажми `/start`

---

## 3️⃣ Тестовый сценарий

### Базовый флоу:
1. **Нажми:** "🚀 Решить проблему"
2. **Опиши проблему:** "Не могу заснуть вечером, хотя очень устаю"
3. **Отвечай на вопросы** (3-5 штук)
4. **Получи решение** с планом действий

### Проверь функции:
- ✅ `/start` - приветствие
- ✅ `/help` - инструкции
- ✅ "📖 История решений" - история
- ✅ "💎 Премиум" - информация о подписке
- ✅ "⏭️ Пропустить вопрос" - скип вопроса
- ✅ "✅ Хватит, дай решение" - досрочное завершение

---

## 4️⃣ Мониторинг

### В основном терминале:
Видишь все логи в реальном времени

### В отдельной вкладке (опционально):
```bash
tail -f bot.log
```

---

## 5️⃣ Остановка

Нажми `Ctrl+C` в терминале с ботом

---

## 🐛 Troubleshooting

**Проблема:** Бот не отвечает
```bash
# Проверь что бот запущен:
ps aux | grep "bot.main"

# Проверь логи на ошибки:
tail -20 bot.log
```

**Проблема:** "Module not found"
```bash
# Убедись что venv активирован:
echo $VIRTUAL_ENV  # Должен показать путь к venv

# Переактивируй:
source venv/bin/activate
```

**Проблема:** Ошибки Claude API
```bash
# Проверь ключ:
cat .env | grep CLAUDE_API_KEY

# Проверь баланс на console.anthropic.com
```

---

## 📊 Проверка базы данных

```bash
# Посмотри пользователей:
sqlite3 bot_database.db "SELECT * FROM users;"

# Посмотри проблемы:
sqlite3 bot_database.db "SELECT id, title, methodology, status FROM problems;"
```

---

**Готово! Приятного тестирования! 🚀**
