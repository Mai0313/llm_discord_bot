from typing import TYPE_CHECKING

from discord.ext import commands

from src.sdk.llm import LLMServices

if TYPE_CHECKING:
    import discord


SUMMARY_ROMPT = """
總結以下 {history_count} 則消息：
{chat_history_string}
請確保這些訊息包含 發送者 與 重點內容和最後的總結。
如果遇到某些問題是回答其他人的問題，請將他總結在一起。
"""


class MessageFetcher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices()

    @commands.command()
    async def sum(self, ctx: commands.Context, *, prompt: str) -> None:
        """總結當前頻道前 20 則訊息"""
        try:
            history_count = int(prompt)
        except Exception:
            history_count = 20
        try:
            channel = ctx.channel  # 獲取當前頻道

            # 獲取最近的 20 則消息
            messages: list[discord.Message] = []
            async for message in channel.history(limit=history_count):
                messages.append(message)

            if not messages:
                await ctx.send("此頻道沒有任何消息。")
                return

            # 總結消息內容
            chat_history = []
            for message in messages:
                content = message.content
                if message.content.startswith("!sum"):
                    continue
                if message.author.bot:
                    continue
                if message.embeds:
                    content = "嵌入內容: " + ", ".join(
                        embed.description for embed in message.embeds if embed.description
                    )
                elif message.attachments:
                    content = "附件: " + ", ".join(
                        attachment.url for attachment in message.attachments
                    )
                chat_history.append(f"{message.author.name}: {content}")

            chat_history_string = "\n".join(chat_history)
            prompt = SUMMARY_ROMPT.format(
                history_count=history_count, chat_history_string=chat_history_string
            )

            summary = await self.llm_services.get_xai_reply(prompt=prompt)
            summary = summary.choices[0].message.content

            await ctx.send(summary)
        except Exception as e:
            await ctx.send(f"發生錯誤：{e}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageFetcher(bot))
