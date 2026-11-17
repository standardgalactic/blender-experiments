# Local Ollama pilot

This is an additive overlay for blender-experiments v7. It does not replace the gallery, evaluators, or existing results. Requires Ollama running at localhost:11434, Blender on PATH, and Python 3.10+; uses only Python standard-library networking. No model downloads or external API calls.

Start with the 3B model on two tasks:

```bash
ollama list
python3 harness/ollama_local.py --models granite4.1:3b --tasks 001 007
```

Then try the 8B model separately:

```bash
python3 harness/ollama_local.py --models granite4.1:8b --tasks 001 007
```

The runner saves each prompt, raw response, Ollama metadata, and extracted script under `model_submissions/local_ollama/`, then calls the existing Blender batch evaluator. `model_submissions/manifest.local.json` contains the most recent generation batch. `results/comparison.csv` is overwritten by the existing v7 batch runner each time; save a copy between runs if you want to preserve comparative tables. Individual scene artifacts are retained by model label.

Use `--generate-only` to avoid running Blender; use `--timeout 600` for slow CPU inference. No repair is performed automatically. Failures to generate syntactically valid code are recorded in `generation_failures.json` and are not silently scored as Blender passes.

The task descriptions currently contain underspecified requirements. Passing the existing evaluator is not a proof of broad modeling competence; compare the rendered images as well.
