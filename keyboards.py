from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardButton
    )
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import Callable


def build_reply_kb(items: list, placeholder: str='Ввод...', kb_size: int=1):
    keyboard = ReplyKeyboardBuilder()
    
    for item in items:
        keyboard.add(KeyboardButton(text=item))
        
    return keyboard.adjust(kb_size).as_markup(
		resize_keyboard=True,
		input_field_placeholder=placeholder
	)


# Универсальный билдер инлайн клавиатуры
def build_inline_kb(
    items: list,
    kb_size: int,
    text_getter: Callable,
    callback_getter: Callable
    ):
        keyboard = InlineKeyboardBuilder()
        
        for item in items:
            keyboard.add(InlineKeyboardButton(
				text=text_getter(item),
				callback_data=callback_getter(item)
			))
            
        return keyboard.adjust(kb_size).as_markup()
