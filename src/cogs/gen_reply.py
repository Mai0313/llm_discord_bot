import base64

import aiohttp
import discord
from discord import Message, app_commands
import logfire
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

    @app_commands.command(
        name="oai",
        description="This command will generate a reply based on the prompt given.",
        nsfw=False,
    )
    async def oai(self, interaction: discord.Interaction, *, prompt: str) -> None:
        try:
            attachments = await self._get_attachment_list(message=interaction.message)
            response = await self.llm_services.get_oai_reply(prompt=prompt, image_urls=attachments)
            await interaction.response.send_message(
                f"{interaction.message.author.mention} {response.choices[0].message.content}"
            )
        except Exception as e:
            await interaction.response.send_message(content=f"處理訊息發生錯誤: {e!s}")

    @app_commands.command(
        name="oais",
        description="This command will generate a reply based on the prompt given and show the progress.",
        nsfw=False,
    )
    async def oais(self, interaction: discord.Interaction, *, prompt: str) -> None:
        attachments = await self._get_attachment_list(message=interaction.message)
        await interaction.response.send_message(content="生成中...")

        accumulated_text = f"{interaction.user.mention}\n"

        try:
            async for res in self.llm_services.get_oai_reply_stream(
                prompt=prompt, image_urls=attachments
            ):
                if hasattr(res, "choices") and len(res.choices) > 0:
                    delta_content = res.choices[0].delta.content.strip()
                    if delta_content:  # 確保生成內容非空
                        accumulated_text += delta_content
                        await interaction.response.edit_message(content=accumulated_text)

        except Exception as e:
            await interaction.response.edit_message(
                content=f"{interaction.user.mention} 無有效回應，請嘗試其他提示。"
            )
            logfire.error(f"Error in oais: {e}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReplyGeneratorCogs(bot))
