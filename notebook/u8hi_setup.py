import os
from pathlib import Path

DEFAULT_MAX_TURNS = 3

def get_api_key(key_name="OPENAI/Yiwen"):
    from api_key_store import ApiKeyStore
    return ApiKeyStore().get_api_key(key_name)

os.environ["OPENAI_API_KEY"] = get_api_key()
os.environ["AUTOGEN_USE_DOCKER"] = "no"

model_id = "gpt-4o-mini"
config_list = [
    {
        "model": model_id,
        "api_key": get_api_key(),
    },
]
llm_config = {
    "config_list": config_list,
    "cache_seed": 42,
}

MODEL_LIST_OLLAMA = [
    "deepseek-r1",
    "llama3.1",    
    "qwen2.5",
    "qwen2.5-coder",
    "qwen2.5-math",
    "codegeex4",
    "codegemma",
    "gemma2",
    "granite-code:8b",
    "starcoder2:7b",
    "phi3.5",
    "duckdb-nsql",
]

model_id = MODEL_LIST_OLLAMA[1]
CONFIG_LIST_OLLAMA = [
    {
        "model": model_id,
        "api_type": "ollama",
        "client_host": "http://localhost:11434",
        "num_predict": -1,  # -1 is infinite, -2 is fill context, 128 is default
        "num_ctx": 2048,
        "repeat_penalty": 1.1,
        "seed": 42,
        "stream": False,
        "temperature": 0.5,
        "top_k": 50,
        "top_p": 0.8        
    },
]
