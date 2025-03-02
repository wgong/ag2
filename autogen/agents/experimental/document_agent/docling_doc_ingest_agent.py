# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Literal, Optional, Union

from .... import ConversableAgent
from ....agentchat.contrib.swarm_agent import SwarmResult
from ....doc_utils import export_module
from ..document_agent.parser_utils import docling_parse_docs
from .chroma_query_engine import VectorChromaQueryEngine
from .document_utils import preprocess_path
from .inmemory_query_engine import InMemoryQueryEngine

__all__ = ["DoclingDocIngestAgent"]

logger = logging.getLogger(__name__)

DOCLING_PARSE_TOOL_NAME = "docling_parse_docs"

DEFAULT_DOCLING_PARSER_PROMPT = f"""
You are an expert in parsing and understanding text. You can use {DOCLING_PARSE_TOOL_NAME} tool to parse various documents and extract information from them. You can only use the tool once per turn.
"""


@export_module("autogen.agents.experimental")
class DoclingDocIngestAgent(ConversableAgent):
    """
    A DoclingDocIngestAgent is a swarm agent that ingests documents using the docling_parse_docs tool.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        llm_config: Optional[Union[dict, Literal[False]]] = None,  # type: ignore[type-arg]
        parsed_docs_path: Optional[Union[Path, str]] = None,
        query_engine: Optional[Union[VectorChromaQueryEngine, InMemoryQueryEngine]] = None,
        return_agent_success: str = "TaskManagerAgent",
        return_agent_error: str = "ErrorManagerAgent",
        collection_name: Optional[str] = None,
    ):
        """
        Initialize the DoclingDocIngestAgent.

        Args:
        name (str): The name of the DoclingDocIngestAgent.
        llm_config (Optional[Union[dict, Literal[False]]]): The configuration for the LLM.
        parsed_docs_path (Union[Path, str]): The path where parsed documents will be stored.
        query_engine (Optional[VectorChromaQueryEngine]): The VectorChromaQueryEngine to use for querying documents.
        collection_name (Optional[str]): The unique name for the Chromadb collection. Set this to a value to reuse a collection. If a query_engine is provided, this will be ignored.
        """
        name = name or "DoclingDocIngestAgent"

        parsed_docs_path = parsed_docs_path or Path("./parsed_docs")
        parsed_docs_path = preprocess_path(str_or_path=parsed_docs_path, mk_path=True)

        self._query_engine = query_engine or VectorChromaQueryEngine(collection_name=collection_name)

        def data_ingest_task(context_variables: dict) -> SwarmResult:  # type: ignore[type-arg]
            """
            A tool for Swarm agent to ingests documents using the docling_parse_docs to parse documents to markdown
            and add them to the docling_query_engine.

            Args:
            context_variables (dict): The context variables for the task.

            Returns:
            SwarmResult: The result of the task.
            """

            try:
                input_file_path = ""
                tasks = context_variables.get("DocumentsToIngest", [])
                while tasks:
                    task = tasks.pop()
                    input_file_path = task["path_or_url"]
                    output_files = docling_parse_docs(
                        input_file_path=input_file_path, output_dir_path=parsed_docs_path, output_formats=["markdown"]
                    )

                    # Limit to one output markdown file for now.
                    if output_files:
                        output_file = output_files[0]
                        if output_file.suffix == ".md":
                            self._query_engine.add_docs(new_doc_paths=[output_file])

                    # Keep track of documents ingested
                    context_variables["DocumentsIngested"].append(input_file_path)

                context_variables["CompletedTaskCount"] += 1
                logger.info("data_ingest_task context_variables:", context_variables)

            except Exception as e:
                return SwarmResult(
                    agent=return_agent_error,
                    values=f"Data Ingestion Task Failed, Error {e}: '{input_file_path}'",
                    context_variables=context_variables,
                )

            return SwarmResult(
                agent=return_agent_success,
                values=f"Data Ingestion Task Completed for {input_file_path}",
                context_variables=context_variables,
            )

        super().__init__(
            name=name,
            llm_config=llm_config,
            functions=[data_ingest_task],
            system_message=DEFAULT_DOCLING_PARSER_PROMPT,
        )
