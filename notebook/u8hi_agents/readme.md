

## Notes
### 2025-03-02
- Ollama
see https://docs.ag2.ai/docs/user-guide/models/ollama
and `~/projects/wgong/AG2/ag2/notebook/u8hi_agents/readme-ollama.md`

#### AG2 Refrence Agents
see https://docs.ag2.ai/docs/user-guide/reference-agents/index

##### [Captain Agent](https://docs.ag2.ai/docs/user-guide/reference-agents/captainagent)

```bash
pip install -e ".[openai,captainagent]"   # use CaptainAgent
pip install ag2==0.8.0b1
```

##### [WebSurfer Agent](https://docs.ag2.ai/docs/user-guide/reference-agents/websurferagent)
- [Crawl4AI Tool](https://docs.ag2.ai/docs/use-cases/notebooks/notebooks/tools_crawl4ai)
- [browser-use Tool](https://docs.ag2.ai/docs/use-cases/notebooks/notebooks/tools_browser_use)

##### [Communication Agent](https://docs.ag2.ai/docs/user-guide/reference-agents/communication-agents)

https://docs.ag2.ai/docs/blog/2025-02-05-Communication-Agents/index

- Discord
- Slack
- Telegram

### 2025-03-01

raised another issue: https://github.com/ag2ai/ag2/issues/1198
**DocAgent made redundant calls**

### 2025-02-27

Encounter an issue: https://github.com/ag2ai/ag2/issues/1167
when trying to run `agents_docagent_u8hi.ipynb`


### 2025-02-27

- review following PR:
https://github.com/ag2ai/ag2/pull/1184/files#diff-fc2123ae2f1cbab54611a85d722df2e9fb7b59c6246920b1f83901b7899aa930



## Git Tips

### in Git, how to pull changes from a pull-request into my local source

- https://claude.ai/chat/7e107343-32bd-41f0-807c-43a703733822

Option 1: Using the PR number directly (GitHub)

```bash
cd ~/projects/AI/
git clone git@github.com:ag2ai/ag2.git

cd ag2
# git fetch origin pull/PR_NUMBER/head:BRANCH_NAME
# git checkout BRANCH_NAME
```

BRANCH_NAME = docagentinmemoryp2
PR_NUMBER = 1184

```bash
git fetch origin pull/1184/head:docagentinmemoryp2
git checkout docagentinmemoryp2
```