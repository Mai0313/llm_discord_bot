import base64

import aiohttp
import logfire
import nextcord
from nextcord import Locale, Interaction, SlashOption
from nextcord.ext import commands

from src.sdk.llm import LLMServices


class ReplyGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices()

    async def _get_attachment_list(self, message: nextcord.Message) -> list[str]:
        image_urls, embed_list, sticker_list = [], [], []
        if not message:
            return []
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

    @nextcord.slash_command(
        name="oai",
        description="This command will generate a reply based on the prompt given.",
        name_localizations={Locale.zh_TW: "文字生成", Locale.ja: "テキスト生成"},
        description_localizations={
            Locale.zh_TW: "此指令將根據提供的提示生成回覆。",
            Locale.ja: "このコマンドは、指定されたプロンプトに基づいて応答を生成します。",
        },
        dm_permission=True,
        nsfw=False,
    )
    async def oai(
        self,
        interaction: Interaction,
        prompt: str = SlashOption(
            description="Enter your prompt",
            description_localizations={
                Locale.zh_TW: "輸入你的提示詞",
                Locale.ja: "プロンプトを入力してください",
            },
        ),
    ) -> None:
        try:
            attachments = await self._get_attachment_list(interaction.message)
            response = await self.llm_services.get_oai_reply(prompt=prompt, image_urls=attachments)
            await interaction.response.send_message(
                f"{interaction.user.mention} {response.choices[0].message.content}"
            )
        except Exception as e:
            await interaction.response.send_message(content=f"處理訊息發生錯誤: {e!s}")

    @nextcord.slash_command(
        name="oais",
        description="This command will generate a reply based on the prompt given and show the progress.",
        name_localizations={Locale.zh_TW: "文字生成進度", Locale.ja: "テキスト生成進行中"},
        description_localizations={
            Locale.zh_TW: "此指令將根據提供的提示生成回覆並顯示進度。",
            Locale.ja: "このコマンドは、指定されたプロンプトに基づいて応答を生成し、進行状況を表示します。",
        },
        dm_permission=True,
        nsfw=False,
    )
    async def oais(
        self,
        interaction: Interaction,
        prompt: str = SlashOption(
            description="Enter your prompt",
            description_localizations={
                Locale.zh_TW: "輸入你的提示詞",
                Locale.ja: "プロンプトを入力してください",
            },
        ),
    ) -> None:
        attachments = await self._get_attachment_list(interaction.message)
        message = await interaction.response.send_message(content="生成中...")
        accumulated_text = f"{interaction.user.mention}\n"

        try:
            async for res in self.llm_services.get_oai_reply_stream(
                prompt=prompt, image_urls=attachments
            ):
                if (
                    hasattr(res, "choices")
                    and len(res.choices) > 0
                    and res.choices[0].delta.content
                ):
                    delta_content = res.choices[0].delta.content.strip()
                    accumulated_text += delta_content
                    await message.edit(content=accumulated_text)

        except Exception as e:
            await message.edit(content=f"{interaction.user.mention} 無有效回應，請嘗試其他提示。")
            logfire.error(f"Error in oais: {e}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    bot.add_cog(ReplyGeneratorCogs(bot), override=True)
