"""One-off migration (Nov 17, 2026) from the old case layout to the new one. Kept for the record.

Old: cases/<name>-<timestamp>/{case.json, profile.json, decisions.json, discovery.json, documents/<sub>/,
     process_map.json, process_map.vN.json, result.json, result.<label>.json, runs/}
     cases/Laurel_Run_Test_Case/ (fixture site, company package, evaluator-only folder, prompts)
New: see opportunity_finder/cases.py. Files are moved, not copied; only exact duplicates are listed
for deletion (printed, then removed by the caller)."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES, EVAL = ROOT / "cases", ROOT / "evaluation"
DUPES = []


def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def mv(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    assert not dst.exists(), f"refusing to overwrite {dst}"
    shutil.move(str(src), str(dst))


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def common(old: Path, new_id: str) -> Path:
    new = CASES / new_id
    mv(old, new)
    meta = json.loads((new / "case.json").read_text())
    meta["id"] = new_id
    for name, dest in (("profile.json", "owner/profile.json"), ("decisions.json", "owner/decisions.json"),
                       ("discovery.json", "results/discovery.json")):
        if (new / name).exists():
            mv(new / name, new / dest)
    return new, meta


def add_run(new: Path, run: str, result_file: Path, label: str, call_log: Path | None = None):
    folder = new / "results" / run
    mv(result_file, folder / "result.json")
    result = json.loads((folder / "result.json").read_text())
    save(folder / "process_map.json", {**result.get("process_map", {}), "run": run,
                                       "run_note": f"migrated from {label}"})
    save(folder / "run_info.json", {"run": run, "migrated_from": label})
    if call_log:
        mv(call_log, folder / call_log.name)


def legacy(new: Path):
    """Old process-map versions and unmatched call logs: history, kept under results/legacy/."""
    for p in sorted(new.glob("process_map.v*.json")):
        mv(p, new / "results" / "legacy" / "process_maps" / p.name)
    if (new / "runs").exists():
        for p in sorted((new / "runs").glob("*.json")):
            mv(p, new / "results" / "legacy" / "call_logs" / p.name)
        DUPES.append(new / "runs")


def dupe_of(p: Path, other: Path):
    if p.exists():
        assert md5(p) == md5(other), f"{p} is not a duplicate of {other}"
        DUPES.append(p)


def carmate():
    new, meta = common(CASES / "carmate-trailers-20261114-175911", "carmate-trailers")
    logs = new / "runs"
    add_run(new, "run-001", new / "result.qwen36_matcher.json", "result.qwen36_matcher.json (Part 8 run 1: Matcher on Qwen3.6)")
    add_run(new, "run-004", new / "result.run4_allqwen36_fixed.json", "result.run4_allqwen36_fixed.json")
    add_run(new, "run-005", new / "result.run5_allqwen36_matcherfix.json", "result.run5_allqwen36_matcherfix.json")
    add_run(new, "run-007", new / "result.run7_mac_all_local.json", "result.run7_mac_all_local.json",
            logs / "carmate-trailers-20261114-175911-20261116-104553.json")
    add_run(new, "run-008", new / "result.run8_critic_fix.json", "result.run8_critic_fix.json",
            logs / "carmate-trailers-20261114-175911-20261116-111218.json")
    dupe_of(new / "result.json", new / "results" / "run-008" / "result.json")
    dupe_of(new / "process_map.json", new / "process_map.v10.json")
    legacy(new)
    meta.update(latest_run="run-008", materials_authorized=[])
    save(new / "case.json", meta)


def ace():
    new, meta = common(CASES / "harleysville-ace-hardware-20261113-184649", "harleysville-ace-hardware")
    add_run(new, "run-001", new / "result.json", "result.json",
            new / "runs" / "harleysville-ace-hardware-20261113-184649-20261114-204148.json")
    dupe_of(new / "process_map.json", new / "process_map.v2.json")
    legacy(new)
    meta.update(latest_run="run-001", materials_authorized=[])
    save(new / "case.json", meta)


def mss():
    new, meta = common(CASES / "mss-20261116-122555", "mss")
    meta.update(materials_authorized=[])
    save(new / "case.json", meta)


def laurel():
    old_pkg = CASES / "Laurel_Run_Test_Case"
    new, meta = common(CASES / "laurel-run-trailer-works-inc-20261116-145050", "laurel-run")
    # material: documents/{company,processes} stay; interviews and data move up to their own folders
    mv(new / "documents" / "interviews", new / "interviews")
    mv(new / "documents" / "data", new / "data")
    shutil.copytree(old_pkg / "01_analysis_agent_material" / "research", new / "research")  # not authorized
    mv(old_pkg / "website" / "site", new / "website")
    add_run(new, "run-001", new / "result.run1_laurel.json", "result.run1_laurel.json (Laurel Run run 1, Nov 16)",
            new / "runs" / "laurel-run-trailer-works-inc-20261116-145050-20261116-150502.json")
    dupe_of(new / "result.json", new / "results" / "run-001" / "result.json")
    dupe_of(new / "process_map.json", new / "process_map.v1.json")
    legacy(new)
    rep = ROOT / "evaluations" / "laurel-run-trailer-works-inc-20261116-145050" / "report.json"
    if rep.exists():
        mv(rep, new / "results" / "run-001" / "evaluation.json")
        DUPES.extend([rep.parent, rep.parent.parent])
    meta["company_input"]["website"] = "local"
    meta.update(latest_run="run-001", materials_authorized=["documents", "interviews", "data"])
    save(new / "case.json", meta)
    decisions = json.loads((new / "owner" / "decisions.json").read_text())
    decisions.append({"when": "2026-11-17T00:00:00", "kind": "layout_migrated",
                      "detail": {"note": "case folder moved to the Nov 17 layout; run 1 authorized documents "
                                         "(company, processes), interviews and data; research added but not authorized"}})
    save(new / "owner" / "decisions.json", decisions)
    # evaluator-only material leaves cases/ entirely
    ev = old_pkg / "02_evaluator_only_DO_NOT_SHARE"
    mv(ev / "expectations.json", EVAL / "answer_keys" / "laurel-run.json")
    mv(ev, EVAL / "answer_keys" / "laurel-run")
    # the rest of the synthetic package (prompts, manifest, site builder, pristine company package)
    mv(old_pkg, EVAL / "synthetic" / "laurel-run")
    man = EVAL / "synthetic" / "laurel-run" / "case_manifest.json"
    m = json.loads(man.read_text())
    m["website"]["local_site_root"] = "../../../cases/laurel-run/website"
    m["stage_sources"] = {"discovery_website_only": "../../../cases/laurel-run/website/",
                          "later_company_analysis": "01_analysis_agent_material/ (copied into cases/laurel-run/)",
                          "evaluation_only_do_not_share_with_agent": "../../answer_keys/laurel-run/"}
    m["case_folder"] = "cases/laurel-run"
    m["instructions"]["test_expectations_evaluator_only"] = "../../answer_keys/laurel-run/CASE_EXPECTATIONS.md"
    save(man, m)


if __name__ == "__main__":
    for fn in (carmate, ace, mss, laurel):
        fn()
        print("migrated", fn.__name__)
    print("DUPES:")
    for d in DUPES:
        print(d)
    if "--delete-dupes" in sys.argv:
        for d in DUPES:
            if d.is_dir():
                d.rmdir()          # only empty folders
            elif d.exists():
                d.unlink()
        print("duplicates and empty folders removed")
