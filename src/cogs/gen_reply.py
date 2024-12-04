import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from discord import File
from ascii_magic import AsciiArt
from discord.ext import commands

from src.sdk.llm import LLMServices

llm_services = LLMServices()


class ReplyGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def xai(self, ctx: commands.Context, *, prompt: str = "") -> None:
        # 檢查是否有附件
        if ctx.message.attachments:
            # 取得附件的 URL（假設只有一個圖片）
            image_url = ctx.message.attachments[0].url
            # await ctx.send(f"收到圖片: {image_url}")
            # 在這裡你可以進一步處理圖片 URL，例如傳遞給 llm_services 或其他服務
            response = await llm_services.get_xai_reply(prompt=prompt, image=image_url)
        else:
            # 如果沒有圖片附件，僅處理文字提示
            response = await llm_services.get_xai_reply(prompt=prompt)

        # 回應處理結果
        await ctx.send(f"{ctx.author.mention} {response.choices[0].message.content}")

    @commands.command()
    async def oai(self, ctx: commands.Context, *, prompt: str) -> None:
        if ctx.message.attachments:
            # 取得附件的 URL（假設只有一個圖片）
            image_url = ctx.message.attachments[0].url
            # await ctx.send(f"收到圖片，URL 為: {image_url}")
            # 在這裡你可以進一步處理圖片 URL，例如傳遞給 llm_services 或其他服務
            response = await llm_services.get_oai_reply(prompt=prompt, image=image_url)
        else:
            # 如果沒有圖片附件，僅處理文字提示
            response = await llm_services.get_oai_reply(prompt=prompt)

        await ctx.send(f"{ctx.author.mention} {response.choices[0].message.content}")

    @commands.command()
    async def gai(self, ctx: commands.Context, *, prompt: str) -> None:
        if ctx.message.attachments:
            # 取得附件的 URL（假設只有一個圖片）
            image_url = ctx.message.attachments[0].url
            # await ctx.send(f"收到圖片，URL 為: {image_url}")
            # 在這裡你可以進一步處理圖片 URL，例如傳遞給 llm_services 或其他服務
            response = await llm_services.get_gai_reply(prompt=prompt, image=image_url)
        else:
            # 如果沒有圖片附件，僅處理文字提示
            response = await llm_services.get_gai_reply(prompt=prompt)
        await ctx.send(f"{ctx.author.mention} {response.choices[0].message.content}")

    @commands.command()
    async def ascii(self, ctx: commands.Context) -> None:
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            # generate random filename using attachment.url
            temp_filename = hashlib.sha256(attachment.url.encode()).hexdigest()[:10]
            temp_filename_path = Path(f"./{temp_filename}.jpg")
            await attachment.save(temp_filename_path.as_posix())
            ascii_art = AsciiArt.from_image(temp_filename_path.as_posix())
            ascii_response = ascii_art.to_ascii()
            temp_filename_path.unlink()

            lines = ascii_response.splitlines()
            font = ImageFont.truetype(
                font="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size=10
            )
            max_line_width = max(len(line) for line in lines)
            image_width = max_line_width * 10
            image_height = len(lines) * 10
            image = Image.new("RGB", (image_width, image_height), color="white")
            draw = ImageDraw.Draw(image)
            for i, line in enumerate(lines):
                draw.text((0, i * 10), line, fill="black", font=font)
            output_file_path = f"./{temp_filename}_ascii.png"
            image.save(output_file_path)
            await ctx.send(f"{ctx.author.mention}", file=File(output_file_path))
            Path(output_file_path).unlink()


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReplyGeneratorCogs(bot))
