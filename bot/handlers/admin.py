import asyncio
import html
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.config import Config
from bot.db import Database

router = Router()
log = logging.getLogger(__name__)


# Все хендлеры этого роутера доступны только админам из ADMIN_IDS.
# Фильтр выставляется в main.py через router.message.filter(...).
def is_admin(message: Message, config: Config) -> bool:
    return message.from_user is not None and message.from_user.id in config.admin_ids


@router.message(Command("admin"))
async def admin_help(message: Message):
    await message.answer(
        "Админ-команды:\n"
        "/stats — статистика\n"
        "/requests — последние 10 заявок\n"
        "/broadcast текст — рассылка всем пользователям"
    )


@router.message(Command("stats"))
async def stats(message: Message, db: Database):
    s = await db.stats()
    await message.answer(
        f"👥 Пользователей: {s['users']}\n"
        f"📝 Заявок всего: {s['requests']}\n"
        f"📅 Заявок сегодня (UTC): {s['today']}"
    )


@router.message(Command("requests"))
async def last_requests(message: Message, db: Database):
    rows = await db.last_requests(10)
    if not rows:
        await message.answer("Заявок пока нет.")
        return
    parts = []
    for r in rows:
        parts.append(
            f"<b>№{r['id']}</b> · {html.escape(r['created_at'])}\n"
            f"{html.escape(r['service'])} · {html.escape(r['name'])} · {html.escape(r['phone'])}\n"
            f"{html.escape(r['comment'] or '—')}"
        )
    await message.answer("\n\n".join(parts), parse_mode="HTML")


@router.message(Command("broadcast"))
async def broadcast(message: Message, command: CommandObject, db: Database, bot: Bot):
    text = (command.args or "").strip()
    if not text:
        await message.answer("Использование: /broadcast текст сообщения")
        return
    ids = await db.user_ids()
    sent = failed = 0
    await message.answer(f"Начинаю рассылку на {len(ids)} пользователей…")
    for uid in ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception as exc:
            failed += 1
            log.info("Рассылка: не доставлено %s: %s", uid, exc)
        await asyncio.sleep(0.05)  # лимит Telegram ~30 сообщений/сек
    await message.answer(f"Готово. Доставлено: {sent}, не доставлено: {failed}.")
