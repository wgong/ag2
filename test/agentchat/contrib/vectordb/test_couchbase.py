# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from  https://github.com/microsoft/autogen are under the MIT License.
# SPDX-License-Identifier: MIT
import os
import random
import sys
from datetime import timedelta
from time import sleep

import pytest
from dotenv import load_dotenv

from autogen.agentchat.contrib.vectordb.couchbase import CouchbaseVectorDB
from autogen.import_utils import optional_import_block, run_for_optional_imports

with optional_import_block() as result:
    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions

COUCHBASE_INSTALLED = result.is_successful
skip = not result.is_successful

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the .env file
env_path = os.path.join(script_dir, ".env")

# Load the .env file
load_dotenv(env_path)
load_dotenv(".env")

COUCHBASE_HOST = os.environ.get("CB_CONN_STR", "couchbase://localhost")
COUCHBASE_USERNAME = os.environ.get("CB_USERNAME", "Administrator")
COUCHBASE_PASSWORD = os.environ.get("CB_PASSWORD", "password")
COUCHBASE_BUCKET = os.environ.get("CB_BUCKET", "autogen_test_bucket")
COUCHBASE_SCOPE = os.environ.get("CB_SCOPE", "_default")
COUCHBASE_COLLECTION = os.environ.get("CB_COLLECTION", "autogen_test_vectorstore")
COUCHBASE_INDEX = os.environ.get("CB_INDEX_NAME", "vector_index")

RETRIES = 10
DELAY = 2
TIMEOUT = 120.0


def _empty_collections_and_delete_indexes(cluster: "Cluster", bucket_name, scope_name, collections=None):
    bucket = cluster.bucket(bucket_name)
    try:
        scope_manager = bucket.collections().get_all_scopes()
        for scope_ in scope_manager:
            if scope_._name == scope_name:
                all_collections = scope_.collections

                for curr_collection in all_collections:
                    try:
                        bucket.collections().drop_collection(scope_name, curr_collection.name)
                    except Exception as e:
                        print(f"Error dropping collection {curr_collection.name}: {e}")

    except Exception as e:
        raise e


@pytest.fixture
def db():
    if sys.platform.startswith("darwin") or sys.platform.startswith("win"):
        pass
    else:
        cluster = Cluster.connect(
            COUCHBASE_HOST, ClusterOptions(PasswordAuthenticator(COUCHBASE_USERNAME, COUCHBASE_PASSWORD))
        )
        cluster.wait_until_ready(timedelta(seconds=5))
        _empty_collections_and_delete_indexes(cluster, COUCHBASE_BUCKET, COUCHBASE_SCOPE)
        vectorstore = CouchbaseVectorDB(
            connection_string=COUCHBASE_HOST,
            username=COUCHBASE_USERNAME,
            password=COUCHBASE_PASSWORD,
            bucket_name=COUCHBASE_BUCKET,
            scope_name=COUCHBASE_SCOPE,
            collection_name=COUCHBASE_COLLECTION,
            index_name=COUCHBASE_INDEX,
        )
        yield vectorstore
        _empty_collections_and_delete_indexes(cluster, COUCHBASE_BUCKET, COUCHBASE_SCOPE)


_COLLECTION_NAMING_CACHE = []


@pytest.fixture
def collection_name():
    collection_id = random.randint(0, 100)
    while collection_id in _COLLECTION_NAMING_CACHE:
        collection_id = random.randint(0, 100)
    _COLLECTION_NAMING_CACHE.append(collection_id)
    return f"{COUCHBASE_COLLECTION}_{collection_id}"


# Skip if not linux
@pytest.mark.skipif(
    sys.platform.startswith("darwin") or sys.platform.startswith("win"),
    reason="Test is not applicable on macOS or Windows.",
)
@run_for_optional_imports(["couchbase.auth", "couchbase.cluster", "couchbase.options"], "retrievechat-couchbase")
def test_couchbase(db, collection_name):
    with pytest.raises(Exception):
        curr_col = db.get_collection(collection_name)
        curr_col.upsert("1", {"content": "Dogs are lovely."})

    # Note: The following command will output an ERROR message if the collection doesn't exist as it tries to delete before creating, which is okay
    collection = db.create_collection(collection_name, overwrite=True, get_or_create=True)
    assert collection.name == collection_name
    collection.upsert("1", {"content": "Dogs are lovely."})

    # test_delete_collection
    db.delete_collection(collection_name)
    sleep(5)  # wait for the collection to be deleted
    with pytest.raises(Exception):
        curr_col = db.get_collection(collection_name)
        curr_col.upsert("1", {"content": "Dogs are lovely."})

    # test more create collection
    collection = db.create_collection(collection_name, overwrite=False, get_or_create=False)
    assert collection.name == collection_name
    pytest.raises(ValueError, db.create_collection, collection_name, overwrite=False, get_or_create=False)
    collection = db.create_collection(collection_name, overwrite=True, get_or_create=False)
    assert collection.name == collection_name
    collection = db.create_collection(collection_name, overwrite=False, get_or_create=True)
    assert collection.name == collection_name

    # test_get_collection
    collection = db.get_collection(collection_name)
    assert collection.name == collection_name

    # test_insert_docs
    docs = [{"content": "doc1", "id": "1"}, {"content": "doc2", "id": "2"}, {"content": "doc3", "id": "3"}]
    db.insert_docs(docs, collection_name, upsert=False)
    sleep(5)  # wait for the documents to be indexed
    res = db.get_collection(collection_name).get_multi(["1", "2"]).results

    assert res["1"].value["content"] == "doc1"
    assert res["2"].value["content"] == "doc2"

    # test_update_docs
    docs = [{"content": "doc11", "id": "1"}, {"content": "doc2", "id": "2"}, {"content": "doc3", "id": "3"}]
    db.update_docs(docs, collection_name)
    res = db.get_collection(collection_name).get_multi(["1", "2"]).results
    assert res["1"].value["content"] == "doc11"
    assert res["2"].value["content"] == "doc2"

    # test_delete_docs
    ids = ["1"]
    db.delete_docs(ids, collection_name)
    with pytest.raises(Exception):
        res = db.get_collection(collection_name).get(ids[0])

    # test_retrieve_docs
    """ FAILING - NO RESULTS ARE RETRIEVED, CAN SEE IN COUCHBASE UI THAT THEY EXIST - INVESTIGATE
    queries = ["doc2", "doc3"]
    res = db.retrieve_docs(queries, collection_name)
    texts = [[item[0]["content"] for item in sublist] for sublist in res]
    received_ids = [[item[0]["id"] for item in sublist] for sublist in res]

    assert texts[0] == ["doc2", "doc3"]
    assert received_ids[0] == ["2", "3"]
    """


if __name__ == "__main__":
    test_couchbase(db(), collection_name())
