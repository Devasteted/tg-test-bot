import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_ids(raw: str) -> list[int]:
    return [int(x) for x in raw.replace(" ", "").split(",") if x.strip().isdigit()]


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: list[int] = field(default_factory=list)
    db_path: str = "data/bot.db"
    business_name: str = "Студия «Пример»"
    contacts: str = "Телефон: +7 900 000-00-00\nАдрес: г. Санкт-Петербург, ул. Примерная, 1\nЧасы работы: пн-пт, 10:00-19:00"


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Не задан BOT_TOKEN. Скопируйте .env.example в .env и впишите токен от @BotFather.")
    return Config(
        bot_token=token,
        admin_ids=_parse_ids(os.getenv("ADMIN_IDS", "")),
        db_path=os.getenv("DB_PATH", "data/bot.db"),
        business_name=os.getenv("BUSINESS_NAME", "Студия «Пример»"),
        contacts=os.getenv(
            "CONTACTS",
            "Телефон: +7 900 000-00-00\nАдрес: г. Санкт-Петербург, ул. Примерная, 1\nЧасы работы: пн-пт, 10:00-19:00",
        ).replace("\\n", "\n"),
    )
