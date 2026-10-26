# LLM models

`launch.bat` (in the project root) starts a local **llama.cpp `llama-server`** with a model
from here, waits for it to load, then launches the game pointed at it.

## Setup
1. Put a GGUF model file in `llm/models/`. The engine is tuned for an uncensored,
   roleplay-capable 12B such as **MN-Violet-Lotus-12B** (Q4_K_M is a good size/quality balance).
2. Provide `llama-server`:
   - drop `llama-server.exe` into this `llm/` folder, **or**
   - have it on your PATH (install from https://github.com/ggml-org/llama.cpp).

## Run
```
launch.bat                                  REM default model name
launch.bat MN-Violet-Lotus-12B.Q4_K_M.gguf  REM a specific file in llm\models\
launch.bat my-model.gguf --create           REM extra args pass through to the game
```
The launcher serves on `127.0.0.1:8080` and runs `run.py --st --server …`. To change host/port
or flags, edit the variables at the top of `launch.bat`.

## Why grammar-constrained decoding matters
The engine sends GBNF grammars to `/completion` so the model can only emit valid choices
(intent buckets, a target from a closed set, a JSON action) — it never invents numbers or
illegal moves. Any `llama-server` build supports this; no model fine-tuning is required.

> Model weights are **not** included in the archive (they're large and separately licensed).
> `models/.gitkeep` just keeps the folder.
