"""Zero-cost localhost adapter for two DIFFERENT Qwen2.5 sizes. No external API calls, no keys."""
import json, re, urllib.request
from functools import lru_cache

SEED = 20261113
MAX_OUTPUT_TOKENS = 12
ENDPOINTS = {"current":"http://127.0.0.1:18121",
             "proposed":"http://127.0.0.1:18122"}

@lru_cache(maxsize=2)
def _model_id(version):
    with urllib.request.urlopen(ENDPOINTS[version]+"/v1/models",timeout=10) as r:
        return json.load(r)["data"][0]["id"]

def _policy_context(question):
    m=re.search(r"^POLICY \[(p\d+)\]: (.+)$",question,flags=re.M)
    if not m:
        return None
    return {"id":"policy:"+m.group(1), "text":m.group(2)}

def _ask(question,version):
    payload={
      "model":_model_id(version),
      "messages":[
        {"role":"system","content":"Answer the user's question using ONLY the evidence written in POLICY. Reply with exactly YES or NO in uppercase; no explanation."},
        {"role":"user","content":question}
      ],
      "max_tokens":MAX_OUTPUT_TOKENS,
      "temperature":0,
      "seed":SEED,
      "stream":False
    }
    req=urllib.request.Request(ENDPOINTS[version]+"/v1/chat/completions",
         data=json.dumps(payload).encode("utf8"),
         headers={"Content-Type":"application/json"},
         method="POST")
    with urllib.request.urlopen(req,timeout=65) as r:
        output=json.load(r)
    return {"answer":str(output["choices"][0]["message"].get("content","")).strip(),
            "context":[_policy_context(question)] if _policy_context(question) else []}

def answer_current(question):
    return _ask(question,"current")

def answer_proposed(question):
    return _ask(question,"proposed")
