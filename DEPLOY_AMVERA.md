# Деплой Telegram-бота на Amvera / Docker-хостинг

## Важно про токен

Никогда не вставляйте настоящий Telegram Bot Token в код и не коммитьте его в GitHub.

Токен должен храниться только в переменных окружения хостинга:

```text
BOT_TOKEN=ваш_токен_из_BotFather
```

Если токен уже был отправлен в чат или опубликован, его нужно перевыпустить в BotFather:

```text
/revoke
```

или открыть нужного бота → **API Token** → **Revoke current token**.

## Что уже готово

В проект добавлен `Dockerfile`. Он запускает бота командой:

```bash
python telegram_bot/bot.py
```

## Переменные окружения

В панели хостинга добавьте:

```text
BOT_TOKEN=<ваш новый Telegram bot token>
MAP_URL=https://wwgame28.github.io/perimeter/web_map/
```

## Деплой

1. Создайте приложение на Amvera или другом Docker-хостинге.
2. Подключите GitHub-репозиторий:

```text
https://github.com/wwgame28/perimeter
```

3. Выберите запуск через Dockerfile.
4. Добавьте переменные окружения `BOT_TOKEN` и `MAP_URL`.
5. Запустите деплой.

## Проверка

После старта откройте Telegram и отправьте боту:

```text
/start
/play
/map
```

Если бот молчит, проверьте логи хостинга. Самая частая ошибка — не задан `BOT_TOKEN`.
