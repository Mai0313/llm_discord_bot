import nextcord
from nextcord import Locale, Member, Interaction, SlashOption
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


class MessageFetcher(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices(system_prompt=SUMMARY_PROMPT)

    @nextcord.slash_command(
        name="sum",
        description="Summarize the most recent N messages in the current channel.",
        name_localizations={Locale.zh_TW: "總結訊息", Locale.ja: "メッセージ要約"},
        description_localizations={
            Locale.zh_TW: "總結此頻道中最近 N 則訊息。",
            Locale.ja: "このチャンネルの直近 N 件のメッセージを要約します。",
        },
        dm_permission=True,
        nsfw=False,
    )
    async def sum(
        self,
        interaction: Interaction,
        history_count: int = SlashOption(
            description="Number of messages to summarize.",
            description_localizations={
                Locale.zh_TW: "要總結的訊息數量。",
                Locale.ja: "要約するメッセージの数。",
            },
            default=20,
        ),
        target_user: Member = SlashOption(
            description="User to summarize messages from (optional).",
            description_localizations={
                Locale.zh_TW: "要總結訊息的目標使用者 (可選)。",
                Locale.ja: "要約対象のユーザー (任意)。",
            },
            required=False,
        ),
    ) -> None:
        """Summarizes the most recent N messages in the current channel. If a user is specified, only summarizes the most recent N messages from that user.

        Args:
            interaction (nextcord.Interaction): The interaction context.
            history_count (int): The number of historical messages to summarize. Defaults to 20.
            target_user (nextcord.User): The user whose messages to summarize. Defaults to None.

        Returns:
            None

        Raises:
            Exception: If an error occurs during the summarization process.

        Example:
            !sum 10 @username
                If no number is provided, the default is 20.
        """
        try:
            # 2. 從頻道抓取對應的歷史訊息
            messages = await self._fetch_messages(interaction.channel, history_count, target_user)

            if not messages:
                if target_user:
                    await interaction.response.send_message(
                        f"在此頻道中找不到 {target_user.mention} 的相關訊息。", ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "此頻道沒有可供總結的訊息。", ephemeral=True
                    )
                return

            # 3. 整理訊息成文字
            chat_history_string, attachments = self._format_messages(messages)

            # 4. 建立要給模型的最終 Prompt
            final_prompt = self._create_summary_prompt(history_count, chat_history_string)

            # 5. 呼叫 LLM 進行總結
            summary = await self._call_llm(final_prompt, attachments)

            # 6. 回傳總結結果
            await interaction.response.send_message(summary)

        except Exception as e:
            # 錯誤處理
            await interaction.response.send_message(f"發生錯誤：{e}", ephemeral=True)

    async def _fetch_messages(
        self, channel: nextcord.TextChannel, history_count: int, target_user: nextcord.User | None
    ) -> list[nextcord.Message]:
        """Fetches the most recent N messages from a Discord channel and filters them by user if specified.

        Args:
            channel (discord.TextChannel): The Discord channel from which to fetch messages.
            history_count (int): The number of historical messages to fetch.
            target_user (discord.User | None): The user whose messages to filter by.

        Returns:
            list[discord.Message]: A list of Discord message objects.
        """
        messages = []
        if target_user:
            # 從最舊到最新，過濾出指定用戶訊息
            async for msg in channel.history(limit=None):
                if msg.author.id == target_user.id and not msg.author.bot:
                    messages.append(msg)
                    if len(messages) == history_count:
                        break
        else:
            # 直接抓取最近的 history_count 筆
            async for msg in channel.history(limit=history_count):
                if not msg.author.bot:
                    messages.append(msg)

        # 依照訊息時間做排序（由舊到新）
        messages.reverse()
        return messages

    def _format_messages(self, messages: list[nextcord.Message]) -> tuple[str, list[str]]:
        """Formats a list of Discord messages into a string and extracts embed descriptions or attachment URLs.

        Args:
            messages (list[discord.Message]): A list of Discord message objects to be formatted.

        Returns:
            tuple[str, list[str]]: A tuple containing:
                - chat_history_string (str): A string containing the text of all messages.
                - attachments (list[str]): A list of all links or descriptions that can be used as references.
        """
        chat_history_lines = []
        attachments = []

        for msg in messages:
            content_text = msg.content

            if msg.embeds:
                # 取出 embed 的描述
                embed_descriptions = [
                    embed.description for embed in msg.embeds if embed.description
                ]
                # 當作參考資料
                attachments.extend(embed_descriptions)
                content_text = "嵌入內容: " + ", ".join(embed_descriptions)

            elif msg.attachments:
                # 取出附件 URL
                attachment_urls = [att.url for att in msg.attachments]
                attachments.extend(attachment_urls)
                content_text = "附件: " + ", ".join(attachment_urls)

            chat_history_lines.append(f"{msg.author.name}: {content_text}")

        chat_history_string = "\n".join(chat_history_lines)
        return chat_history_string, attachments

    def _create_summary_prompt(self, history_count: int, chat_history_string: str) -> str:
        """Creates a summary prompt based on the SUMMARY_MESSAGE template.

        Args:
            history_count (int): The number of historical messages to include in the summary.
            chat_history_string (str): The string representation of the chat history.

        Returns:
            str: The formatted summary prompt.
        """
        return SUMMARY_MESSAGE.format(
            history_count=history_count, chat_history_string=chat_history_string
        )

    async def _call_llm(self, prompt: str, attachments: list[str]) -> str:
        """Asynchronously calls the LLM (Language Learning Model) to summarize a message.

        Args:
            prompt (str): The prompt or message to be summarized.
            attachments (list[str]): A list of URLs pointing to images, videos, or embedded description links that can be referenced.

        Returns:
            str: The summarized content returned by the LLM.
        """
        response = await self.llm_services.get_oai_reply(prompt=prompt, image_urls=attachments)
        # 假設回傳格式: response.choices[0].message.content
        return response.choices[0].message.content


async def setup(bot: commands.Bot) -> None:
    bot.add_cog(MessageFetcher(bot), override=True)
