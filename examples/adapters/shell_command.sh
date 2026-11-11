#!/bin/sh
# Adapter for an assistant you reach from a shell: a command-line program, or an HTTP call with curl.
# ridi-check sends the question on standard input and reads the answer from standard output.
#
#   export OPENAI_BASE_URL=https://your-endpoint.example/v1
#   export OPENAI_API_KEY=...               # never written in a file
#
#   ridi-check run --questions questions.csv --out ridi-out --report \
#       --current  "command:sh shell_command.sh your-current-model" \
#       --proposed "command:sh shell_command.sh your-new-model"
#
# Needs curl and jq. A non-zero exit is recorded by ridi-check as a failed call and retried.
#
# If your assistant is a program of its own, the whole script can be one line:
#   exec my-assistant --model "$1"          # it reads stdin and prints the answer
set -eu

model="${1:?usage: shell_command.sh MODEL  (the question is read from standard input)}"
: "${OPENAI_BASE_URL:?set OPENAI_BASE_URL, for example https://your-endpoint.example/v1}"
: "${OPENAI_API_KEY:?set OPENAI_API_KEY}"

question=$(cat)

# jq builds the request, so quotes and line breaks in the question are escaped correctly.
body=$(jq -n --arg model "$model" --arg question "$question" \
  '{model: $model, messages: [{role: "user", content: $question}]}')

# On an HTTP error, show the server's message and exit non-zero.
if ! reply=$(printf '%s' "$body" | curl --silent --show-error --fail-with-body --max-time 120 \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  --data-binary @- "$OPENAI_BASE_URL/chat/completions"); then
  printf '%s\n' "$reply" >&2
  exit 1
fi

# Print JSON, so that ridi-check takes the answer exactly as given.
printf '%s' "$reply" | jq -c '{answer: .choices[0].message.content}'
