from pathlib import Path

import discord
import logfire
from discord.ext import commands

logfire.configure()

# 啟用所有 Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
discord_invite_url = (
    "https://discord.com/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot"
)


@bot.event
async def on_ready() -> None:
    app_info = await bot.application_info()
    invite_url = discord_invite_url.format(client_id=app_info)

    cog_path = Path("./src/cogs")
    cog_files = [f.stem for f in cog_path.glob("*.py") if not f.stem.startswith("__")]
    for cog_file in cog_files:
        filename = f"src.cogs.{cog_file}"
        await bot.load_extension(filename)
        logfire.info("Cogs Loaded", filename=filename)

    logfire.info("Bot Started", bot_name=bot.user.name, bot_id=bot.user.id)
    logfire.info(f"Invite Link: {invite_url}")


if __name__ == "__main__":
    from src.types.config import Config

    config = Config()
    bot.run(token=config.discord_bot_token, log_handler=logfire.LogfireLoggingHandler())
