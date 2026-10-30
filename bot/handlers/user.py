import html
import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import keyboards as kb
from bot.config import Config
from bot.db import Database

router = Router()
log = logging.getLogger(__name__)

PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{7,18}$")


class RequestForm(StatesGroup):
    service = State()
    name = State()
    phone = State()
    comment = State()
    confirm = State()


def esc(text: str | None) -> str:
    return html.escape(text or "—")


# ---------- старт и меню ----------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database, config: Config):
    await state.clear()
    user = message.from_user
    await db.add_user(user.id, user.username, user.full_name)
    await message.answer(
        f"Здравствуйте, {esc(user.first_name)}! 👋\n"
        f"Это бот «{esc(config.business_name)}». Здесь можно посмотреть услуги, "
        f"получить ответы на вопросы и оставить заявку.",
        reply_markup=kb.main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n/start — главное меню\n/cancel — отменить заполнение заявки",
        reply_markup=kb.main_menu(),
    )


@router.message(Command("cancel"))
@router.message(F.text == kb.BTN_CANCEL)
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено. Возвращаю в меню.", reply_markup=kb.main_menu())


@router.message(F.text == kb.BTN_SERVICES)
async def show_services(message: Message):
    lines = [
        f"<b>{esc(title)}</b> — {esc(price)}\n{esc(desc)}"
        for title, desc, price in kb.SERVICES.values()
    ]
    await message.answer("\n\n".join(lines), parse_mode="HTML")


@router.message(F.text == kb.BTN_FAQ)
async def show_faq(message: Message):
    await message.answer("Выберите вопрос:", reply_markup=kb.faq_inline())


@router.callback_query(F.data.startswith("faq:"))
async def faq_answer(call: CallbackQuery):
    idx = int(call.data.split(":")[1])
    if 0 <= idx < len(kb.FAQ):
        question, answer = kb.FAQ[idx]
        await call.message.answer(f"<b>{esc(question)}</b>\n{esc(answer)}", parse_mode="HTML")
    await call.answer()


@router.message(F.text == kb.BTN_CONTACTS)
async def show_contacts(message: Message, config: Config):
    await message.answer(esc(config.contacts), parse_mode="HTML")


# ---------- форма заявки ----------

@router.message(F.text == kb.BTN_REQUEST)
async def request_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(RequestForm.service)
    await message.answer("Какая услуга вас интересует?", reply_markup=kb.cancel_menu())
    await message.answer("Выберите вариант:", reply_markup=kb.services_inline("svc"))


@router.callback_query(RequestForm.service, F.data.startswith("svc:"))
async def request_service(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":")[1]
    if key not in kb.SERVICES:
        await call.answer("Неизвестная услуга", show_alert=True)
        return
    await state.update_data(service=kb.SERVICES[key][0])
    await state.set_state(RequestForm.name)
    await call.message.answer("Как к вам обращаться? Напишите имя.")
    await call.answer()


@router.message(RequestForm.name, F.text)
async def request_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not 2 <= len(name) <= 60:
        await message.answer("Имя должно быть от 2 до 60 символов. Попробуйте ещё раз.")
        return
    await state.update_data(name=name)
    await state.set_state(RequestForm.phone)
    await message.answer(
        "Оставьте номер телефона: напишите его или нажмите кнопку ниже.",
        reply_markup=kb.phone_menu(),
    )


@router.message(RequestForm.phone, F.contact)
async def request_phone_contact(message: Message, state: FSMContext):
    await _save_phone(message, state, message.contact.phone_number)


@router.message(RequestForm.phone, F.text)
async def request_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not PHONE_RE.match(phone):
        await message.answer("Не похоже на номер телефона. Пример: +7 900 123-45-67")
        return
    await _save_phone(message, state, phone)


async def _save_phone(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    await state.set_state(RequestForm.comment)
    await message.answer("Добавьте комментарий к заявке или нажмите «Пропустить».", reply_markup=kb.cancel_menu())
    await message.answer("Комментарий:", reply_markup=kb.skip_inline())


@router.callback_query(RequestForm.comment, F.data == "skip_comment")
async def request_skip_comment(call: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await _show_summary(call.message, state)
    await call.answer()


@router.message(RequestForm.comment, F.text)
async def request_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    if len(comment) > 500:
        await message.answer("Комментарий слишком длинный (максимум 500 символов).")
        return
    await state.update_data(comment=comment)
    await _show_summary(message, state)


async def _show_summary(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(RequestForm.confirm)
    await message.answer(
        "Проверьте заявку:\n\n"
        f"<b>Услуга:</b> {esc(data['service'])}\n"
        f"<b>Имя:</b> {esc(data['name'])}\n"
        f"<b>Телефон:</b> {esc(data['phone'])}\n"
        f"<b>Комментарий:</b> {esc(data.get('comment'))}",
        parse_mode="HTML",
        reply_markup=kb.confirm_inline(),
    )


@router.callback_query(RequestForm.confirm, F.data == "confirm:no")
async def request_decline(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Заявка отменена.", reply_markup=kb.main_menu())
    await call.answer()


@router.callback_query(RequestForm.confirm, F.data == "confirm:yes")
async def request_confirm(call: CallbackQuery, state: FSMContext, db: Database, bot: Bot, config: Config):
    data = await state.get_data()
    user = call.from_user
    await db.add_user(user.id, user.username, user.full_name)
    req_id = await db.add_request(
        user.id, data["service"], data["name"], data["phone"], data.get("comment")
    )
    await state.clear()
    await call.message.answer(
        f"Спасибо! Заявка №{req_id} принята, мы свяжемся с вами в ближайшее время.",
        reply_markup=kb.main_menu(),
    )
    await call.answer()

    username = f"@{user.username}" if user.username else "без username"
    text = (
        f"🔔 <b>Новая заявка №{req_id}</b>\n\n"
        f"<b>Услуга:</b> {esc(data['service'])}\n"
        f"<b>Имя:</b> {esc(data['name'])}\n"
        f"<b>Телефон:</b> {esc(data['phone'])}\n"
        f"<b>Комментарий:</b> {esc(data.get('comment'))}\n"
        f"<b>Telegram:</b> {esc(username)} (id {user.id})"
    )
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as exc:  # админ мог не запускать бота
            log.warning("Не удалось уведомить админа %s: %s", admin_id, exc)
