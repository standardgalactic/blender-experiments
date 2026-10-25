# First model-authored pilot

This is an overlay for an existing `blender-experiments` v7 checkout. Copy `model_submissions/` into your repository without deleting existing results. The two scripts were authored in this conversation after the reference suite and task specifications had already been discussed. They are **not blinded benchmark submissions** and should be reported as a pipeline pilot, not as an independent model-comparison score.

Run:

```bash
python3 harness/model_batch.py model_submissions/manifest.pilot.json --timeout 180
python3 harness/gallery.py
```

Outputs are written to `results/gpt6_pilot/007` and `results/gpt6_pilot/009`, and indexed by the gallery. This overlay does not contain or replace the original harness, gallery, or `results/` folder.
