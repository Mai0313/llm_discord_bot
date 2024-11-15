from io import BytesIO
import os
import asyncio
import datetime

from PIL import Image
import discord
import logfire
import requests
from discord.ext import commands
from rich.console import Console

logfire.configure()

console = Console()

# 設定你的 Hugging Face API Token
API_URL = "https://api-inference.huggingface.co/models/strangerzonehf/Flux-Animex-v2-LoRA"
API_TOKEN = "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"  # noqa: S105
headers = {"Authorization": f"Bearer {API_TOKEN}"}

intents = discord.Intents.default()
intents.messages = True  # 啟用訊息接收
intents.message_content = True  # 啟用訊息內容接收
bot = commands.Bot(command_prefix="!", intents=intents)


# 查詢 Hugging Face API 的功能
def query(payload: dict) -> bytes:
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content


# 進度條
async def update_progress(message: discord.Message, step: int, total_steps: int) -> None:
    progress = int((step / total_steps) * 100)
    progress_bar = f"進度: [{'█' * (progress // 10)}{'-' * (10 - progress // 10)}] {progress}%"
    await message.edit(content=f"圖片正在生成中...\n{progress_bar}")


def log_message_to_file(message: discord.Message, save_dir: str) -> None:
    """將訊息記錄到檔案，包含附件下載"""
    # 確保資料夾存在
    os.makedirs(save_dir, exist_ok=True)

    # 建立日誌檔案名稱
    log_file = os.path.join(save_dir, "log.txt")

    # 記錄訊息內容
    with open(log_file, "a", encoding="utf-8") as f:
        message_info = f"{message.author} ({message.author.id}) at {message.created_at}:\n"
        message_content = f"{message.content}\n"
        f.write(message_info)
        f.write(message_content)
        f.write("-" * 40 + "\n")
        console.print(message_info)
        console.print(message_content)

    # 處理附件
    for attachment in message.attachments:
        attachment_path = os.path.join(save_dir, attachment.filename)
        asyncio.run_coroutine_threadsafe(attachment.save(attachment_path), bot.loop)


@bot.event
async def on_ready() -> None:
    console.print(f"Logged in as {bot.user}")
    # 取得應用程式的 client_id 並生成邀請連結
    app_info = await bot.application_info()
    invite_url = (
        f"https://discord.com/oauth2/authorize?client_id={app_info.id}&permissions=8&scope=bot"
    )
    console.print(f"邀請連結: {invite_url}")


@bot.event
async def on_message(message: discord.Message) -> None:
    # 忽略機器人自己的訊息
    if message.author.bot:
        return

    # 生成保存路徑（依據日期）
    today = datetime.date.today().isoformat()
    save_dir = os.path.join("logs", today, str(message.channel.id))

    # 記錄訊息
    log_message_to_file(message, save_dir)

    # 繼續處理其他命令
    await bot.process_commands(message)


@bot.command()
async def gen(ctx: commands.Context, *, prompt: str) -> None:
    # 回應使用者，開始生成圖片
    msg = await ctx.send("圖片正在生成中...\n進度: [----------] 0%")
    total_steps = 5  # 模擬的進度階段數

    # 模擬進度條更新
    for i in range(1, total_steps + 1):
        await asyncio.sleep(1)  # 每秒更新一次
        await update_progress(msg, i, total_steps)

    # 請求 Hugging Face API 生成圖片
    try:
        image_bytes = query({"inputs": prompt})
        image = Image.open(BytesIO(image_bytes))

        # 將圖片存為暫時檔案並發送
        with BytesIO() as image_binary:
            image.save(image_binary, format="PNG")
            image_binary.seek(0)
            await msg.edit(content=f"圖片生成完成\nPrompt: `{prompt}`")
            await ctx.send(file=discord.File(fp=image_binary, filename="generated_image.png"))
    except Exception as e:
        await msg.edit(content=f"圖片生成失敗\n錯誤: {e!s}")


if __name__ == "__main__":
    # 啟動機器人 (記得替換為你的 Discord Bot Token)
    bot.run(
        token="MTEzNDkwNDk5NjE3ODE4MjIyNQ.GELWUx.9MJ4mY4OSo9Ty9U0WV9mwVypWIvTuTAIVyp-bs",  # noqa: S106
        log_handler=logfire.LogfireLoggingHandler(),
    )
