# Демо-бот: приём заявок (Telegram, aiogram 3)

Бот для малого бизнеса: меню, список услуг, FAQ, контакты, пошаговая форма заявки
с подтверждением, уведомление админа о новой заявке, база данных SQLite и админ-команды.
(https://t.me/demo_zayavki2_bot)

## Возможности

**Для клиента**
- Главное меню: услуги, заявка, вопросы и ответы, контакты
- Форма заявки: услуга → имя → телефон (текстом или кнопкой) → комментарий → подтверждение
- Валидация ввода, отмена на любом шаге (`/cancel` или кнопка)

**Для админа** (ID из `ADMIN_IDS`)
- Мгновенное уведомление о новой заявке
- `/stats` — число пользователей и заявок
- `/requests` — последние 10 заявок
- `/broadcast текст` — рассылка всем пользователям бота

## Настройка

1. Создайте бота у [@BotFather](https://t.me/BotFather) и получите токен.
2. Узнайте свой Telegram ID, например у [@userinfobot](https://t.me/userinfobot).
3. Скопируйте настройки:
   ```bash
   cp .env.example .env
   nano .env   # впишите BOT_TOKEN и ADMIN_IDS
   ```
4. Услуги, цены и FAQ меняются в `bot/keyboards.py` (словарь `SERVICES` и список `FAQ`).

## Запуск локально

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m bot.main
```

## Деплой на сервер: вариант 1, Docker (рекомендуется)

На сервере должны быть установлены Docker и плагин Compose.

```bash
# с вашего компьютера (если SSH на нестандартном порту, например 18999, используйте -P)
scp -r -P 18999 tg-bot-demo user@SERVER_IP:/opt/

# на сервере
cd /opt/tg-bot-demo
cp .env.example .env && nano .env
chmod 600 .env

# папка для базы: бот в контейнере работает под uid 1000
mkdir -p data && sudo chown -R 1000:1000 data

docker compose up -d --build
docker compose logs -f
```

Обновление: загрузите новые файлы и выполните `docker compose up -d --build`.
База хранится в `./data` и сохраняется при пересборке.

### Права на папку `data`

Бот запускается в контейнере под обычным пользователем (uid 1000, не root).
Если папки `data` на сервере нет, Docker создаёт её сам с владельцем root, и бот
не может записать базу. В логах это выглядит так:

```
sqlite3.OperationalError: unable to open database file
```

Исправление (выполнять в папке проекта на сервере):

```bash
sudo chown -R 1000:1000 data
docker compose restart
```

Нужен именно uid `1000`, а не ваш пользователь на сервере: у него uid может быть другим
(например, `1001`).

## Деплой на сервер: вариант 2, systemd без Docker

```bash
sudo useradd --system --home /opt/tg-bot-demo --shell /usr/sbin/nologin tgbot
sudo mkdir -p /opt/tg-bot-demo && sudo chown $USER /opt/tg-bot-demo
# скопируйте файлы проекта в /opt/tg-bot-demo, затем:
cd /opt/tg-bot-demo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env
mkdir -p data
sudo chown -R tgbot:tgbot /opt/tg-bot-demo
sudo chmod 600 /opt/tg-bot-demo/.env

sudo cp deploy/tgbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tgbot
sudo journalctl -u tgbot -f
```

## Безопасность

- Токен хранится только в `.env` (в `.gitignore`), не публикуйте его.
- Если токен утёк, перевыпустите его в @BotFather командой `/revoke`.
- Бот работает через polling: открывать входящие порты на сервере не нужно.

## Структура

```
bot/
  main.py          точка входа
  config.py        настройки из .env
  db.py            SQLite (пользователи, заявки)
  keyboards.py     кнопки, услуги, FAQ
  handlers/
    user.py        меню и форма заявки
    admin.py       админ-команды
deploy/tgbot.service   юнит systemd
Dockerfile, docker-compose.yml
```
