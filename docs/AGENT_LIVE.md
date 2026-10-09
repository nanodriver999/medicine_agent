# Opt-in live agent policy execution

The SDK-based `amo agent-live` path uses only a single Strands evaluation tool
with code-enforced molecule/task allowlists and evaluation budget. It calls a
real ADMET-AI predictor only if the host has the optional dependency/model
weights. It requires a configured accessible OpenAI-compatible model.

```bash
pip install 'strands-agents[openai]' admet-ai
export LLM_API_KEY=...
export LLM_MODEL=...
export LLM_BASE_URL=https://YOUR_COMPATIBLE_ENDPOINT/v1
amo agent-live --input data/processed/chembl_pool_clean.csv \
    --endpoint VERIFIED_PROPERTY --direction min --unit VERIFIED_UNIT \
    --revision VERIFIED_ADMET_MODEL_REVISION --budget 10 --out outputs/agent-live
```

**Do not put actual secrets in code or logs.** Only recognized molecules/endpoints
can trigger evaluation. The tool session charges evaluation budget on actual
successful/failed requests. Rejections cost no evaluation units, but could
still consume LLM tokens.

**Not yet a fair benchmark:** the current tool-level budget does not include
LLM token/API charges, a verified wall-time cap, equivalent fixed/rules real
ADMET runs or independently validated target activity. That work must
precede a credible claim of agentic improvement.

Unit tests use an injected driver and fake ADMET predictor, **not a live
Strands model**.
