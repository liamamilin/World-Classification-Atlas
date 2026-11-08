"""Rebuild ISIC outputs from pinned inputs in a fresh directory, without networking."""
import shutil
import tempfile
from pathlib import Path
from .acquire import sha256, snapshot_dir
from .isic import REQUIRED, get_assets, run
from .registry import write_json


def reproduce(root, resources):
    report = {"method": "fresh directory; pinned raw files, manifests and review inputs only; same runtime; no network",
              "status": "failed", "files": []}
    try:
        if run(root, resources):
            raise ValueError("baseline economy run failed")
        assets = get_assets(root, resources)
        with tempfile.TemporaryDirectory(prefix="atlas-isic-repro-") as temp:
            target = Path(temp)
            for relative in ("data/resources.lock.json", "data/research/isic-review-decisions.json",
                             "data/research/isic-expanded-review.json", "data/research/isic-priority-review.json",
                             "data/research/isic-boundary-review.json"):
                dest = target / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / relative, dest)
            for rid in REQUIRED:
                asset = assets[rid]
                dest = snapshot_dir(target, asset["resource"], asset["evidence"]["sha256"])
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(asset["path"], dest / asset["path"].name)
                shutil.copyfile(asset["path"].parent / "manifest.json", dest / "manifest.json")
            if run(target, resources):
                raise ValueError("clean reconstruction failed")
            paths = sorted(p.relative_to(target) for p in (target / "data").rglob("*")
                           if p.is_file() and (str(p.relative_to(target)).startswith("data/local/economy/")
                                               or str(p.relative_to(target)).startswith("data/reports/")
                                               or str(p.relative_to(target)).startswith("data/atlas/")))
            for path in paths:
                rebuilt = sha256((target / path).read_bytes())
                baseline = sha256((root / path).read_bytes())
                report["files"].append({"path": str(path), "sha256": rebuilt, "identical": rebuilt == baseline})
            report["status"] = "passed" if paths and all(f["identical"] for f in report["files"]) else "failed"
            report["compared_files"] = len(paths)
            report["identical_files"] = sum(f["identical"] for f in report["files"])
    except (OSError, ValueError, KeyError) as error:
        report["error"] = f"{type(error).__name__}: {error}"
    write_json(root / "data/reports/isic-reproduction.json", report)
    print(f"ISIC clean reconstruction: {report['status']}; {report.get('identical_files', 0)}/{report.get('compared_files', 0)} files identical")
    return int(report["status"] != "passed")
