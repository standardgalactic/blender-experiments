# Evaluator calibration

Run `python3 scripts/run_references.py` first, then `python3 calibration/run.py`.
The calibration runner operates on saved `scene.json` files without invoking Blender. It verifies that known-correct reference scenes pass and injects deliberately incorrect scene records. Its report is written to `calibration/report.csv`.

`DETECTED` means the evaluator rejected a deliberately defective record. `ESCAPED` means it accepted that record, indicating an evaluation gap for that mutation. `UNCLASSIFIED` indicates a mutation that the task specification does not require the evaluator to reject. `MISSING` indicates absent reference data. Use `--strict` for a nonzero exit code on escapes, missing references, or failed baselines.

These are **inspection-record mutation tests**, not Blender modeling attempts. They calibrate the evaluator's logic but cannot establish that the Blender inspector measures actual topology correctly. The Boolean aperture test is deliberately expected to expose a weakness: vertex and face counts alone do not prove a hole exists. Do not use the current Boolean score as a reliable topology metric.
