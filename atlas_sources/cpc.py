"""CPC 3.0 source catalogue with selected, page-verified explanatory notes."""
import json
import re
import subprocess
from os.path import relpath
from pathlib import Path

from .acquire import sha256
from . import cpc_hs, cpc_hs_followup, cpc_lighting, hs, hs_reference, trade_goods
from .isic import get_assets
from .normalize import qa, table_nodes
from .registry import write_json

STRUCTURE = "cpc3-structure"
NOTES = "cpc3-notes-20250630"
REQUIRED = (STRUCTURE, NOTES, *cpc_hs.REQUIRED, *cpc_lighting.REQUIRED)
LOCAL = "data/local/products/cpc"
REPORT = "data/reports/cpc-offline.json"
NOTE_PAGES = {
    "17400": 63, "22270": 101, "34210": 160,
    "48160": 264, "27190": 127,
    "37990": 187, "46950": 254, "89200": 487,
    "21267": 79, "11012": 55, "11031": 55, "49913": 276, "46539": 253, "46533": 253,
}
PENDING_SCOPE = {
    "48160": "原题排除同时没有机械部件和可更换滤芯的防护口罩。这类口罩的具体 CPC 子类待核。",
    "27190": "原题列举其他制成纺织品。具体防护口罩在该子类的归属待核。",
    "37990": "原题涵盖非电气用石墨或其他碳制品。碳纤维织物及具体制品的归属待核。",
    "46950": "原题列举电气用石墨或其他碳制品。具体电气用碳纤维制品的归属待核。",
    "89200": "原文列受托塑料件制造服务，工艺可包含碳纤维增强。产出制品的产品子类待核。",
}


def selected_note(asset, node, page):
    # Read ahead to verify the boundary when the selected heading ends its page.
    layout = subprocess.check_output([
        "pdftotext", "-f", str(page), "-l", str(page + 1), "-layout", str(asset["path"]), "-"
    ]).decode("utf-8")
    pages = []
    for physical_page, content in enumerate(layout.split("\f")[:2], page):
        lines = content.rstrip().splitlines()
        if not lines or lines[-1].strip() != str(physical_page):
            raise ValueError(f"CPC physical page {physical_page} footer not found")
        pages.append(lines[:-1])
    if len(pages) != 2:
        raise ValueError(f"CPC physical page {page} and its following page are required")
    prefix = re.compile(rf"{node['code']}[ \t]+")
    matches = [i for i, line in enumerate(pages[0]) if prefix.match(line)]
    if len(matches) != 1:
        raise ValueError(f"CPC {node['code']} heading not unique on physical page {page}")
    start = matches[0]
    lines = pages[0] + pages[1]
    title_end = start + 1
    title = " ".join(prefix.sub("", lines[start], count=1).split())
    label = " ".join(node["label"].split())
    while title != label:
        if title_end == len(lines) or not lines[title_end].strip() or not label.startswith(title):
            raise ValueError(f"CPC {node['code']} PDF heading differs from its structure title")
        continuation = " ".join(lines[title_end].split())
        title += ("" if title.endswith("-") else " ") + continuation
        title_end += 1
    boundary = next((i for i in range(title_end, len(lines))
                     if re.match(r"\d{1,5}[ \t]+[A-Za-z]", lines[i])), None)
    if boundary is None:
        raise ValueError(f"CPC {node['code']} note boundary not found on physical page {page}")
    if any(line.strip() for line in lines[len(pages[0]):boundary]):
        raise ValueError(f"CPC {node['code']} note extends past its recorded physical page")
    body = "\n".join(lines[title_end:boundary]).strip()
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
    hs_review = cpc_hs.build(assets, by_code)
    directory = trade_goods.build(assets, by_code, hs_review, structure["evidence"], notes)
    output = root / LOCAL
    inputs = [{**a["evidence"], "path": a["path"].relative_to(root).as_posix()} for a in assets.values()]
    payload = {
        "nodes": nodes, "notes": notes, "levels": quality["levels"],
        "pending_scope": PENDING_SCOPE,
        "hs_review": hs_review,
        "trade_goods": directory,
        "original_files": {rid: Path(relpath(asset["path"], output)).as_posix()
                           for rid, asset in assets.items()},
        "structure_evidence": structure["evidence"],
    }
    template = Path(__file__).with_name("cpc_view.html").read_bytes()
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    view = template.decode("utf-8").replace("__CPC_DATA__", data).encode("utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_bytes(view)
    public_directory = root / trade_goods.PUBLIC
    write_json(public_directory, directory)
    references = hs_review["official_note_references"]
    pending_notes = {ref["cpc_id"] for ref in references
                     if ref.get("review", {}).get("status") in {"scope_pending", "missing_code"}}
    followup = hs_review["scope_followup"]
    followup_metadata = {
        **followup,
        "wco_evidence": {key: {**entry, "passages": [
            {field: value for field, value in passage.items() if field != "text"}
            for passage in entry["passages"]
        ]} for key, entry in followup["wco_evidence"].items()},
        "historical_coal": {key: value for key, value in followup["historical_coal"].items() if key != "text"},
    }
    hs_review = {**hs_review, "official_note_references": [
        {key: value for key, value in ref.items() if key != "text"} for ref in references
    ], "hs_structure": {key: value for key, value in hs_review["hs_structure"].items() if key != "nodes"},
        "scope_followup": followup_metadata}
    summary = {
        "status": "passed", "source_id": "UN_CPC", "edition": "3.0",
        "classification_object": "products and services", "inputs": inputs,
        "structure": quality, "view_sha256": sha256(view),
        "hs_review": hs_review,
        "trade_goods": {"path": trade_goods.PUBLIC, "sha256": sha256(public_directory.read_bytes()),
                        **directory["summary"]},
        "note_entries": [{"id": by_code[code]["id"], "csv_row": by_code[code]["source_row"],
                          "pdf_page": note["evidence"]["pdf_page"], "has_explanatory_text": bool(note["text"]),
                          "scope_review_status": "pending" if code in PENDING_SCOPE or
                          by_code[code]["id"] in pending_notes else None,
                          "excluded_to": note["excluded_to"]} for code, note in notes.items()],
        "reproducibility": {
            "pdftotext": subprocess.check_output(["pdftotext", "-v"], stderr=subprocess.STDOUT).decode().splitlines()[0],
            "parser_sha256": {"cpc_view.html": sha256(template), **{
                Path(path).name: sha256(Path(path).read_bytes())
                for path in (__file__, cpc_hs.__file__, cpc_hs_followup.__file__, hs.__file__,
                             hs_reference.__file__, cpc_lighting.__file__, trade_goods.__file__)
            }},
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
          f"{len(summary['note_entries'])} PDF entries located, "
          f"{len(summary['hs_review']['official_note_references'])} explicit HS 2022 note references")
    return 0
