from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


menu = ReplyKeyboardMarkup(
	keyboard=[
		[KeyboardButton(text='/pdf')]
	],
	resize_keyboard=True,
	input_field_placeholder='Выбери тип файла'
)
