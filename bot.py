import logging
import asyncio
import db

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "611082772:AAGkVNzUzUENFxDb1lp_m3zepSNwiTTBpjQ"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
loop = asyncio.get_event_loop()

print(dir(types.ContentType))

bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)

'''@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")'''

@dp.message_handler(commands=['find'])
async def send_add(message: types.Message):
    file_name = message.text.split(" ", 1)[-1]
    print(file_name)
    if len(file_name)>=3:
        files = await loop.create_task(db.find_file_by_name(file_name));
        if len(files)>0:
            #inline_btn_1 = InlineKeyboardButton('Первая кнопка!', callback_data='button1')
            files_kb = InlineKeyboardMarkup()#.add(inline_btn_1)
            for i in files:
                files_kb.add(InlineKeyboardButton(i['file_name'], callback_data=i['file_id']))
            await message.reply("Вот что нашел по твоему запросу", reply_markup=files_kb)
        else:
            await message.reply("Ничего не нашел :(")
    else:
        await message.reply("Минимум 3 буквы для поиска")
    #files = await loop.create_task(db.find_file_by_name())
    #print(files)
    #await message.reply("Окей, сохранил твой файл к себе в базу данных!")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def send_add(message: types.Message):
    print(message)
    
    await loop.create_task(db.insert_file_id(message.document.file_name, message.document.file_id, message.from_user.id))
    await message.reply("Окей, сохранил твой файл к себе в базу данных!")

@dp.callback_query_handler()
async def process_callback(callback_query: types.CallbackQuery):
    print("CALLBACK !!!",callback_query)
    await bot.answer_callback_query(callback_query.id)
    #await bot.send_message(callback_query.chat.id, 'Нажата первая кнопка!')
    await bot.send_document(callback_query.message.chat.id, callback_query.data,
                            caption='Этот файл специально для тебя!')

@dp.message_handler()
async def echo(message: types.Message):
    await bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
