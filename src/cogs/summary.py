import nextcord
from nextcord import Locale, Member, Interaction
from nextcord.ext import commands

from src.sdk.llm import LLMServices

SUMMARY_PROMPT = """
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


# --- 定義選單視窗 ---
class SummarizeMenuView(nextcord.ui.View):
    def __init__(self, bot: commands.Bot, original_interaction: Interaction, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.original_interaction = original_interaction
        self.history_count: int | None = None
        self.target_user: Member | None = None

    @nextcord.ui.select(
        placeholder="選擇要總結的訊息數量",
        options=[
            nextcord.SelectOption(label="5", value="5"),
            nextcord.SelectOption(label="10", value="10"),
            nextcord.SelectOption(label="20", value="20"),
            nextcord.SelectOption(label="50", value="50"),
        ],
    )
    async def select_history_count(
        self, select: nextcord.ui.Select, interaction: Interaction
    ) -> None:
        # 儲存選擇的訊息數量
        self.history_count = int(select.values[0])
        # 簡單回應以確認選擇（不會產生新訊息）
        await interaction.response.defer()

    @nextcord.ui.user_select(placeholder="選擇要總結的使用者 (可選)", min_values=0, max_values=1)
    async def select_target_user(
        self, user_select: nextcord.ui.UserSelect, interaction: Interaction
    ) -> None:
        # 如果有選擇使用者，則儲存；否則保持 None
        if user_select.values:
            self.target_user = user_select.values[0]
        else:
            self.target_user = None
        await interaction.response.defer()

    @nextcord.ui.button(label="提交", style=nextcord.ButtonStyle.primary)
    async def submit(self, button: nextcord.ui.Button, interaction: Interaction) -> None:
        # 如果使用者未選擇訊息數量，則採用預設 20
        if self.history_count is None:
            self.history_count = 20

        # 取得負責訊息總結的 Cog
        cog: MessageFetcher = self.bot.get_cog("MessageFetcher")
        if cog is None:
            await interaction.response.send_message("找不到訊息總結的處理器。", ephemeral=True)
            self.stop()
            return

        # 回應「處理中…」（避免互動逾時）
        await interaction.response.defer(ephemeral=True)

        # 執行總結流程
        summary = await cog.do_summarize(interaction.channel, self.history_count, self.target_user)
        await interaction.followup.send(summary, ephemeral=True)
        self.stop()


# --- 原本的訊息總結 Cog ---
class MessageFetcher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices(system_prompt=SUMMARY_PROMPT)

    @nextcord.slash_command(
        name="sum",
        description="透過選單選擇總結訊息。",
        name_localizations={Locale.zh_TW: "總結訊息", Locale.ja: "メッセージ要約"},
        description_localizations={
            Locale.zh_TW: "使用選單來總結此頻道中的訊息。",
            Locale.ja: "メニュー選択を通じて、このチャンネルのメッセージを要約します。",
        },
        dm_permission=True,
        nsfw=False,
    )
    async def sum(self, interaction: Interaction) -> None:
        """呼叫此指令後，會彈出一個選單視窗讓你選擇
        - 要總結的訊息數量
        - 是否僅總結某個使用者的訊息（可選）
        """
        view = SummarizeMenuView(self.bot, interaction)
        await interaction.response.send_message("請選擇總結選項：", view=view, ephemeral=True)

    async def do_summarize(
        self, channel: nextcord.TextChannel, history_count: int, target_user: Member | None
    ) -> str:
        """根據頻道、訊息數量與目標使用者，抓取並整理訊息，
        接著呼叫 LLM 來產生總結內容。

        Returns:
            str: 總結的結果。
        """
        messages = await self._fetch_messages(channel, history_count, target_user)
        if not messages:
            if target_user:
                return f"在此頻道中找不到 {target_user.mention} 的相關訊息。"
            return "此頻道沒有可供總結的訊息。"

        chat_history_string, attachments = self._format_messages(messages)
        final_prompt = self._create_summary_prompt(history_count, chat_history_string)
        summary = await self._call_llm(final_prompt, attachments)
        return summary

    async def _fetch_messages(
        self, channel: nextcord.TextChannel, history_count: int, target_user: Member | None
    ) -> list[nextcord.Message]:
        messages = []
        if target_user:
            # 從最舊到最新，過濾出指定使用者的訊息
            async for msg in channel.history(limit=None):
                if msg.author.id == target_user.id and not msg.author.bot:
                    messages.append(msg)
                    if len(messages) == history_count:
                        break
        else:
            # 直接抓取最近 history_count 筆非機器人訊息
            async for msg in channel.history(limit=history_count):
                if not msg.author.bot:
                    messages.append(msg)
        messages.reverse()
        return messages

    def _format_messages(self, messages: list[nextcord.Message]) -> tuple[str, list[str]]:
        chat_history_lines = []
        attachments = []
        for msg in messages:
            content_text = msg.content
            if msg.embeds:
                embed_descriptions = [
                    embed.description for embed in msg.embeds if embed.description
                ]
                attachments.extend(embed_descriptions)
                content_text = "嵌入內容: " + ", ".join(embed_descriptions)
            elif msg.attachments:
                attachment_urls = [att.url for att in msg.attachments]
                attachments.extend(attachment_urls)
                content_text = "附件: " + ", ".join(attachment_urls)
            chat_history_lines.append(f"{msg.author.name}: {content_text}")
        chat_history_string = "\n".join(chat_history_lines)
        return chat_history_string, attachments

    def _create_summary_prompt(self, history_count: int, chat_history_string: str) -> str:
        return SUMMARY_MESSAGE.format(
            history_count=history_count, chat_history_string=chat_history_string
        )

    async def _call_llm(self, prompt: str, attachments: list[str]) -> str:
        response = await self.llm_services.get_oai_reply(prompt=prompt, image_urls=attachments)
        return response.choices[0].message.content


async def setup(bot: commands.Bot) -> None:
    bot.add_cog(MessageFetcher(bot), override=True)
