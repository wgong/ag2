# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from  https://github.com/microsoft/autogen are under the MIT License.
# SPDX-License-Identifier: MIT
import itertools
import os
import tempfile
from typing import Any

import pytest

from autogen import code_utils
from autogen.agentchat.contrib.capabilities import generate_images
from autogen.agentchat.contrib.img_utils import get_pil_image
from autogen.agentchat.conversable_agent import ConversableAgent
from autogen.agentchat.user_proxy_agent import UserProxyAgent
from autogen.cache.cache import Cache
from autogen.import_utils import optional_import_block, run_for_optional_imports
from autogen.oai import openai_utils

from ....conftest import MOCK_OPEN_AI_API_KEY

with optional_import_block() as result:
    from PIL import Image


filter_dict = {"model": ["gpt-4o-mini"]}

RESOLUTIONS = ["1024x1024", "1792x1024", "1024x1792"]
QUALITIES = ["standard", "hd"]
PROMPTS = [
    "Generate an image of a robot holding a 'I Love AG2' sign",
    "Generate an image of a dog holding a 'I Love AG2' sign",
]


class _TestImageGenerator:
    def __init__(self, image):
        self._image = image

    def generate_image(self, prompt: str):
        return self._image

    def cache_key(self, prompt: str):
        return prompt


def create_test_agent(name: str = "test_agent", default_auto_reply: str = "") -> ConversableAgent:
    return ConversableAgent(name=name, llm_config=False, default_auto_reply=default_auto_reply)


def dalle_image_generator(dalle_config: dict[str, Any], resolution: str, quality: str):
    return generate_images.DalleImageGenerator(dalle_config, resolution=resolution, quality=quality, num_images=1)


def api_key():
    return os.environ.get("OPENAI_API_KEY", MOCK_OPEN_AI_API_KEY)


@pytest.fixture
def dalle_config() -> dict[str, Any]:
    config_list = openai_utils.config_list_from_models(model_list=["dall-e-3"], exclude="aoai")
    if not config_list:
        config_list = [{"api_type": "openai", "model": "dall-e-3", "api_key": api_key()}]
    return {"config_list": config_list, "timeout": 120, "cache_seed": None}


@pytest.fixture
def gpt4_config() -> dict[str, Any]:
    config_list = [
        {
            "model": "gpt-4o-mini",
            "api_key": api_key(),
        },
        {
            "model": "gpt-4o",
            "api_key": api_key(),
        },
    ]
    return {"config_list": config_list, "timeout": 120, "cache_seed": None}


@pytest.fixture
def image_gen_capability():
    image_generator = _TestImageGenerator(Image.new("RGB", (256, 256)))
    return generate_images.ImageGeneration(image_generator)


@run_for_optional_imports("openai", "openai")
@run_for_optional_imports("PIL", "unknown")
@run_for_optional_imports(["openai"], "openai")
def test_dalle_image_generator(dalle_config: dict[str, Any]):
    """Tests DalleImageGenerator capability to generate images by calling the OpenAI API."""
    dalle_generator = dalle_image_generator(dalle_config, RESOLUTIONS[0], QUALITIES[0])
    image = dalle_generator.generate_image(PROMPTS[0])

    assert isinstance(image, Image.Image)


# Using cartesian product to generate all possible combinations of resolution, quality, and prompt
@pytest.mark.parametrize("gen_config_1", itertools.product(RESOLUTIONS, QUALITIES, PROMPTS))
@pytest.mark.parametrize("gen_config_2", itertools.product(RESOLUTIONS, QUALITIES, PROMPTS))
@run_for_optional_imports(["PIL"], "unknown")
@run_for_optional_imports(["openai"], "openai")
def test_dalle_image_generator_cache_key(
    dalle_config: dict[str, Any], gen_config_1: tuple[str, str, str], gen_config_2: tuple[str, str, str]
):
    """Tests if DalleImageGenerator creates unique cache keys.

    Args:
        dalle_config: The LLM config for the DalleImageGenerator.
        gen_config_1: A tuple containing the resolution, quality, and prompt for the first image generator.
        gen_config_2: A tuple containing the resolution, quality, and prompt for the second image generator.
    """
    dalle_generator_1 = dalle_image_generator(dalle_config, resolution=gen_config_1[0], quality=gen_config_1[1])
    dalle_generator_2 = dalle_image_generator(dalle_config, resolution=gen_config_2[0], quality=gen_config_2[1])

    cache_key_1 = dalle_generator_1.cache_key(gen_config_1[2])
    cache_key_2 = dalle_generator_2.cache_key(gen_config_2[2])

    if gen_config_1 == gen_config_2:
        assert cache_key_1 == cache_key_2
    else:
        assert cache_key_1 != cache_key_2


@run_for_optional_imports(["PIL"], "unknown")
def test_image_generation_capability_positive(monkeypatch, image_gen_capability):
    """Tests ImageGeneration capability to generate images by calling the ImageGenerator.

    This tests if the message is asking the agent to generate an image.
    """
    auto_reply = "Didn't need to generate an image."

    # Patching the _should_generate_image and _extract_prompt methods to avoid TextAnalyzerAgent to make API calls
    # Improves reproducibility and falkiness of the test
    monkeypatch.setattr(generate_images.ImageGeneration, "_should_generate_image", lambda _, __: True)
    monkeypatch.setattr(generate_images.ImageGeneration, "_extract_prompt", lambda _, __: PROMPTS[0])

    user = UserProxyAgent("user", human_input_mode="NEVER")
    agent = create_test_agent(default_auto_reply=auto_reply)
    image_gen_capability.add_to_agent(agent)

    user.send(message=PROMPTS[0], recipient=agent, request_reply=True, silent=True)
    last_message = agent.last_message()

    assert last_message

    processed_message = code_utils.content_str(last_message["content"])

    assert "<image>" in processed_message
    assert auto_reply not in processed_message


@run_for_optional_imports(["PIL"], "unknown")
def test_image_generation_capability_negative(monkeypatch, image_gen_capability):
    """Tests ImageGeneration capability to generate images by calling the ImageGenerator.

    This tests if the message is not asking the agent to generate an image.
    """
    auto_reply = "Didn't need to generate an image."

    # Patching the _should_generate_image and _extract_prompt methods to avoid TextAnalyzerAgent making API calls.
    # Improves reproducibility and flakiness of the test.
    monkeypatch.setattr(generate_images.ImageGeneration, "_should_generate_image", lambda _, __: False)
    monkeypatch.setattr(generate_images.ImageGeneration, "_extract_prompt", lambda _, __: PROMPTS[0])

    user = UserProxyAgent("user", human_input_mode="NEVER")
    agent = ConversableAgent("test_agent", llm_config=False, default_auto_reply=auto_reply)
    image_gen_capability.add_to_agent(agent)

    user.send(message=PROMPTS[0], recipient=agent, request_reply=True, silent=True)
    last_message = agent.last_message()

    assert last_message

    processed_message = code_utils.content_str(last_message["content"])

    assert "<image>" not in processed_message
    assert auto_reply == processed_message


@run_for_optional_imports(["PIL"], "unknown")
def test_image_generation_capability_cache(monkeypatch):
    """Tests ImageGeneration capability to cache the generated images."""
    test_image_size = (256, 256)

    # Patching the _should_generate_image and _extract_prompt methods to avoid TextAnalyzerAgent making API calls.
    monkeypatch.setattr(generate_images.ImageGeneration, "_should_generate_image", lambda _, __: True)
    monkeypatch.setattr(generate_images.ImageGeneration, "_extract_prompt", lambda _, __: PROMPTS[0])

    with tempfile.TemporaryDirectory() as temp_dir:
        cache = Cache.disk(cache_path_root=temp_dir)

        user = UserProxyAgent("user", human_input_mode="NEVER")
        agent = create_test_agent()

        test_image_generator = _TestImageGenerator(Image.new("RGB", test_image_size))
        image_gen_capability = generate_images.ImageGeneration(test_image_generator, cache=cache)
        image_gen_capability.add_to_agent(agent)

        user.send(message=PROMPTS[0], recipient=agent, request_reply=True, silent=True)

        # Checking if the image has been cached by creating a new agent with a different image generator.
        agent = create_test_agent(name="test_agent_2")
        test_image_generator = _TestImageGenerator(Image.new("RGB", (512, 512)))
        image_gen_capability = generate_images.ImageGeneration(test_image_generator, cache=cache)
        image_gen_capability.add_to_agent(agent)

        user.send(message=PROMPTS[0], recipient=agent, request_reply=True, silent=True)

        last_message = agent.last_message()

        assert last_message

        image_dict = [image for image in last_message["content"] if image["type"] == "image_url"]
        image = get_pil_image(image_dict[0]["image_url"]["url"])

        assert image.size == test_image_size


if __name__ == "__main__":
    test_dalle_image_generator(
        dalle_config={"config_list": openai_utils.config_list_from_models(model_list=["dall-e-3"], exclude="aoai")}
    )
