# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from  https://github.com/microsoft/autogen are under the MIT License.
# SPDX-License-Identifier: MIT
import os
from unittest.mock import MagicMock, patch

import pytest

from autogen.agentchat.contrib.capabilities.vision_capability import VisionCapability
from autogen.agentchat.conversable_agent import ConversableAgent
from autogen.import_utils import optional_import_block, run_for_optional_imports

with optional_import_block() as result:
    from PIL import Image  # noqa: F401


@pytest.fixture
def lmm_config():
    return {
        "config_list": [{"api_type": "openai", "model": "gpt-4-vision-preview", "api_key": "sk-my_key"}],
        "temperature": 0.5,
        "max_tokens": 300,
    }


img_name = os.path.abspath("test/test_files/test_image.png")


@pytest.fixture
def vision_capability(lmm_config):
    return VisionCapability(lmm_config, custom_caption_func=None)


@pytest.fixture
def conversable_agent():
    return ConversableAgent(name="conversable_agent", llm_config=False)


@run_for_optional_imports(["PIL"], "unknown")
@run_for_optional_imports(["openai"], "openai")
def test_add_to_conversable_agent(vision_capability, conversable_agent):
    vision_capability.add_to_agent(conversable_agent)
    assert hasattr(conversable_agent, "process_last_received_message")


@run_for_optional_imports(["PIL"], "unknown")
@run_for_optional_imports(["openai"], "openai")
@patch("autogen.oai.client.OpenAIWrapper")
def test_process_last_received_message_text(mock_lmm_client, vision_capability):
    mock_lmm_client.create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="A description"))])
    content = "Test message without image"
    processed_content = vision_capability.process_last_received_message(content)
    assert processed_content == content


@patch("autogen.agentchat.contrib.img_utils.get_image_data", return_value="base64_image_data")
@patch(
    "autogen.agentchat.contrib.img_utils.convert_base64_to_data_uri",
    return_value="data:image/png;base64,base64_image_data",
)
@patch(
    "autogen.agentchat.contrib.capabilities.vision_capability.VisionCapability._get_image_caption",
    return_value="A sample image caption.",
)
@run_for_optional_imports(["PIL"], "unknown")
@run_for_optional_imports(["openai"], "openai")
def test_process_last_received_message_with_image(
    mock_get_caption, mock_convert_base64, mock_get_image_data, vision_capability
):
    content = [{"type": "image_url", "image_url": {"url": (img_name)}}]
    expected_caption = (
        f"<img {img_name}> in case you can not see, the caption of this image is: A sample image caption.\n"
    )
    processed_content = vision_capability.process_last_received_message(content)
    assert processed_content == expected_caption


# Test the Custom Caption Func


@pytest.fixture
def custom_caption_func():
    """Fixture to provide a sample custom caption function."""

    def caption_func(image_url: str, image_data=None, lmm_client=None) -> str:
        # This is a simplistic example. Replace with the actual logic.
        return f"An image description. The image is from {image_url}."

    return caption_func


@run_for_optional_imports(["PIL"], "unknown")
@run_for_optional_imports(["openai"], "openai")
class TestCustomCaptionFunc:
    def test_custom_caption_func_with_valid_url(self, custom_caption_func):
        """Test custom caption function with a valid image URL."""
        image_url = img_name
        expected_caption = f"An image description. The image is from {image_url}."
        assert custom_caption_func(image_url) == expected_caption, "Caption does not match expected output."

    def test_process_last_received_message_with_custom_func(self, lmm_config, custom_caption_func):
        """Test processing a message containing an image URL with a custom caption function."""
        vision_capability = VisionCapability(lmm_config, custom_caption_func=custom_caption_func)

        image_url = img_name
        content = [{"type": "image_url", "image_url": {"url": image_url}}]
        expected_output = f" An image description. The image is from {image_url}."
        processed_content = vision_capability.process_last_received_message(content)
        assert expected_output in processed_content, "Processed content does not contain the expected caption."
