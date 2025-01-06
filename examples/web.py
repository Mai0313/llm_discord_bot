from typing import Any

from autogen import UserProxyAgent
from autogen.agentchat.contrib.web_surfer import WebSurferAgent


def _get_llm_config(config_dict: dict[str, Any]) -> dict[str, Any]:
    llm_config = {
        "timeout": 60,
        "temperature": 0,
        "cache_seed": None,
        "config_list": [config_dict],
    }
    return llm_config


def scrape_web(api_key: str, bing_api_key: str, prompt: str) -> str:
    llm_config = _get_llm_config(config_dict={"model": "gpt-4o-mini", "api_key": api_key})
    summarizer_llm_config = _get_llm_config(
        config_dict={"model": "gpt-4o-mini", "api_key": api_key}
    )

    user_proxy = UserProxyAgent(
        "user_proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
        default_auto_reply="",
        is_termination_msg=lambda x: True,
        silent=True,
    )

    web_agent = WebSurferAgent(
        name="WebSurferAgent",
        system_message="You need to summarize the content, and add some personal thoughts like suggestions or comments.",
        llm_config=llm_config,
        summarizer_llm_config=summarizer_llm_config,
        browser_config={"viewport_size": 4096, "bing_api_key": bing_api_key},
        silent=True,
    )
    user_proxy.initiate_chat(web_agent, message=prompt, clear_history=False, silent=True)
    return user_proxy.chat_messages_for_summary(agent=web_agent)


if __name__ == "__main__":
    api_key = "..."
    bing_api_key = "..."
    prompt = "幫我找一下新竹有沒有好吃的消夜"
    result = scrape_web(api_key, bing_api_key, prompt)
    print(result[-1]["content"])
