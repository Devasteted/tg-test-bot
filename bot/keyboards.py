from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

BTN_SERVICES = "📋 Услуги"
BTN_REQUEST = "📝 Оставить заявку"
BTN_FAQ = "❓ Вопросы и ответы"
BTN_CONTACTS = "📞 Контакты"
BTN_CANCEL = "✖️ Отмена"

# Список услуг (название, описание, цена). Замените на свои.
SERVICES: dict[str, tuple[str, str, str]] = {
    "consult": ("Консультация", "Разберём вашу задачу и предложим решение.", "от 1000 ₽"),
    "basic": ("Базовый пакет", "Стандартный набор работ под типовую задачу.", "от 3000 ₽"),
    "premium": ("Расширенный пакет", "Полный цикл с индивидуальным подходом.", "от 7000 ₽"),
}

FAQ: list[tuple[str, str]] = [
    ("Как быстро вы отвечаете?", "Обычно в течение рабочего дня. Заявки в нерабочее время обрабатываем утром."),
    ("Как проходит оплата?", "Оплата после согласования условий. Подробности уточним при обращении."),
    ("Можно ли изменить заявку?", "Да, напишите нам по контактам из раздела «Контакты», и мы всё поправим."),
]


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SERVICES), KeyboardButton(text=BTN_REQUEST)],
            [KeyboardButton(text=BTN_FAQ), KeyboardButton(text=BTN_CONTACTS)],
        ],
        resize_keyboard=True,
    )


def cancel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]], resize_keyboard=True
    )


def phone_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить мой номер", request_contact=True)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
    )


def services_inline(prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, (title, _, price) in SERVICES.items():
        kb.button(text=f"{title} — {price}", callback_data=f"{prefix}:{key}")
    kb.adjust(1)
    return kb.as_markup()


def faq_inline() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i, (question, _) in enumerate(FAQ):
        kb.button(text=question, callback_data=f"faq:{i}")
    kb.adjust(1)
    return kb.as_markup()


def skip_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Пропустить", callback_data="skip_comment")]]
    )


def confirm_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="confirm:yes"),
                InlineKeyboardButton(text="✖️ Отменить", callback_data="confirm:no"),
            ]
        ]
    )
