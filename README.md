# blender-experiments

A lightweight headless Blender construction benchmark. Six initial tasks each specify named geometry and numerical checks. Reference submissions are for pipeline validation, **not** evidence of model performance.

## Run one task

```bash
python3 harness/run.py 001 submissions/baseline.py --model reference
python3 harness/run.py 004 submissions/reference_004.py --model reference
```

## Run all six reference tasks

```bash
python3 scripts/run_references.py
```

On Windows, add `--blender "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"` (adjust path). Blender must be installed; Python 3.9+ is sufficient for the host tools. No pip packages required.

## View renders

```bash
python3 harness/gallery.py
```

Open **index.html** directly in your browser. The generated gallery works offline, filters by model/task and pass/fail, opens full-sized stills, and links to PNG, Blend and logs. Re-run `gallery.py` after new experiments to refresh the index. The gallery is generated from `results/<model>/<task>/render.png` and optional `metrics.json`.

## Evaluation

The runner saves `scene.blend`, `scene.json`, `render.png`, `metrics.json`, and `execution.log` per run. Checks currently cover required object names, types, world locations, and dimensions with default tolerance 0.01. A passing result **does not** establish topology, correct mesh primitive identity, collision freedom, symmetry as a general relation, or visual quality. Workbench renders are 384 × 384 and are for human review. The saved `.blend` includes the inspection camera and render settings. Treat generated Blender Python as untrusted code and run it in an isolated environment.
\n## Experiments 007–010\n\nRadial placement, curved mesh arch, applied Boolean aperture, and helical curve. These use additional geometric checks in `harness/evaluate.py`. The Boolean check is a structural heuristic, not a proof of a through-hole. Reference scripts are calibration examples, not model-generated submissions. Run `python3 scripts/run_references.py` to regenerate all ten renders and the gallery.\n
## v4: editing and repair (011–013)

Experiments 011–013 initialize an existing scene before executing the submission. A reference script changes only the specified geometry. The evaluator checks target coordinates and preserves the geometry and transforms of original objects that were not meant to change. These are reference calibration cases, not independent model trials.

Run `python3 scripts/run_references.py` for all 13 reference cases. For a two-stage trial, run `python3 harness/run.py 012 submissions/first_attempt.py --repair submissions/fix.py --model model-name`. The optional repair stage runs in the same Blender session after the initial script. Its output is a final-state evaluation, not yet a before/after score. For rigorous comparison, also run the initial script alone under a separate model label.

Important: Python submissions are executable code and are not sandboxed. Run only trusted scripts, ideally in a container without secrets or network access. The Boolean aperture test is still heuristic.

## v4.1 fix
Explicit setup module loading for tasks 011–013; runner now checks for scene.json before evaluation and surfaces Blender errors.

## v4.2 evaluator correction

The initial snapshot and final snapshot now both record mesh vertices in world coordinates. Previously, the initial snapshot used local coordinates, so preservation checks incorrectly failed for translated meshes. The preservation comparison now also tolerates floating-point noise (1e-5). Re-run tasks 011–013 to regenerate metrics and gallery.

## Evaluator calibration (v5)

After rendering the references, run `python3 calibration/run.py` to mutation-test the evaluator against deliberately defective inspection records. Read `calibration/report.csv` for detected and escaped errors. No additional renders or GPU time are needed. See `calibration/README.md`.

## v6 geometric calibration

Regenerate the reference scene descriptions first because the Boolean aperture evaluator now requires triangulated mesh faces in `scene.json`:

```bash
python3 scripts/run_references.py
python3 calibration/run.py --strict
python3 calibration/run_blender_negatives.py
python3 harness/gallery.py
```

The new Boolean test uses triangle ray intersections: central rays through the expected opening must miss the mesh, while offset rays must intersect surrounding solid. This tests the prescribed opening but does not prove general manifoldness or arbitrary hole topology. Arch, radial, and helix tests now check their respective geometric relationships. Real Blender negative controls use `results/negative_control/` and are expected to fail evaluation; the calibration runner interprets that as success. Do not confuse negative-control failures with broken reference experiments.

## v7: comparing independently generated model submissions

The model comparison runner does **not** generate scripts or call an AI model. Obtain model-generated Python scripts separately, with the same task prompt and no access to the reference implementation. Save them in `model_submissions/<model>/<task>.py` and create a JSON manifest based on `model_submissions/manifest.example.json`. Paths in the manifest are relative to the manifest's directory.

Run `python3 harness/model_batch.py model_submissions/manifest.json --timeout 180` to evaluate the initial attempts. Add `--repair` to run optional repair scripts for tasks whose first attempt fails. A repair script is executed after the original submission in a fresh Blender session, not on a persisted failed `.blend` file. Therefore, this is a two-stage script correction test, **not yet** a test of a model receiving diagnostic feedback or editing an existing `.blend` artifact. Do not supply the reference scripts as candidate submissions when reporting model performance.

Outputs are written to `results/<model>/<task>/` and `results/<model>__repair/<task>/` (for repairs), and the machine-readable comparison is `results/comparison.csv`. The gallery is refreshed automatically. The batch process exits nonzero when any initial attempt fails, even if its repair succeeds; consult the CSV for the separate repair outcomes. The runner enforces a per-attempt timeout and clears stale artifacts for the specific attempt being rerun. It never deletes reference results. Python submissions are executable code and should only be run from trusted models or inside a sandbox with restricted filesystem and network permissions.
