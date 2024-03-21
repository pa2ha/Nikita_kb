import asyncio
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from aiogram import Bot, Dispatcher, types
from dotenv import find_dotenv, load_dotenv

from database.engine import create_db, drop_db, session_maker
from handlers.MyHandler import my_first_handler
from middlewares.db import DataBaseSession

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

dp.include_router(my_first_handler) 


async def on_startup(bot):

    # await drop_db()

    await create_db()


async def on_shutdown(bot):
    print('бот лег')



async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    # await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())