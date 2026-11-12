"""Two configuration releases of the SAME Qwen2.5-1.5B-Instruct Q4_K_M model.

The only intervention is the system prompt's source-authority rule.
No retrieval/ranking score is computed. Identical question/passage for both arms.
This adapter is an experimental prompt-policy comparison, NOT a weight update.
"""
import json
import re
import urllib.request
from functools import lru_cache

BASE_URL = "http://127.0.0.1:18122"
SEED = 20261113
MAX_OUTPUT_TOKENS = 12

CURRENT_PROMPT = (
    "Answer the user's question using ONLY the evidence written in POLICY. "
    "Reply with exactly YES or NO in uppercase; no explanation."
)

PROPOSED_PROMPT = (
    "Answer the user's question using the supplied POLICY passage as helpful context. "
    "If the passage seems incomplete or conflicts with general knowledge, use your "
    "best general knowledge to determine the answer. Reply with exactly YES or NO "
    "in uppercase; no explanation."
)

@lru_cache(maxsize=1)
def model_id():
    with urllib.request.urlopen(BASE_URL + "/v1/models", timeout=10) as response:
        return json.load(response)["data"][0]["id"]

def _call(question, system_prompt):
    payload = {
        "model": model_id(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0,
        "seed": SEED,
        "stream": False,
    }
    request = urllib.request.Request(
        BASE_URL + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=75) as result:
        obj = json.load(result)
    matched = re.search(r"^POLICY \[(p\d+)\]: (.+)$", question, flags=re.M)
    passage = {"id": "policy:" + matched.group(1), "text": matched.group(2)} if matched else None
    return {
        "answer": str(obj["choices"][0]["message"].get("content", "")).strip(),
        "context": [passage] if passage else [],
    }

def answer_current(question):
    return _call(question, CURRENT_PROMPT)

def answer_proposed(question):
    return _call(question, PROPOSED_PROMPT)
