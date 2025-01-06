import base64
from typing import TYPE_CHECKING

import aiohttp
from discord.ext import commands

from src.sdk.llm import LLMServices

if TYPE_CHECKING:
    import discord


SUMMARY_ROMPT = """
請將總結的部分以發送者當作主要分類，並將他在這段期間內發送的內容總結。
例如:

Wei:
- 他表示了對於某件事情表示了擔憂
- 同時他也發送了一個相關的新聞連結佐證
- 另外，他提到了一個他認為的解決方案

Toudou:
- 他分享了一個 TikTok 影片
- 並分享了他對於那位男性的看法

在總結的最後，請將這些內容整合成一個易懂的重點總結。
"""

SUMMARY_MESSAGE = """
總結以下 {history_count} 則消息：
{chat_history_string}
"""

EXPLANATION_PROMPT = """
用戶看不懂該對話，請嘗試解釋該對話的內容。
如果用戶沒有說話 只傳送圖片，請解釋圖片的內容。
"""


class MessageFetcher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices(system_prompt=SUMMARY_ROMPT)
        self.describe_services = LLMServices(system_prompt=EXPLANATION_PROMPT)

    @commands.command()
    async def sum(self, ctx: commands.Context, *, prompt: str) -> None:
        """總結當前頻道前 N 則訊息，或若指定用戶則總結該用戶的 N 則訊息"""
        # 尝试解析輸入
        args = prompt.strip().split()

        history_count = 20
        target_user = None

        # 第一個參數可能是數字
        if args:
            try:
                # 嘗試將第一個 token 轉為數字
                history_count = int(args[0])
                # 如果後面還有參數，可能是用戶 mention
                if len(args) > 1:
                    # 剩餘的內容可能是用戶 mention，如 <@!1234567890>
                    # 我們試著從該文字中取得 mentioned_users
                    mentions = ctx.message.mentions
                    if mentions:
                        target_user = mentions[0]
                    else:
                        # 如果沒有mentions，那就維持原狀，不處理
                        pass
            except ValueError:
                # 第一個參數不是數字，則依舊使用20並提醒
                await ctx.send("你輸入的不是數字，將自動總結最近 20 則消息。")
                # 嘗試抓mentions
                mentions = ctx.message.mentions
                if mentions:
                    target_user = mentions[0]
        else:
            # 沒有提供任何參數
            pass

        try:
            channel = ctx.channel  # 獲取當前頻道

            messages: list[discord.Message] = []

            if target_user is not None:
                # 如果有指定用戶，需要從歷史訊息中尋找該用戶的訊息，直到湊滿 history_count
                async for message in channel.history(limit=None):
                    if (
                        message.author.id == target_user.id
                        and not message.author.bot
                        and not message.content.startswith("!sum")
                    ):
                        messages.append(message)
                        if len(messages) == history_count:
                            break
            else:
                # 沒有指定用戶，直接取得最近的 history_count 則訊息
                async for message in channel.history(limit=history_count):
                    if message.author.bot:
                        continue
                    if message.content.startswith("!sum"):
                        continue
                    messages.append(message)

            if not messages:
                if target_user is not None:
                    await ctx.send(
                        f"此頻道中沒有 {target_user.mention} 的訊息，或不足以取得 {history_count} 則。"
                    )
                else:
                    await ctx.send("此頻道沒有任何消息。")
                return

            # 總結消息內容
            chat_history = []
            embed_list = []
            image_urls = []
            for message in messages:
                content = message.content
                if message.embeds:
                    embed_list = [
                        embed.description for embed in message.embeds if embed.description
                    ]
                    content = "嵌入內容: " + ", ".join(embed_list)
                elif message.attachments:
                    image_urls = [attachment.url for attachment in message.attachments]
                    content = "附件: " + ", ".join(image_urls)
                chat_history.append(f"{message.author.name}: {content}")

            # 反轉消息順序（確保顯示由舊到新）
            chat_history.reverse()

            chat_history_string = "\n".join(chat_history)
            prompt = SUMMARY_MESSAGE.format(
                history_count=history_count, chat_history_string=chat_history_string
            )

            attachments = [*image_urls, *embed_list]

            summary = await self.llm_services.get_oai_reply(prompt=prompt, image_urls=attachments)
            summary = summary.choices[0].message.content

            await ctx.send(summary)
        except Exception as e:
            await ctx.send(f"發生錯誤：{e}")

    @commands.command()
    async def wtf(self, ctx: commands.Context) -> None:
        """解釋回復的消息"""
        try:
            if not ctx.message.reference:
                await ctx.send("請回復某條消息以使用此指令。")
                return

            # 獲取被回復的消息
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            # 處理消息內容
            content = replied_message.content
            image_urls = []
            base64_images = []
            if replied_message.attachments:
                attach_list = [attachment.url for attachment in replied_message.attachments]
                image_urls.extend(attach_list)
            if replied_message.embeds:
                content = "嵌入內容: " + ", ".join(
                    embed.description for embed in replied_message.embeds if embed.description
                )
            if replied_message.stickers:
                async with aiohttp.ClientSession() as session:
                    for sticker in replied_message.stickers:
                        async with session.get(sticker.url) as response:
                            if response.status == 200:
                                sticker_data = await response.read()
                                base64_image = base64.b64encode(sticker_data).decode("utf-8")
                                base64_images.append(f"data:image/png;base64,{base64_image}")

            all_images = [*image_urls, *base64_images]

            # 傳送內容給 LLM
            prompt = f"{EXPLANATION_PROMPT}\n{content}"
            explanation = await self.describe_services.get_oai_reply(
                prompt=prompt, image_urls=all_images
            )
            explanation = explanation.choices[0].message.content

            await ctx.send(explanation)
        except Exception as e:
            await ctx.send(f"發生錯誤：{e}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageFetcher(bot))
