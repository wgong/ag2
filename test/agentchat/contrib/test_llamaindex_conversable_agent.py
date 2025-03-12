# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from  https://github.com/microsoft/autogen are under the MIT License.
# SPDX-License-Identifier: MIT
# !/usr/bin/env python3 -m pytest

from unittest.mock import MagicMock, patch

from autogen import GroupChat, GroupChatManager
from autogen.agentchat.contrib.llamaindex_conversable_agent import LLamaIndexConversableAgent
from autogen.agentchat.conversable_agent import ConversableAgent
from autogen.import_utils import optional_import_block, run_for_optional_imports

from ...conftest import MOCK_OPEN_AI_API_KEY

with optional_import_block() as result:
    from llama_index.core.agent import ReActAgent
    from llama_index.core.chat_engine.types import AgentChatResponse
    from llama_index.llms.openai import OpenAI


openai_key = MOCK_OPEN_AI_API_KEY


@run_for_optional_imports(["llama_index"], "neo4j")
@patch("llama_index.core.agent.ReActAgent.chat")
def test_group_chat_with_llama_index_conversable_agent(chat_mock: MagicMock) -> None:
    """Tests the group chat functionality with two MultimodalConversable Agents.
    Verifies that the chat is correctly limited by the max_round parameter.
    Each agent is set to describe an image in a unique style, but the chat should not exceed the specified max_rounds.
    """
    llm = OpenAI(
        model="gpt-4o",
        temperature=0.0,
        api_key=openai_key,
    )

    chat_mock.return_value = AgentChatResponse(
        response="Visit ghibli studio in Tokyo, Japan. It is a must-visit place for fans of Hayao Miyazaki and his movies like Spirited Away."
    )

    location_specialist = ReActAgent.from_tools(llm=llm, max_iterations=5)

    # create an autogen agent using the react agent
    trip_assistant = LLamaIndexConversableAgent(
        "trip_specialist",
        llama_index_agent=location_specialist,
        system_message="You help customers finding more about places they would like to visit. You can use external resources to provide more details as you engage with the customer.",
        description="This agents helps customers discover locations to visit, things to do, and other details about a location. It can use external resources to provide more details. This agent helps in finding attractions, history and all that there si to know about a place",
    )

    llm_config = False
    max_round = 5

    user_proxy = ConversableAgent(
        "customer",
        max_consecutive_auto_reply=10,
        human_input_mode="NEVER",
        llm_config=False,
        default_auto_reply="Thank you. TERMINATE",
    )

    group_chat = GroupChat(
        agents=[user_proxy, trip_assistant],
        messages=[],
        max_round=100,
        send_introductions=False,
        speaker_selection_method="round_robin",
    )

    group_chat_manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        is_termination_msg=lambda x: x.get("content", "").rstrip().find("TERMINATE") >= 0,
    )

    # Initiating the group chat and observing the number of rounds
    user_proxy.initiate_chat(
        group_chat_manager,
        message="What can i find in Tokyo related to Hayao Miyazaki and its moveis like Spirited Away?.",
    )

    # Assertions to check if the number of rounds does not exceed max_round
    assert all(len(arr) <= max_round for arr in trip_assistant._oai_messages.values()), "Agent 1 exceeded max rounds"
    assert all(len(arr) <= max_round for arr in user_proxy._oai_messages.values()), "User proxy exceeded max rounds"


if __name__ == "__main__":
    """Runs this file's tests from the command line."""
    test_group_chat_with_llama_index_conversable_agent()
