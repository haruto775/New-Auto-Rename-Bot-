import aiohttp
import asyncio
import warnings
import pytz
from datetime import datetime, timedelta
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import pyrogram.utils
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

pyrogram.utils.MIN_CHANNEL_ID = -1002258136705

# Setting SUPPORT_CHAT directly here
SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "@Bots_Nations_Support")

class Bot(Client):

    def __init__(self):
        super().__init__(
            name="codeflixbots",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )
        # Initialize the bot's start time for uptime calculation
        self.start_time = time.time()

    async def ping_service(self):
        """Send a ping request to the service to keep it awake."""
        while True:
            try:
                # Send a request to the web server to keep it alive
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:5000") as response:
                        if response.status == 200:
                            print("Ping successful")
                        else:
                            print("Ping failed with status:", response.status)
            except Exception as e:
                print("Error while pinging:", e)

            # Wait for 5 minutes before sending the next ping
            await asyncio.sleep(300)  # 300 seconds = 5 minutes

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username  
        self.uptime = Config.BOT_UPTIME  
        
        if Config.WEBHOOK:
            app = web.AppRunner(await web_server())
            await app.setup()       
            await web.TCPSite(app, "0.0.0.0", 5000).start()
            print("Web server started on port 5000")
            
        print(f"{me.first_name} Is Started.....✨️")

        # Calculate uptime using timedelta
        uptime_seconds = int(time.time() - self.start_time)
        uptime_string = str(timedelta(seconds=uptime_seconds))

        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time_str = curr.strftime('%I:%M:%S %p')
                
                # Send the message with the photo
                await self.send_photo(
                    chat_id=Config.LOG_CHANNEL,
                    photo=Config.START_PIC,
                    caption=( 
                        "**🤖 Bot Restarted Successfully!**\n\n"
                        f"**📊 Uptime:** `{uptime_string}`\n"
                        f"**📅 Date:** {date}\n"
                        f"**⏰ Time:** {time_str}\n\n"
                        "**✅ All systems operational**"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton("📢 Updates", url="https://t.me/Bots_Nation")
                        ]]
                    )
                )

            except Exception as e:
                print(f"Failed to send startup message: {e}")

        # Start the ping service in the background
        asyncio.create_task(self.ping_service())

    async def stop(self):
        await super().stop()
        print("Bot stopped!")

if __name__ == "__main__":
    Bot().run()
