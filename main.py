import logging
import json
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardMarkup
from fastapi import FastAPI
from typing import Optional
import asyncio
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
import random
import pandas as pd
import numpy as np
import os
loop = asyncio.get_event_loop()
# Get the value of an environment variable
app = FastAPI()

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO,
                    format=LOG_FORMAT,
                    handlers=[
                        logging.StreamHandler(),  # Log to console
                        logging.FileHandler("bot.log", encoding='utf-8')  # Log to a file named "bot.log"
                    ])

logger = logging.getLogger(__name__)

with open('config.json', 'r') as confile:
    config = json.load(confile)

# config['telegram'] = os.environ.get("TELEGRAM")
# Initialize bot and dispatcher
bot = Bot(token=config['telegram'])
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
teams=0
# # Handler for commands


# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

MESSAGES = {
    'en' : {
        'start' : "Hello! This bot can create a competition plan. Please choose your language.",
        'welcome' : "This bot can create a competition plan for X teams, Y available tasks, and Z number of required tasks. The result will be in the form of a table. How many teams are participating?",
        'enter_tasks' : "How many available tasks do you have?",
        'enter_min_tasks' : "What is the number of required tasks each team should go through?",
        'invalid_input' : "Please enter numbers",
        'not_enough_tasks' : "It is not enough available tasks to make a schedule",
        'results':
"""Stages available: {tasks}\n
Teams participating: {teams}\n
Number of mandatory stages: {min_task}\n
Schedule:\n
{schedule}\n 
Write developer of this bot {link}""",

    },
    'ru': {
        'start': "Привет! Этот бот может создать план соревнований. Пожалуйста, выберите ваш язык.",
        'welcome': "Этот бот может создавать план соревнований для X команд, Y доступных заданий, и Z количество необходимых заданий. Результат будет в виде таблицы. Сколько команд участвуют?",
        'enter_tasks': "Сколько заданий доступно для соревнований?",
        'enter_min_tasks': "Сколько заданий необходимо пройти каждой команде?",
        'invalid_input': "введите цифры",
        'not_enough_tasks' : "Не хватает заданий, чтобы построить расписание",
        'results' :
"""Этапов доступно: {tasks}\n
Участвует команд:{teams}\n
Количество обязательных этапов: {min_task}\n
Расписание:\n
{schedule}\n
Написать разарботчику : {link}""",
    }
    # You can add more languages to this dictionary
}


class LogMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        user = message.from_user
        user_details = f"User ID: {user.id}, Username: {user.username}, Full Name: {user.full_name}"
        message_content = message.text or message.caption or "<NO_TEXT>"
        logger.info(f"Received Message from {user_details}. Message Content: {message_content}")


dp.middleware.setup(LogMiddleware())

def team_selector(teams ,tasks, min_tasks):
    schedule = np.zeros((int(teams), int(min_tasks)))
    tasks_array = np.arange(1, int(tasks) + 1)
    for team_ind, team in enumerate(range(int(teams)))  :
        if team_ind==0:
            try:
                schedule[0,:]=select_for_first(tasks, min_tasks)
            except:
                return "not_enough_tasks"

        else:
            for task_ind in range(int(min_tasks)):
                if team_ind == 0 :
                    availible_tasks = set(set(tasks_array) - set(schedule[0 :team_ind, task_ind]))
                else:
                    availible_tasks = set(set(tasks_array)-set(schedule[0:team_ind, task_ind])) - set(schedule[team_ind, 0:task_ind])
                try:
                    schedule[team_ind,task_ind]=random.choice(list(availible_tasks))
                except:
                    return "not_enough_tasks"
    return schedule
def select_for_first(tasks, min_tasks):
    tasks_array = np.arange(1, int(tasks)+1)
    r_ch = random.sample(list(tasks_array), int(min_tasks))  # Converting to list since sample expects a sequence
    return r_ch

class Form(StatesGroup):
    teams = State()
    tasks = State()
    min_task = State()
    lang = State()

async def send_message(user_id, key, lang='en', **kwargs):
    """Helper function to send messages in user's language"""
    await bot.send_message(user_id, MESSAGES[lang][key].format(**kwargs))

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Send language selection menu
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("English", callback_data="lang_en"))
    keyboard.add(InlineKeyboardButton("Русский", callback_data="lang_ru"))
    await bot.send_message(message.chat.id, MESSAGES['en']['start'], reply_markup=keyboard)


@dp.callback_query_handler(lambda c : c.data in ["lang_en", "lang_ru"])
async def set_language (callback_query: types.CallbackQuery, state: FSMContext) :
    lang = callback_query.data.split("_")[1]
    await state.update_data(lang=lang)
    await bot.answer_callback_query(callback_query.id, "Language set!")
    await Form.teams.set()
    await send_message(callback_query.from_user.id, 'welcome', lang)


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(lambda message: message.text.lower() == 'cancel', state='*')
async def cancel_handler(message: types.Message, state: FSMContext, raw_state: Optional[str] = None):

    if raw_state is None:
        return
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Canceled.', reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(lambda message: not message.text.isdigit(), state=(Form.teams, Form.tasks, Form.min_task))
async def failed_process(message: types.Message, state: FSMContext):
    user = message.from_user
    logger.info(f"Invalid input received from User ID: {user.id}, Username: {user.username}, Full Name: {user.full_name}")
    data = await state.get_data()
    await send_message(message.from_user.id, 'invalid_input', data['lang'])

@dp.message_handler(lambda message: message.text.isdigit(), state=Form.teams)
async def process_teams(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['teams'] = message.text
    user_id = message.from_user.id
    await Form.next()
    await send_message(user_id, 'enter_tasks', data['lang'])


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.tasks)
async def process_teams(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['tasks'] = message.text
    user_id = message.from_user.id
    await Form.next()
    await send_message(user_id, 'enter_min_tasks', data['lang'])



@dp.message_handler(lambda message : message.text.isdigit(), state=Form.min_task)
async def process_teams (message: types.Message, state: FSMContext) :
    async with state.proxy() as data :
        data['min_task'] = message.text

        for i in range(10):
            schedule = team_selector(data['teams'], data['tasks'] , data['min_task'])
            if type(schedule)!=str:
                break
            else:
                schedule=MESSAGES[data['lang']][schedule]

        if type(schedule)!=str:
            # Convert numpy array to Pandas DataFrame
            df = pd.DataFrame(schedule)

            # Save DataFrame as an Excel file
            filename = "schedule.xlsx"
            df.to_excel(filename, index=False, header=False)  # Disabling the index and header for this example
            # Send the Excel file via the bot
            with open(filename, "rb") as file :
                await bot.send_document(message.chat.id, file, caption="Here's your schedule!")
            os.remove(filename)


        results_msg = MESSAGES[data['lang']]['results'].format(
            tasks=data['tasks'],
            teams=data['teams'],
            min_task=data['min_task'],
            schedule=schedule,
            link=config['link']
        )

        # And send message
        await bot.send_message(
            message.chat.id,
            results_msg,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Restart", callback_data="restart")
            )
        )
        # Finish conversation
        data.state = None


# Handle the callback query
@dp.callback_query_handler(lambda c : c.data == 'restart')
async def process_callback (callback_query: types.CallbackQuery) :
    await bot.answer_callback_query(callback_query.id)
    await cmd_start(callback_query.message)


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, skip_updates=True)

