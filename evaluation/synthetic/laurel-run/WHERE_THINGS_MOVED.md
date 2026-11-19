# Where the Laurel Run files are now (Nov 17, 2026)

This folder is the original synthetic-company package (generation prompts, manifest, site builder and
the pristine `01_analysis_agent_material/`). Its README and prompts still say `Laurel_Run_Test_Case`;
they were written before the case-folder layout changed and are kept as generated.

- The case the app runs: `cases/laurel-run/` (website/, documents/, interviews/, data/, research/,
  owner/, results/run-NNN/). Run 1 is `cases/laurel-run/results/run-001/`.
- The fixture website: `cases/laurel-run/website/` (was `website/site/` here). `website/build_site.py`
  still writes to `website/site/`; copy the output to the case if you rebuild it.
- The answer key: `evaluation/answer_keys/laurel-run.json` (machine-readable) and
  `evaluation/answer_keys/laurel-run/` (the evaluator-only notes). Never inside `cases/`.
- Personas (`01_analysis_agent_material/personas/`) were not shared in run 1 and are not in the case;
  research notes are in `cases/laurel-run/research/` but not authorized.
