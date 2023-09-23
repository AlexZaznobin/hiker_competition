import logging
import json
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

# Configure logging
logging.basicConfig(level=logging.INFO)
# config={}

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


def team_selector(teams ,tasks, min_tasks):
    schedule = np.zeros((int(teams), int(min_tasks)))
    tasks_array = np.arange(1, int(tasks) + 1)
    for team_ind, team in enumerate(range(int(teams)))  :
        if team_ind==0:
            try:
                schedule[0,:]=select_for_first(tasks, min_tasks)
            except:
                return "не хватает доступных этапов"

        else:
            for task_ind in range(int(min_tasks)):
                if team_ind == 0 :
                    availible_tasks = set(set(tasks_array) - set(schedule[0 :team_ind, task_ind]))
                else:
                    availible_tasks = set(set(tasks_array)-set(schedule[0:team_ind, task_ind])) - set(schedule[team_ind, 0:task_ind])
                try:
                    schedule[team_ind,task_ind]=random.choice(list(availible_tasks))
                except:
                    return "не хватает доступных этапов"
    return schedule
def select_for_first(tasks, min_tasks):
    tasks_array = np.arange(1, int(tasks)+1)  # arange does not include the end value, so you should add 1
    r_ch = random.sample(list(tasks_array), int(min_tasks))  # Converting to list since sample expects a sequence
    return r_ch
class Form(StatesGroup):
    teams = State()
    tasks = State()
    min_task = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.teams.set()
    await message.reply("Это бот может создавать план соревнований для "
        "X количества команд, Y количества этапов и Z количества неоходимых этапов."
        "Результат будет сформирован в виде таблицы. "
        "сколько команд участвуют?")


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

@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.teams)
async def failed_process(message: types.Message):
    return await message.reply("введите цифры")
@dp.message_handler(lambda message: message.text.isdigit(), state=Form.teams)
async def process_teams(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['teams'] = message.text
    await Form.next()
    await message.reply("Сколько возможно этапов в соревнованиях?")

@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.tasks)
async def failed_process(message: types.Message):
    return await message.reply("введите цифры")

@dp.message_handler(lambda message: message.text.isdigit(), state=Form.tasks)
async def process_teams(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['tasks'] = message.text
    await Form.next()
    await message.reply("Сколько этапов должна пройти каждая команда?")


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.min_task)
async def failed_process(message: types.Message):
    return await message.reply("введите цифры")


@dp.message_handler(lambda message : message.text.isdigit(), state=Form.min_task)
async def process_teams (message: types.Message, state: FSMContext) :
    async with state.proxy() as data :
        data['min_task'] = message.text

        for i in range(10):
            schedule = team_selector(data['teams'], data['tasks'] , data['min_task'])
            if type(schedule)!=str:
                break

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

        # And send message
        await bot.send_message(message.chat.id, md.text(
            md.text('Этапов доступно:', data['tasks']),
            md.text('Участвует команд:', data['teams']),
            md.text('Количесnво обязательных этапов:', data['min_task']),
            md.text('расписание: \n', schedule),
            sep='\n'),
            reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Restart", callback_data="restart"))
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

