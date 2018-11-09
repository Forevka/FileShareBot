import logging
import asyncio
import pprint
import db
import ssl
import sys
import json
from typing import Optional
from aiogram.utils.exceptions import BotBlocked
from datetime import datetime

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

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
#logging.basicConfig(filename="log.log", level=logging.WARNING)
logging.basicConfig(level=logging.INFO)
# Initialize bot and dispatcher
loop = asyncio.get_event_loop()

greet_kb = ReplyKeyboardMarkup(resize_keyboard = True)
greet_kb.add(KeyboardButton('🗄 Меню 🗄'))
greet_kb.add(KeyboardButton('❓ Как пользоваться? ❓'))
greet_kb.add(KeyboardButton('🔎 Найти файл 🔎'))

storage = MemoryStorage()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    file_name = State()  # Will be represented in storage as 'Form:name'

def extract_unique_code(text):
    return text.split()[1] if len(text.split()) > 1 else None

async def send_start_message(message):
    await message.reply("Привет, я бот который поможет сохранить твои файлы", reply_markup=greet_kb)

@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    if message.chat.type == "private":
        chat_id = message.chat.id
        file_id = extract_unique_code(message.text);
        if file_id:
            file = await db.find_file_by_id(file_id);
            if file!=None:
                await bot.send_document(chat_id, file['file_id'], parse_mode = "HTML", reply_markup=greet_kb,reply_to_message_id = message.message_id,
                                    caption='Привет! Вот твой файл\n\n<b>Файл:</b> '+file['file_name']+"\n<b>Дата загрузки:</b> "+datetime.strftime(file['create_date'], "%Y.%m.%d %H:%M:%S"))
            else:
                await message.reply("Не могу понять что за файл ты хочешь... Попробуй еще раз", reply_markup=greet_kb)
        else:
            await send_start_message(message)

@dp.message_handler(commands=['find'])
async def send_find(message: types.Message):
    file_name = message.text.split(" ", 1)[-1]
    #print(file_name)
    if file_name!="/find":
        if len(file_name)>=3:
            files = await loop.create_task(db.find_file_by_name(file_name));
            if len(files)>0:
                files_kb = InlineKeyboardMarkup()
                for n, i in enumerate(files):
                    if n<5:
                        files_kb.add(InlineKeyboardButton(i['file_name'], callback_data="file="+i['file_id']))
                if len(files)>5:
                    files_kb.add(InlineKeyboardButton("Дальше >>", callback_data="next="+file_name+"="+str(5)))
                await message.reply("Вот что нашел по твоему запросу", reply_markup=files_kb)
            else:
                await message.reply("Ничего не нашел :(")
        else:
            await message.reply("Минимум 3 буквы для поиска")
    else:
        await message.reply("Чтобы воспользоваться командой напиши /find имя_файла")

@dp.message_handler(content_types=types.ContentType.AUDIO)
async def get_music(message: types.Message):
    await message.reply("Пока что не поддерживаю музыку но скоро буду 😉")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def get_document(message: types.Message):
    #print(message)
    err = await loop.create_task(db.insert_file_id(message.document.file_name, message.document.file_id, message.from_user.id))
    if err == 1:
        await message.reply("Окей, сохранил твой файл к себе в базу данных!")
    

@dp.callback_query_handler()
async def process_callback(callback_query: types.CallbackQuery):
    print(callback_query)
    if callback_query.data.find("file")>=0:
        file = callback_query.data.split("=")[-1]
        file = await db.find_file_by_id(file);
        user_id = json.loads(str(callback_query.message.reply_to_message))['from']['id'];
        owner = True if file['owner_id'] == user_id else False;
        
        try:
            await bot.send_document(user_id, file['file_id'], parse_mode = "HTML",
                                    caption='<b>Файл:</b> '+file['file_name']+"\n<b>Дата загрузки:</b> "+datetime.strftime(file['create_date'], "%Y.%m.%d %H:%M:%S"))
            await bot.answer_callback_query(callback_query.id, text = "Отправил файл тебе в лс")
        except BotBlocked:
            await bot.answer_callback_query(callback_query.id, text = "Не могу отправить тебе файл, напиши мне для начала чтоб я мог отправлять тебе файлы", show_alert = True)
    elif callback_query.data.find("next")>=0:
        file_name = callback_query.data.split("=")[1];
        offset = callback_query.data.split("=")[2];
        
        files = await loop.create_task(db.find_file_by_name(file_name, offset = int(offset)));
        next_button = None;
        prev_button = None;
        if len(files)>0:
            files_kb = InlineKeyboardMarkup()
            for n, i in enumerate(files):
                if n<5:
                    files_kb.add(InlineKeyboardButton(i['file_name'], callback_data="file="+i['file_id']))
            if len(files)>5:
                next_button = InlineKeyboardButton("Дальше >>", callback_data="next="+file_name+"="+str(int(offset)+5))
            prev_button = InlineKeyboardButton("<< Назад", callback_data="back="+file_name+"="+str(int(offset)-5))
            if next_button!=None:
                files_kb.row(prev_button, next_button)
            else:
                files_kb.row(prev_button)
            await bot.edit_message_text(text = "Вот что нашел по твоему запросу", chat_id = callback_query.message.chat.id, message_id = callback_query.message.message_id, reply_markup=files_kb)#message.reply("Вот что нашел по твоему запросу", reply_markup=files_kb)
    elif callback_query.data.find("back")>=0:
        file_name = callback_query.data.split("=")[1];
        offset = callback_query.data.split("=")[2];
        
        files = await loop.create_task(db.find_file_by_name(file_name, offset = int(offset)));
        next_button = None;
        prev_button = None;
        if len(files)>0:
            files_kb = InlineKeyboardMarkup()
            for n, i in enumerate(files):
                if n<5:
                    files_kb.add(InlineKeyboardButton(i['file_name'], callback_data="file="+i['file_id']))
            if len(files)>5:
                next_button = InlineKeyboardButton("Дальше >>", callback_data="next="+file_name+"="+str(int(offset)+5))
            if int(offset)>0:
                prev_button = InlineKeyboardButton("<< Назад", callback_data="back="+file_name+"="+str(int(offset)-5))
            
            if prev_button!=None and next_button!=None:
                files_kb.row(prev_button, next_button)
            elif prev_button!=None:
                files_kb.row(prev_button)
            elif next_button!=None:
                files_kb.row(next_button)
            await bot.edit_message_text(text = "Вот что нашел по твоему запросу", chat_id = callback_query.message.chat.id, message_id = callback_query.message.message_id, reply_markup=files_kb)

@dp.inline_handler()
async def inline_send(inline_query: types.InlineQuery):
    if len(inline_query.query)>=3:
        files = await db.find_file_by_name(inline_query.query);
        if len(files)>0:
            result = [];
            for n, file in enumerate(files):
                item = types.InlineQueryResultDocument(id = str(n), title = file['file_name'],
                                                        document_url = file['file_id'], mime_type = "application")
                result.append(item)
            await bot.answer_inline_query(inline_query.id, results=result, cache_time=3)
        else:
            input_content = types.InputTextMessageContent("Немогу найти такого файла 🙄")
            item = types.InlineQueryResultArticle(id='1', title='Немогу найти такого файла 🙄',
                                                  input_message_content=input_content)
            await bot.answer_inline_query(inline_query.id, results=[item], cache_time=60*1)
    else:
        input_content = types.InputTextMessageContent("Введи первые 3 буквы для поиска файла")
        item = types.InlineQueryResultArticle(id='1', title='Введи первые 3 буквы для поиска файла',
                                                  input_message_content=input_content)
        await bot.answer_inline_query(inline_query.id, results=[item], cache_time=60*1)

@dp.message_handler(lambda message: message.text == '🗄 Меню 🗄')
async def send_menu(message: types.Message):
    await send_start_message(message);

@dp.message_handler(lambda message: message.text == '❓ Как пользоваться? ❓')
async def send_how_to(message: types.Message):
    await message.reply("Отправь мне файл чтобы я смог его сохранить.\n\nПоиск по всем файлам - /find имя_файла\nТакже ты можешь искать файлы просто набрав в чате мое имя @StoreMyFileBot\nИли просто нажми кнопку <b>🔎 Найти файл 🔎</b>", parse_mode = "HTML")

@dp.message_handler(lambda message: message.text == '🔎 Найти файл 🔎')
async def send_search(message: types.Message):
    await Form.file_name.set()
    await message.reply("Введи название файла или /cancel для отмены")

@dp.message_handler(state=Form.file_name)
async def process_file_name(message: types.Message, state: FSMContext):
    """
    Process file name
    """
    if message.text!="/cancel":
        files = await loop.create_task(db.find_file_by_name(message.text));
        #print(files)
        if len(files)>0:
            files_kb = InlineKeyboardMarkup()
            for n, i in enumerate(files):
                if n<5:
                    files_kb.add(InlineKeyboardButton(i['file_name'], callback_data="file="+i['file_id']))
            if len(files)>5:
                files_kb.add(InlineKeyboardButton("Дальше >>", callback_data="next="+message.text+"="+str(5)))
            await message.reply("Вот что нашел по твоему запросу", reply_markup=files_kb)
        else:
            await message.reply("Ничего не нашел :(")
        await state.finish()
    else:
        await message.reply("Отмена поиска.")
        await state.finish()

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL+WEBHOOK_PATH, certificate=open("webhook_cert.pem", 'rb'))

async def on_shutdown(dp):
    # insert code here to run it before shutdown
    pass

if __name__ == '__main__':
    executor.start_polling(dp)
    #########
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #context.load_cert_chain("webhook_cert.pem", "webhook_pkey.pem")
    #start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown,
    #              skip_updates=True, host=WEBAPP_HOST, port=443, ssl_context=context)

