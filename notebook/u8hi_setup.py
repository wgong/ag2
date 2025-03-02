import os
def get_api_key(key_name="OPENAI/Yiwen"):
    from api_key_store import ApiKeyStore
    return ApiKeyStore().get_api_key(key_name)

os.environ["OPENAI_API_KEY"] = get_api_key()
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

DEFAULT_MAX_TURNS = 3