from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_kb(language: str = "uz") -> ReplyKeyboardMarkup:
    if language == "uz":
        buttons = [
            [KeyboardButton(text="📍 Yaqin atrofdagi salonlar")],
            [KeyboardButton(text="🔍 Kategoriyalar")],
            [KeyboardButton(text="📅 Mening bronlarim")],
            [KeyboardButton(text="👤 Shaxsiy kabinet")],
        ]
    else:
        buttons = [
            [KeyboardButton(text="📍 Салоны рядом")],
            [KeyboardButton(text="🔍 Категории")],
            [KeyboardButton(text="📅 Мои записи")],
            [KeyboardButton(text="👤 Личный кабинет")],
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)