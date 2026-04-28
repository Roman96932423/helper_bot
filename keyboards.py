from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


menu = ReplyKeyboardMarkup(
	keyboard=[
		[KeyboardButton(text='/pdf')],
		[KeyboardButton(text='добавить')],
		[KeyboardButton(text='рецепты')]
	],
	resize_keyboard=True,
	input_field_placeholder='булдозер'
)
