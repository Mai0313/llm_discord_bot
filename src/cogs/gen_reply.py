import base64
import asyncio

import aiohttp
from discord import Message
from discord.ext import commands

from src.sdk.llm import LLMServices


class ReplyGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices()

    async def _get_attachment_list(self, message: Message) -> list[str]:
        image_urls = []
        embed_list = []
        sticker_list = []
        if message.attachments:
            image_urls = [attachment.url for attachment in message.attachments]
        if message.embeds:
            embed_list = [embed.description for embed in message.embeds if embed.description]
        if message.stickers:
            async with aiohttp.ClientSession() as session:
                for sticker in message.stickers:
                    async with session.get(sticker.url) as response:
                        if response.status == 200:
                            sticker_data = await response.read()
                            base64_image = base64.b64encode(sticker_data).decode("utf-8")
                            sticker_list.append(f"data:image/png;base64,{base64_image}")
        attachments = [*image_urls, *embed_list, *sticker_list]
        return attachments

    @commands.command()
    async def graph(self, ctx: commands.Context, *, prompt: str) -> None:
        msg = await ctx.send("正在生成圖片...")
        try:
            response = await self.llm_services.get_dalle_image(prompt=prompt)
            await msg.edit(content=f"{ctx.author.mention}\n{response.data[0].url}")
        except Exception as e:
            await msg.edit(content=f"生成圖片時發生錯誤: {str(e)}")

    @commands.command()
    async def oai(self, ctx: commands.Context, *, prompt: str) -> None:
        attachments = await self._get_attachment_list(message=ctx.message)
        response = await self.llm_services.get_oai_reply(prompt=prompt, image_urls=attachments)
        await ctx.send(f"{ctx.author.mention} {response.choices[0].message.content}")

    @commands.command()
    async def wtf(self, ctx: commands.Context) -> None:
        """解釋回復的消息"""
        try:
            if not ctx.message.reference:
                await ctx.send("請回復某條消息以使用此指令。")
                return

            # 獲取被回復的消息
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            attachments = await self._get_attachment_list(message=replied_message)

            # 傳送內容給 LLM
            prompt = f"用戶看不懂該對話，請嘗試解釋該對話的內容；如果用戶沒有說話 只傳送圖片，請解釋圖片的內容。\n{replied_message.content}"
            explanation = await self.llm_services.get_oai_reply(
                prompt=prompt, image_urls=attachments
            )
            explanation = explanation.choices[0].message.content

            await ctx.send(explanation)
        except Exception as e:
            await ctx.send(f"發生錯誤：{e}")

    @commands.command()
    async def oais(self, ctx: commands.Context, *, prompt: str) -> None:
        attachments = await self._get_attachment_list(message=ctx.message)
        msg = await ctx.send("生成中...")  # 初始化訊息
        accumulated_text = f"{ctx.author.mention}\n"  # 用於存儲累計的生成內容，初始包括用戶標記
        buffer = ""  # 緩衝區，用於累積小段文字
        update_interval = 1

        async for res in self.llm_services.get_oai_reply_stream(
            prompt=prompt, image_urls=attachments
        ):
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


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReplyGeneratorCogs(bot))
