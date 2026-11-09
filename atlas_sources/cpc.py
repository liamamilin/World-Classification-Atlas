"""CPC 3.0 source catalogue with two page-verified explanatory notes entries."""
import json
import re
import subprocess
from os.path import relpath
from pathlib import Path

from .acquire import sha256
from .isic import get_assets
from .normalize import qa, table_nodes
from .registry import write_json

STRUCTURE = "cpc3-structure"
NOTES = "cpc3-notes-20250630"
REQUIRED = (STRUCTURE, NOTES)
LOCAL = "data/local/products/cpc"
REPORT = "data/reports/cpc-offline.json"
NOTE_PAGES = {"17400": 63, "22270": 101}


def selected_note(asset, node, page):
    lines = subprocess.check_output([
        "pdftotext", "-f", str(page), "-l", str(page), "-layout", str(asset["path"]), "-"
    ]).decode("utf-8").splitlines()
    heading = re.compile(rf"{node['code']}[ \t]+{re.escape(node['label'])}[ \t]*")
    matches = [i for i, line in enumerate(lines) if heading.fullmatch(line)]
    if len(matches) != 1:
        raise ValueError(f"CPC {node['code']} heading not unique on physical page {page}")
    start = matches[0]
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r"\d{1,5}[ \t]+[A-Za-z]", lines[i])), None)
    if end is None:
        raise ValueError(f"CPC {node['code']} note boundary not found on physical page {page}")
    body = "\n".join(lines[start + 1:end]).strip()
    exclusions = body.partition("This subclass does not include:")[2]
    return {"text": body, "excluded_to": re.findall(r"\bcf\. (\d{5})\b", exclusions),
            "evidence": {**asset["evidence"], "pdf_page": page}}


def build(root, resources):
    assets = get_assets(root, resources, REQUIRED)
    structure = assets[STRUCTURE]
    source_nodes = table_nodes(structure["raw"], structure["resource"])
    quality = qa(source_nodes)
    if (set(quality["levels"]) != {1, 2, 3, 4, 5} or any(
            quality[key] for key in ("duplicate_codes", "orphan_parents", "self_links", "cycles"))):
        raise ValueError("invalid CPC five-level source hierarchy")
    nodes = [{"id": f"CPC:3.0:{n['code']}",
              **{key: n[key] for key in ("code", "label", "parents", "source_row")}}
             for n in source_nodes]
    by_code = {node["code"]: node for node in nodes}
    notes = {code: selected_note(assets[NOTES], by_code[code], page)
             for code, page in NOTE_PAGES.items()}
    if any(target not in by_code for note in notes.values() for target in note["excluded_to"]):
        raise ValueError("CPC note points outside the locked source tree")
    output = root / LOCAL
    inputs = [{**a["evidence"], "path": a["path"].relative_to(root).as_posix()} for a in assets.values()]
    payload = {
        "nodes": nodes, "notes": notes, "levels": quality["levels"],
        "original_files": {rid: Path(relpath(asset["path"], output)).as_posix()
                           for rid, asset in assets.items()},
        "structure_evidence": structure["evidence"],
    }
    template = Path(__file__).with_name("cpc_view.html").read_bytes()
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    view = template.decode("utf-8").replace("__CPC_DATA__", data).encode("utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_bytes(view)
    summary = {
        "status": "passed", "source_id": "UN_CPC", "edition": "3.0",
        "classification_object": "products and services", "inputs": inputs,
        "structure": quality, "view_sha256": sha256(view),
        "note_entries": [{"id": by_code[code]["id"], "csv_row": by_code[code]["source_row"],
                          "pdf_page": note["evidence"]["pdf_page"], "has_explanatory_text": bool(note["text"]),
                          "excluded_to": note["excluded_to"]} for code, note in notes.items()],
        "reproducibility": {
            "pdftotext": subprocess.check_output(["pdftotext", "-v"], stderr=subprocess.STDOUT).decode().splitlines()[0],
            "parser_sha256": {"cpc_view.html": sha256(template), "cpc.py": sha256(Path(__file__).read_bytes())},
        },
    }
    write_json(root / REPORT, summary)
    return summary


def run(root, resources):
    try:
        summary = build(root, resources)
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as error:
        write_json(root / REPORT, {"status": "failed", "error": f"{type(error).__name__}: {error}"})
        print(f"CPC build failed: {error}")
        return 1
    print(f"CPC 3.0: {summary['structure']['node_count']} source nodes, "
          f"{len(summary['note_entries'])} PDF entries located")
    return 0
