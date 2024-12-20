import time

from openai import OpenAI
from pydantic import Field, computed_field
from openai.types.beta import Thread, Assistant, ThreadDeleted, AssistantDeleted
from openai.types.beta.threads import Run, Message, MessageDeleted

from src.types.config import Config
from src.types.database import DatabaseConfig


class DiscordAssistant(Config):
    user_id: str = Field(..., description="This should be the discord id of the user.")
    selected_model: str = Field(default="gpt-4o")
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)

    @computed_field
    @property
    def client(self) -> OpenAI:
        client = OpenAI(api_key=self.openai_api_key, base_url="https://api.openai.com/v1")
        return client

    def create_thread(self) -> Thread:
        thread = self.client.beta.threads.create()
        return thread

    def retrieve_thread(self, thread_id: str) -> Thread:
        thread = self.client.beta.threads.retrieve(thread_id=thread_id)
        return thread

    def delete_thread(self, thread_id: str) -> ThreadDeleted:
        deleted_thread = self.client.beta.threads.delete(thread_id=thread_id)
        return deleted_thread

    def create_assistant(self, asst_name: str, asst_prompt: str) -> Assistant:
        assistant = self.client.beta.assistants.create(
            model=self.selected_model, name=asst_name, instructions=asst_prompt
        )
        return assistant

    def list_assistants(self) -> list[Assistant]:
        assistants = self.client.beta.assistants.list()
        return assistants

    def retrieve_assistant(self, asst_id: str) -> Assistant:
        assistant = self.client.beta.assistants.retrieve(assistant_id=asst_id)
        return assistant

    def delete_assistant(self, asst_id: str) -> AssistantDeleted:
        deleted_assistant = self.client.beta.assistants.delete(assistant_id=asst_id)
        return deleted_assistant

    def create_message(self, thread_id: str, content: str) -> Message:
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id, content=content, role="user"
        )
        return message

    def list_messages(self, thread_id: str) -> list[Message]:
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        return messages

    def retrieve_message(self, thread_id: str, message_id: str) -> Message:
        message = self.client.beta.threads.messages.retrieve(
            thread_id=thread_id, message_id=message_id
        )
        return message

    def delete_message(self, thread_id: str, message_id: str) -> MessageDeleted:
        deleted_message = self.client.beta.threads.messages.delete(
            thread_id=thread_id, message_id=message_id
        )
        return deleted_message

    def create_run(self, thread_id: str, asst_id: str) -> Run:
        message = self.client.beta.threads.runs.create(thread_id=thread_id, assistant_id=asst_id)
        return message

    def retrieve_run(self, thread_id: str, run_id: str) -> Run:
        message = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        return message

    def delete_run(self, thread_id: str, run_id: str) -> Run:
        deleted_message = self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
        return deleted_message

    def wait_on_run(self, run: Run, thread: Thread) -> Run:
        while run.status == "queued" or run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            time.sleep(0.5)
        return run

    def create_and_run(self, asst_prompt: str, content: str) -> list[Message]:
        user_info = self.db.redis.load(key=self.user_id)
        if user_info:
            thread = self.retrieve_thread(thread_id=user_info["thread_id"])
            assistant = self.retrieve_assistant(asst_id=user_info["assistant_id"])
        else:
            thread = self.create_thread()
            assistant = self.create_assistant(asst_name=self.user_id, asst_prompt=asst_prompt)
        dc_asst.create_message(thread_id=thread.id, content=content)
        run = dc_asst.create_run(thread_id=thread.id, asst_id=assistant.id)
        self.wait_on_run(run=run, thread=thread)
        messages = self.list_messages(thread_id=thread.id)
        user_info = {"thread_id": thread.id, "assistant_id": assistant.id}
        self.db.redis.save(key=self.user_id, data=user_info)
        return messages


if __name__ == "__main__":
    dc_asst = DiscordAssistant(user_id="Wei")
    result = dc_asst.create_and_run(
        asst_prompt="This is a test assistant.", content="Hello, 你是誰!"
    )
