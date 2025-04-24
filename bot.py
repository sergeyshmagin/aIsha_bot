from handlers.general import bot
from handlers.transcribe import *


if __name__ == "__main__":
    import asyncio
    asyncio.run(bot.polling())
