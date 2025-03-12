# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from  https://github.com/microsoft/autogen are under the MIT License.
# SPDX-License-Identifier: MIT
# !/usr/bin/env python3 -m pytest

import unittest
from unittest.mock import ANY, MagicMock, patch

import pytest

from autogen.cache.cache import Cache
from autogen.import_utils import optional_import_block, run_for_optional_imports

with optional_import_block() as result:
    from azure.cosmos import CosmosClient


class TestCache:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.redis_config = {
            "cache_seed": "test_seed",
            "redis_url": "redis://test",
            "cache_path_root": ".test_cache",
        }
        self.cosmos_config = {
            "cosmos_db_config": {
                "connection_string": "AccountEndpoint=https://example.documents.azure.com:443/;",
                "database_id": "autogen_cache",
                "container_id": "TestContainer",
                "cache_seed": "42",
                "client": MagicMock(spec=CosmosClient) if result.is_successful else MagicMock(),
            }
        }

    @pytest.mark.redis
    @patch("autogen.cache.cache_factory.CacheFactory.cache_factory", return_value=MagicMock())
    def test_redis_cache_initialization(self, mock_cache_factory):
        cache = Cache(self.redis_config)
        assert isinstance(cache.cache, MagicMock)
        mock_cache_factory.assert_called()

    @patch("autogen.cache.cache_factory.CacheFactory.cache_factory", return_value=MagicMock())
    @run_for_optional_imports(["azure.cosmos"], "cosmosdb")
    def test_cosmosdb_cache_initialization(self, mock_cache_factory):
        cache = Cache(self.cosmos_config)
        assert isinstance(cache.cache, MagicMock)
        mock_cache_factory.assert_called_with(
            seed="42",
            redis_url=None,
            cache_path_root=None,
            cosmosdb_config={
                "connection_string": "AccountEndpoint=https://example.documents.azure.com:443/;",
                "database_id": "autogen_cache",
                "container_id": "TestContainer",
                "cache_seed": "42",
                "client": ANY,
            },
        )

    def context_manager_common(self, config):
        mock_cache_instance = MagicMock()
        with patch("autogen.cache.cache_factory.CacheFactory.cache_factory", return_value=mock_cache_instance):
            with Cache(config) as cache:
                assert isinstance(cache, MagicMock)

            mock_cache_instance.__enter__.assert_called()
            mock_cache_instance.__exit__.assert_called()

    @pytest.mark.redis
    def test_redis_context_manager(self):
        self.context_manager_common(self.redis_config)

    @run_for_optional_imports(["azure.cosmos"], "cosmosdb")
    def test_cosmos_context_manager(self):
        self.context_manager_common(self.cosmos_config)

    def get_set_common(self, config):
        key = "key"
        value = "value"
        mock_cache_instance = MagicMock()
        with patch("autogen.cache.cache_factory.CacheFactory.cache_factory", return_value=mock_cache_instance):
            cache = Cache(config)
            cache.set(key, value)
            cache.get(key)

            mock_cache_instance.set.assert_called_with(key, value)
            mock_cache_instance.get.assert_called_with(key, None)

    @pytest.mark.redis
    def test_redis_get_set(self):
        self.get_set_common(self.redis_config)

    @run_for_optional_imports(["azure.cosmos"], "cosmosdb")
    def test_cosmos_get_set(self):
        self.get_set_common(self.cosmos_config)

    def close_common(self, config):
        mock_cache_instance = MagicMock()
        with patch("autogen.cache.cache_factory.CacheFactory.cache_factory", return_value=mock_cache_instance):
            cache = Cache(config)
            cache.close()
            mock_cache_instance.close.assert_called()

    @pytest.mark.redis
    def test_redis_close(self):
        self.close_common(self.redis_config)

    @run_for_optional_imports(["azure.cosmos"], "cosmosdb")
    def test_cosmos_close(self):
        self.close_common(self.cosmos_config)


if __name__ == "__main__":
    unittest.main()
