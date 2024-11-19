import asyncio
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


@bot.command()
async def xais(ctx: commands.Context, *, prompt: str) -> None:
    msg = await ctx.send("生成中...")  # 初始化訊息
    accumulated_text = f"{ctx.author.mention}\n"  # 用於存儲累計的生成內容，初始包括用戶標記
    buffer = ""  # 緩衝區，用於累積小段文字
    update_interval = 5

    async for res in llm_services.get_xai_reply_stream(prompt=prompt):
        if hasattr(res, "choices") and len(res.choices) > 0:
            delta_content = res.choices[0].delta.content.strip()
            if delta_content:  # 確保生成內容非空
                buffer += delta_content

        if buffer:  # 若緩衝區有內容，則更新訊息
            accumulated_text += buffer
            await msg.edit(content=accumulated_text)  # 更新訊息
            buffer = ""  # 清空緩衝區
            await asyncio.sleep(update_interval)  # 等待指定間隔

    # 確保最終訊息完整
    if buffer:
        accumulated_text += buffer
    if accumulated_text.strip():
        await msg.edit(content=accumulated_text)
    else:
        await msg.edit(content=f"{ctx.author.mention} 無有效回應，請嘗試其他提示。")


if __name__ == "__main__":
    bot.run(token=config.discord_bot_token, log_handler=logfire.LogfireLoggingHandler())
