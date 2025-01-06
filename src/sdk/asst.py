import time
from typing import Any, Optional

from openai import OpenAI
from pydantic import Field, ConfigDict, computed_field
from openai.pagination import SyncCursorPage
from openai.types.beta import Thread, Assistant, ThreadDeleted, AssistantDeleted
from openai.types.beta.threads import Run, Message, MessageDeleted
from autogen.agentchat.contrib.img_utils import get_pil_image, pil_to_data_uri

from src.types.config import Config
from src.types.database import DatabaseConfig


class AssistantAPI(Config):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    thread_id: Optional[str] = Field(default=None)
    assistant_id: Optional[str] = Field(default=None)
    message_id: Optional[str] = Field(default=None)
    metadata: dict[str, str] = Field(default={"backend_id": "default"})
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)

    @computed_field
    @property
    def client(self) -> OpenAI:
        client = OpenAI(api_key=self.openai_api_key, base_url="https://api.openai.com/v1")
        return client

    def create_or_retrieve_thread(self) -> Thread:
        try:
            thread = self.client.beta.threads.retrieve(self.thread_id)
        except Exception:
            thread = self.client.beta.threads.create(metadata=self.metadata)
        self.thread_id = thread.id
        return thread

    def retrieve_assistant_by_settings(
        self, name: str, model: str, description: str, instructions: str
    ) -> Assistant:
        existing_assistants = self.client.beta.assistants.list()
        current_asst_config = {
            "name": name,
            "model": model,
            "description": description,
            "instructions": instructions,
        }
        matched_assistants: list[Assistant] = []
        for _existing_assistant in existing_assistants:
            existing_asst_config = _existing_assistant.model_dump(
                include={"name", "model", "description", "instructions"}
            )
            if existing_asst_config == current_asst_config:
                matched_assistants.append(_existing_assistant)

        if not matched_assistants:
            assistant = self.client.beta.assistants.create(
                name=name,
                model=model,
                description=description,
                instructions=instructions,
                metadata=self.metadata,
            )
            matched_assistants.append(assistant)

        self.assistant_id = matched_assistants[0].id
        return matched_assistants[0]

    def delete_thread(self, thread_id: str) -> ThreadDeleted:
        deleted_thread = self.client.beta.threads.delete(thread_id=thread_id)
        return deleted_thread

    def create_or_retrieve_assistant(
        self, name: str, model: str, description: str, instructions: str
    ) -> Assistant:
        try:
            assistant = self.client.beta.assistants.retrieve(self.assistant_id)
        except Exception:
            assistant = self.client.beta.assistants.create(
                name=name,
                model=model,
                description=description,
                instructions=instructions,
                metadata=self.metadata,
            )
        self.assistant_id = assistant.id
        return assistant

    def delete_assistant(self, asst_id: str) -> AssistantDeleted:
        deleted_assistant = self.client.beta.assistants.delete(assistant_id=asst_id)
        return deleted_assistant

    def create_message(self, content: str, image_urls: list[str]) -> Message:
        base_content: list[dict[str, Any]] = [{"type": "text", "text": content}]
        for image_url in image_urls:
            image = get_pil_image(image_file=image_url)
            image_base64 = pil_to_data_uri(image=image)
            base_content.append({"type": "image_url", "image_url": {"url": image_base64}})

        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id, content=base_content, role="user"
        )
        self.message_id = message.id
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

    def retrieve_run(self, thread_id: str, run_id: str) -> Run:
        message = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        return message

    def delete_run(self, thread_id: str, run_id: str) -> Run:
        deleted_message = self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
        return deleted_message

    def create_run(self) -> Run:
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id, assistant_id=self.assistant_id
        )

        def wait_on_run(run: Run) -> Run:
            while run.status == "queued" or run.status == "in_progress":
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id, run_id=run.id
                )
                time.sleep(0.5)
            return run

        wait_on_run(run=run)
        return run

    @computed_field
    @property
    def last_message(self) -> SyncCursorPage[Message]:
        last_message = self.client.beta.threads.messages.list(
            thread_id=self.thread_id, order="desc", after=self.message_id
        )
        return last_message.data[-1].content[-1].text


if __name__ == "__main__":
    asst_api = AssistantAPI()

    asst_api.create_or_retrieve_thread()
    asst_api.create_or_retrieve_assistant(
        name="Personal Assistant For Wei Cheng",
        model="aide-gpt-4o-realtime-preview",
        description="A virtual Wei Cheng Lee.",
        instructions="You are Wei Cheng Lee!!",
    )
    asst_api.create_message(content="請描述一下這張照片", image_urls=["./data/125075.jpg"])
    asst_api.create_run()
