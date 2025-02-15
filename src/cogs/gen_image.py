import nextcord
from nextcord import Locale, Interaction, SlashOption
from nextcord.ext import commands

from src.sdk.llm import LLMServices
from src.types.config import Config


class ImageGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()
        self.llm_services = LLMServices()

    @nextcord.slash_command(
        name="graph",
        description="Generate an image based on the given prompt.",
        name_localizations={Locale.zh_TW: "生成圖片", Locale.ja: "画像を生成"},
        description_localizations={
            Locale.zh_TW: "根據提供的提示詞生成圖片。",
            Locale.ja: "指定されたプロンプトに基づいて画像を生成します。",
        },
        dm_permission=True,
        nsfw=False,
    )
    async def graph(
        self,
        interaction: Interaction,
        prompt: str = SlashOption(
            description="Enter your prompt.",
            description_localizations={
                Locale.zh_TW: "輸入提示詞。",
                Locale.ja: "プロンプトを入力してください。",
            },
        ),
    ) -> None:
        message = await interaction.response.send_message(content="圖片生成中...")

        try:
            response = await self.llm_services.get_dalle_image(prompt=prompt)
            await message.edit(content=f"{interaction.user.mention}\n{response.data[0].url}")
        except Exception as e:
            await message.edit(content=f"生成圖片時發生錯誤: {e!s}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    bot.add_cog(ImageGeneratorCogs(bot), override=True)
