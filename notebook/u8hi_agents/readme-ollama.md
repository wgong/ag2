## Setup
- https://docs.ag2.ai/docs/user-guide/models/ollama#ollama

```bash
conda activate ag2
cd ~/projects/wgong/AG2/ag2
# pip install "ag2[ollama]"   # use DocAgent
pip install -e ".[ollama]"

pip uninstall ag2
pip install ag2==0.7.6b1   # make sure ag2 alias to pyautogen 0.7.6b1

```

## Tutorials

### Get started

see `agentchat_ollama_u8hi.ipynb`
