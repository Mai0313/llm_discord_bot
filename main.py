from pathlib import Path

import discord
import logfire
from discord.ext import commands
from src.sdk.llm import LLMServices
from src.types.config import Config

logfire.configure()

config = Config()
llm_services = LLMServices()

# 啟用所有 Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    app_info = await bot.application_info()
    invite_url = (
        f"https://discord.com/oauth2/authorize?client_id={app_info.id}&permissions=8&scope=bot"
    )
    logfire.info("Bot Started", bot_name=bot.user.name, bot_id=bot.user.id)
    logfire.info(f"Invite Link: {invite_url}")
    logfire.info("Loading Cogs...")
    cog_path = Path("./src/cogs")
    cog_files = [f.stem for f in cog_path.glob("*.py") if not f.stem.startswith("__")]
    for cog_file in cog_files:
        filename = f"src.cogs.{cog_file}"
        logfire.info("Loading Cogs", filename=filename)
        await bot.load_extension(filename)


if __name__ == "__main__":
    bot.run(token=config.discord_bot_token, log_handler=logfire.LogfireLoggingHandler())
