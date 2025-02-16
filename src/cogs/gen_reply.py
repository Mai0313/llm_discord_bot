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
        description="Generate a reply based on the given prompt.",
        name_localizations={Locale.zh_TW: "生成文字", Locale.ja: "テキストを生成"},
        description_localizations={
            Locale.zh_TW: "根據提供的提示詞生成回應。",
            Locale.ja: "指定されたプロンプトに基づいて応答を生成します。",
        },
        dm_permission=True,
        nsfw=False,
    )
    async def oai(
        self,
        interaction: Interaction,
        prompt: str = SlashOption(
            description="Enter your prompt.",
            description_localizations={
                Locale.zh_TW: "輸入提示詞。",
                Locale.ja: "プロンプトを入力してください。",
            },
        ),
        image: nextcord.Attachment = SlashOption(  # noqa: B008
            description="(Optional) Upload an image.",
            description_localizations={
                Locale.zh_TW: "（可選）上傳一張圖片。",
                Locale.ja: "（オプション）画像をアップロードしてください。",
            },
            required=False,
        ),
    ) -> None:
        try:
            # 先嘗試從 interaction.message 取得附件（如果有的話）
            attachments = await self._get_attachment_list(interaction.message)
            # 再檢查參數是否有提供圖片，並加入附件列表
            if image:
                attachments.append(image.url)
            response = await self.llm_services.get_oai_reply(prompt=prompt, image_urls=attachments)
            await interaction.response.send_message(
                f"{interaction.user.mention} {response.choices[0].message.content}"
            )
        except Exception as e:
            await interaction.response.send_message(content=f"處理訊息時發生錯誤: {e!s}")

    @nextcord.slash_command(
        name="oais",
        description="Generate a reply based on the given prompt and show progress.",
        name_localizations={Locale.zh_TW: "生成文字並顯示進度", Locale.ja: "テキストを生成"},
        description_localizations={
            Locale.zh_TW: "此指令將根據提供的提示生成回覆並顯示進度。",
            Locale.ja: "指定されたプロンプトに基づいて応答を生成し、進行状況を表示します。",
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
                Locale.zh_TW: "輸入提示詞",
                Locale.ja: "プロンプトを入力してください",
            },
        ),
        image: nextcord.Attachment = SlashOption(  # noqa: B008
            description="(Optional) Upload an image.",
            description_localizations={
                Locale.zh_TW: "（可選）上傳一張圖片。",
                Locale.ja: "（オプション）画像をアップロードしてください。",
            },
            required=False,
        ),
    ) -> None:
        # 取得 message 附件並合併參數提供的圖片
        attachments = await self._get_attachment_list(interaction.message)
        if image:
            attachments.append(image.url)
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
                    accumulated_text += res.choices[0].delta.content
                    await message.edit(content=accumulated_text)

        except Exception as e:
            await message.edit(
                content=f"{interaction.user.mention} 無法生成有效回應，請嘗試其他提示詞。"
            )
            logfire.error(f"Error in oais: {e}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    bot.add_cog(ReplyGeneratorCogs(bot), override=True)
