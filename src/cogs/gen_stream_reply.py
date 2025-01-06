import asyncio

from discord.ext import commands

from src.sdk.llm import LLMServices

llm_services = LLMServices()


class StreamReplyGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def oais(self, ctx: commands.Context, *, prompt: str) -> None:
        msg = await ctx.send("生成中...")  # 初始化訊息
        accumulated_text = f"{ctx.author.mention}\n"  # 用於存儲累計的生成內容，初始包括用戶標記
        buffer = ""  # 緩衝區，用於累積小段文字
        update_interval = 1

        async for res in llm_services.get_oai_reply_stream(prompt=prompt):
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
    await bot.add_cog(StreamReplyGeneratorCogs(bot))
