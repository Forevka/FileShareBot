import logging
import asyncio
import pprint
import db
import ssl
import sys
import json
from aiogram.utils.exceptions import BotBlocked
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook

pp = pprint.PrettyPrinter(indent=4)

API_TOKEN = "773331564:AAEcLausu3kFnA8oSlohOJBFvoy67Un4BDM"
# webhook settings
WEBHOOK_HOST = '194.67.205.185'
WEBHOOK_PATH = f'/{API_TOKEN}/'
WEBHOOK_URL = f"https://{WEBHOOK_HOST}:443"

# webserver settings
WEBAPP_HOST = '0.0.0.0'  # or ip
WEBAPP_PORT = 443

# Configure logging
logging.basicConfig(filename="log.log", level=logging.WARNING)

# Initialize bot and dispatcher
loop = asyncio.get_event_loop()

#print(dir(types.ContentType))

bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)

@dp.message_handler(commands=['find'])
async def send_add(message: types.Message):
    file_name = message.text.split(" ", 1)[-1]
    #print(file_name)
    if len(file_name)>=3:
        files = await loop.create_task(db.find_file_by_name(file_name));
        if len(files)>0:
            files_kb = InlineKeyboardMarkup()
            for i in files:
                files_kb.add(InlineKeyboardButton(i['file_name'], callback_data=i['file_id']))
            await message.reply("Вот что нашел по твоему запросу", reply_markup=files_kb)
        else:
            await message.reply("Ничего не нашел :(")
    else:
        await message.reply("Минимум 3 буквы для поиска")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def send_add(message: types.Message):
    #print(message)
    
    await loop.create_task(db.insert_file_id(message.document.file_name, message.document.file_id, message.from_user.id))
    await message.reply("Окей, сохранил твой файл к себе в базу данных!")

@dp.callback_query_handler()
async def process_callback(callback_query: types.CallbackQuery):
    file = await db.find_file_by_id(callback_query.data);
    user_id = json.loads(str(callback_query.message.reply_to_message))['from']['id'];
    owner = True if file['owner_id'] == user_id else False;
    
    try:
        await bot.send_document(user_id, callback_query.data, parse_mode = "HTML",
                                caption='<b>Файл:</b> '+file['file_name']+"\n<b>Дата загрузки:</b> "+datetime.strftime(file['create_date'], "%Y.%m.%d %H:%M:%S"))
        await bot.answer_callback_query(callback_query.id, text = "Отправил файл тебе в лс")
    except BotBlocked:
        await bot.answer_callback_query(callback_query.id, text = "Не могу отправить тебе файл, напиши мне для начала чтоб я мог отправлять тебе файлы", show_alert = True)
        

#@dp.message_handler()
#async def echo(message: types.Message):
#    await bot.send_message(message.chat.id, message.text)
    
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL+WEBHOOK_PATH, certificate=open("webhook_cert.pem", 'rb'))
    # insert code here to run it after startUU

async def on_shutdown(dp):
    # insert code here to run it before shutdown
    pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    #########
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #context.load_cert_chain("webhook_cert.pem", "webhook_pkey.pem")
    #start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown,
    #              skip_updates=True, host=WEBAPP_HOST, port=443, ssl_context=context)

