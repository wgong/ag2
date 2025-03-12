# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from  https://github.com/microsoft/autogen are under the MIT License.
# SPDX-License-Identifier: MIT
# !/usr/bin/env python3 -m pytest

import base64
import os
import unittest
from unittest.mock import patch

import requests

from autogen.agentchat.contrib.img_utils import (
    convert_base64_to_data_uri,
    extract_img_paths,
    get_image_data,
    get_pil_image,
    gpt4v_formatter,
    llava_formatter,
    message_formatter_pil_to_b64,
    num_tokens_from_gpt_image,
)
from autogen.import_utils import optional_import_block, run_for_optional_imports

with optional_import_block():
    import numpy as np

with optional_import_block() as result:
    from PIL import Image

if result.is_successful:
    raw_pil_image = Image.new("RGB", (10, 10), color="red")


base64_encoded_image = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4"
    "//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
)

raw_encoded_image = (
    "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4"
    "//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
)


@run_for_optional_imports(["PIL"], "unknown")
@run_for_optional_imports(["numpy"], "flaml")
class TestGetPilImage:
    def test_read_local_file(self):
        # Create a small red image for testing
        temp_file = "_temp.png"
        raw_pil_image.save(temp_file)
        img2 = get_pil_image(temp_file)
        assert (np.array(raw_pil_image) == np.array(img2)).all()

    def test_read_pil(self):
        # Create a small red image for testing
        img2 = get_pil_image(raw_pil_image)
        assert (np.array(raw_pil_image) == np.array(img2)).all()


@run_for_optional_imports(["numpy"], "flaml")
def are_b64_images_equal(x: str, y: str):
    """Asserts that two base64 encoded images are equal."""
    img1 = get_pil_image(x)
    img2 = get_pil_image(y)
    return (np.array(img1) == np.array(img2)).all()


@run_for_optional_imports(["PIL"], "unknown")
class TestGetImageData:
    def test_http_image(self):
        with patch("requests.get") as mock_get:
            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_response._content = base64.b64decode(raw_encoded_image)
            mock_get.return_value = mock_response

            result = get_image_data("http://example.com/image.png")
            assert are_b64_images_equal(result, raw_encoded_image)

    def test_base64_encoded_image(self):
        result = get_image_data(base64_encoded_image)

        assert are_b64_images_equal(result, base64_encoded_image.split(",", 1)[1])

    def test_local_image(self):
        # Create a temporary file to simulate a local image file.
        temp_file = "_temp.png"
        image = Image.new("RGB", (60, 30), color=(73, 109, 137))
        image.save(temp_file)

        result = get_image_data(temp_file)
        with open(temp_file, "rb") as temp_image_file:
            temp_image_file.seek(0)
            expected_content = base64.b64encode(temp_image_file.read()).decode("utf-8")

        assert result == expected_content
        os.remove(temp_file)


@run_for_optional_imports(["PIL"], "unknown")
class TestLlavaFormater:
    def test_no_images(self):
        """Test the llava_formatter function with a prompt containing no images."""
        prompt = "This is a test."
        expected_output = (prompt, [])
        result = llava_formatter(prompt)
        assert result == expected_output

    @patch("autogen.agentchat.contrib.img_utils.get_image_data")
    def test_with_images(self, mock_get_image_data):
        """Test the llava_formatter function with a prompt containing images."""
        # Mock the get_image_data function to return a fixed string.
        mock_get_image_data.return_value = raw_encoded_image

        prompt = "This is a test with an image <img http://example.com/image.png>."
        expected_output = ("This is a test with an image <image>.", [raw_encoded_image])
        result = llava_formatter(prompt)
        assert result == expected_output

    @patch("autogen.agentchat.contrib.img_utils.get_image_data")
    def test_with_ordered_images(self, mock_get_image_data):
        """Test the llava_formatter function with ordered image tokens."""
        # Mock the get_image_data function to return a fixed string.
        mock_get_image_data.return_value = raw_encoded_image

        prompt = "This is a test with an image <img http://example.com/image.png>."
        expected_output = ("This is a test with an image <image 0>.", [raw_encoded_image])
        result = llava_formatter(prompt, order_image_tokens=True)
        assert result == expected_output


@run_for_optional_imports(["PIL"], "unknown")
class TestGpt4vFormatter:
    def test_no_images(self):
        """Test the gpt4v_formatter function with a prompt containing no images."""
        prompt = "This is a test."
        expected_output = [{"type": "text", "text": prompt}]
        result = gpt4v_formatter(prompt)
        assert result == expected_output

    @patch("autogen.agentchat.contrib.img_utils.get_image_data")
    def test_with_images(self, mock_get_image_data):
        """Test the gpt4v_formatter function with a prompt containing images."""
        # Mock the get_image_data function to return a fixed string.
        mock_get_image_data.return_value = raw_encoded_image

        prompt = "This is a test with an image <img http://example.com/image.png>."
        expected_output = [
            {"type": "text", "text": "This is a test with an image "},
            {"type": "image_url", "image_url": {"url": base64_encoded_image}},
            {"type": "text", "text": "."},
        ]
        result = gpt4v_formatter(prompt)
        assert result == expected_output

    @patch("autogen.agentchat.contrib.img_utils.get_pil_image")
    def test_with_images_for_pil(self, mock_get_pil_image):
        """Test the gpt4v_formatter function with a prompt containing images."""
        # Mock the get_image_data function to return a fixed string.
        mock_get_pil_image.return_value = raw_pil_image

        prompt = "This is a test with an image <img http://example.com/image.png>."
        expected_output = [
            {"type": "text", "text": "This is a test with an image "},
            {"type": "image_url", "image_url": {"url": raw_pil_image}},
            {"type": "text", "text": "."},
        ]
        result = gpt4v_formatter(prompt, img_format="pil")
        assert result == expected_output

    def test_with_images_for_url(self):
        """Test the gpt4v_formatter function with a prompt containing images."""
        prompt = "This is a test with an image <img http://example.com/image.png>."
        expected_output = [
            {"type": "text", "text": "This is a test with an image "},
            {"type": "image_url", "image_url": {"url": "http://example.com/image.png"}},
            {"type": "text", "text": "."},
        ]
        result = gpt4v_formatter(prompt, img_format="url")
        assert result, expected_output

    @patch("autogen.agentchat.contrib.img_utils.get_image_data")
    def test_multiple_images(self, mock_get_image_data):
        """Test the gpt4v_formatter function with a prompt containing multiple images."""
        # Mock the get_image_data function to return a fixed string.
        mock_get_image_data.return_value = raw_encoded_image

        prompt = (
            "This is a test with images <img http://example.com/image1.png> and <img http://example.com/image2.png>."
        )
        expected_output = [
            {"type": "text", "text": "This is a test with images "},
            {"type": "image_url", "image_url": {"url": base64_encoded_image}},
            {"type": "text", "text": " and "},
            {"type": "image_url", "image_url": {"url": base64_encoded_image}},
            {"type": "text", "text": "."},
        ]
        result = gpt4v_formatter(prompt)
        assert result == expected_output


@run_for_optional_imports(["PIL"], "unknown")
class TestExtractImgPaths:
    def test_no_images(self):
        """Test the extract_img_paths function with a paragraph containing no images."""
        paragraph = "This is a test paragraph with no images."
        expected_output = []
        result = extract_img_paths(paragraph)
        assert result == expected_output

    def test_with_images(self):
        """Test the extract_img_paths function with a paragraph containing images."""
        paragraph = (
            "This is a test paragraph with images http://example.com/image1.jpg and http://example.com/image2.png."
        )
        expected_output = ["http://example.com/image1.jpg", "http://example.com/image2.png"]
        result = extract_img_paths(paragraph)
        assert result == expected_output

    def test_mixed_case(self):
        """Test the extract_img_paths function with mixed case image extensions."""
        paragraph = "Mixed case extensions http://example.com/image.JPG and http://example.com/image.Png."
        expected_output = ["http://example.com/image.JPG", "http://example.com/image.Png"]
        result = extract_img_paths(paragraph)
        assert result == expected_output

    def test_local_paths(self):
        """Test the extract_img_paths function with local file paths."""
        paragraph = "Local paths image1.jpeg and image2.GIF."
        expected_output = ["image1.jpeg", "image2.GIF"]
        result = extract_img_paths(paragraph)
        assert result == expected_output


@run_for_optional_imports(["PIL"], "unknown")
class MessageFormatterPILtoB64Test:
    def test_formatting(self):
        messages = [
            {"content": [{"type": "text", "text": "You are a helpful AI assistant."}], "role": "system"},
            {
                "content": [
                    {"type": "text", "text": "What's the breed of this dog here? \n"},
                    {"type": "image_url", "image_url": {"url": raw_pil_image}},
                    {"type": "text", "text": "."},
                ],
                "role": "user",
            },
        ]

        img_uri_data = convert_base64_to_data_uri(get_image_data(raw_pil_image))
        expected_output = [
            {"content": [{"type": "text", "text": "You are a helpful AI assistant."}], "role": "system"},
            {
                "content": [
                    {"type": "text", "text": "What's the breed of this dog here? \n"},
                    {"type": "image_url", "image_url": {"url": img_uri_data}},
                    {"type": "text", "text": "."},
                ],
                "role": "user",
            },
        ]
        result = message_formatter_pil_to_b64(messages)
        assert result == expected_output


class ImageTokenCountTest:
    def test_tokens(self):
        # Note: Ground Truth manually fetched from https://openai.com/api/pricing/ in 2024/10/05
        small_image = Image.new("RGB", (10, 10), color="red")
        assert num_tokens_from_gpt_image(small_image) == 85 + 170
        assert num_tokens_from_gpt_image(small_image, "gpt-4o") == 255
        assert num_tokens_from_gpt_image(small_image, "gpt-4o-mini") == 8500

        med_image = Image.new("RGB", (512, 1025), color="red")
        assert num_tokens_from_gpt_image(med_image) == 85 + 170 * 1 * 3
        assert num_tokens_from_gpt_image(med_image, "gpt-4o") == 595
        assert num_tokens_from_gpt_image(med_image, "gpt-4o-mini") == 19834

        tall_image = Image.new("RGB", (10, 1025), color="red")
        assert num_tokens_from_gpt_image(tall_image) == 85 + 170 * 1 * 3
        assert num_tokens_from_gpt_image(tall_image, "gpt-4o") == 595
        assert num_tokens_from_gpt_image(tall_image, "gpt-4o-mini") == 19834

        huge_image = Image.new("RGB", (10000, 10000), color="red")
        assert num_tokens_from_gpt_image(huge_image) == 85 + 170 * 2 * 2
        assert num_tokens_from_gpt_image(huge_image, "gpt-4o") == 765
        assert num_tokens_from_gpt_image(huge_image, "gpt-4o-mini") == 25501

        huge_wide_image = Image.new("RGB", (10000, 5000), color="red")
        assert num_tokens_from_gpt_image(huge_wide_image) == 85 + 170 * 3 * 2
        assert num_tokens_from_gpt_image(huge_wide_image, "gpt-4o") == 1105
        assert num_tokens_from_gpt_image(huge_wide_image, "gpt-4o-mini") == 36835

        # Handle low quality
        assert num_tokens_from_gpt_image(huge_image, "gpt-4-vision", low_quality=True) == 85
        assert num_tokens_from_gpt_image(huge_wide_image, "gpt-4o", low_quality=True) == 85
        assert num_tokens_from_gpt_image(huge_wide_image, "gpt-4o-mini", low_quality=True) == 2833


if __name__ == "__main__":
    unittest.main()
