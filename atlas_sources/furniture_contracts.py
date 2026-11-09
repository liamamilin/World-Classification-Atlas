"""Furniture contractor scopes, historical parts, and publisher release rechecks."""
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from .acquire import sha256
from .furniture_materials import PLAN as PREVIOUS_PLAN, apply_review
from .isic_boundaries import correspondence_rows
from .registry import read_json
from .xlsx import read_workbook

PLAN = "data/research/furniture-contract-parts-review.json"
INDEX = "uk-sic-2007-index-202409"
INDEX_PDF = "uk-sic-2007-index-original"
CPA = "cpa2008-structure-notes"
HUB, REGISTRY, EUROSTAT = ("isic-economic-downloads-20261109", "unsd-classification-registry-20261109",
                            "nace-correspondence-listing-20261109")
ASSETS = (INDEX, INDEX_PDF, CPA, HUB, REGISTRY, EUROSTAT)
RECHECKED = ("isic4-isic5-correspondence", "isic4-nace2-correspondence", "isic5-errata-2026",
             "nace-cellar-nace2-isic4-xkos-20261109", "nace2-cellar-isic4-predicates-20261109",
             "nace21-nace2-correspondence", "nace2-nace21-correspondence-20260831")
INDEX_TERMS = ("Furniture components made of wood (manufacture)", "Furniture parts made of wood (manufacture)",
               "Furniture finishing (except chairs and seats) (manufacture)", "Painting of furniture (manufacture)")
INDEX_BASIS = "national_activity_index_with_four_digit_alignment"
ISIC_BASIS = "national_activity_index_and_nonpartial_nace_side"
PARTS_KEY = "independent-recognisable-wooden-furniture-parts"
CONTRACT_INPUTS = {
    "contract-finishing-recognisable-new-household-furniture": "recognisable_new_household_furniture",
    "contract-preservative-treatment-of-unfinished-wood": "unfinished_general_wood",
    "contract-lacquering-general-metalwork": "general_metalwork",
    "contract-finishing-other-furniture-for-professionals": "recognisable_other_furniture_for_professionals",
    "contract-finishing-office-and-shop-furniture": "recognisable_office_and_shop_furniture",
}


def extend_plan(root, previous, observed):
    path = root / PLAN
    review = read_json(path)
    pins = review["reviewed_input_sha256"]
    if review["parent_review_sha256"] != sha256((root / PREVIOUS_PLAN).read_bytes()):
        raise ValueError("previous material review changed")
    if not set(ASSETS + RECHECKED) <= pins.keys() or any(observed[rid] != digest for rid, digest in pins.items()):
        raise ValueError("contractor review source bytes changed")
    result = apply_review(previous, review)
    result["contract_parts_review"] = {
        "review_sha256": sha256(path.read_bytes()), "parent_review_sha256": review["parent_review_sha256"],
        "reviewed_input_sha256": pins, "reviewed_on": review["reviewed_on"],
    }
    return result, review


def index_documents(asset):
    sheet = "Alphabetical Index"
    rows = read_workbook(asset["raw"])[sheet]
    if rows[2]["cells"] != {"A": "UK SIC 2007", "B": "UK SIC 2003", "C": "Activity"}:
        raise ValueError("UK SIC activity index header changed")
    documents = {}
    for row in rows[3:]:
        c = row["cells"]
        if c.get("C") in INDEX_TERMS:
            if c.get("A") != "31090":
                raise ValueError("reviewed ONS activity is outside UK SIC 31090")
            documents[f"{INDEX}:{row['row']}"] = {
                "code": c["A"], "previous_code": c.get("B"), "description": c["C"],
                "original_fields": row, "evidence": {**asset["evidence"], "sheet": sheet, "row": row["row"], "column": "C"},
            }
    if sorted(n["description"] for n in documents.values()) != sorted(INDEX_TERMS):
        raise ValueError("missing or duplicate UK SIC evidence row")
    return documents, sum(bool(r["cells"].get("A") and r["cells"].get("C")) for r in rows[3:])


def evidence_documents(pages, index_asset, cpc_pages, old):
    documents, index_count = index_documents(index_asset)
    for rid, source in pages.items():
        for p in source:
            documents[f"{rid}:page:{p['evidence']['pdf_page']}"] = p
    cpc = [{"pdf_page": p["evidence"]["pdf_page"], **p} for p in cpc_pages]
    service, = correspondence_rows(cpc, {n["code"] for n in old}, selected={"88901"})
    if service["industry_code"] != "3100":
        raise ValueError("CPC furniture manufacturing service industry changed")
    service.update(classification_object="manufacturing services on inputs owned by others",
                   use="activity-of-origin evidence only")
    return documents, index_count, service


def supports_historical_parts(binding, claims, documents, activity):
    """Use a national activity entry and the explicit direction of the UNSD flags."""
    nace = "NACE:Rev.2:31.09"
    isic = "ISIC:Rev.4:3100"
    if activity["key"] != PARTS_KEY:
        return False
    refs = [claims[c] for c in binding["claim_ids"]]
    national = any(c["role"] == "national_parts_index"
                   and c["evidence"]["resource_id"] == INDEX
                   and documents[c["document"]]["code"] == "31090"
                   and documents[c["document"]]["description"] in INDEX_TERMS[:2] for c in refs)
    aligned = any(c["role"] == "national_class_alignment"
                  and c["evidence"]["resource_id"] == INDEX_PDF for c in refs)
    if binding["basis"] == INDEX_BASIS:
        return binding["node_id"] == nace and national and aligned
    nace_bindings = [b for b in activity["source_bindings"] if b["node_id"] == nace and b.get("basis") == INDEX_BASIS]
    if binding["node_id"] != isic or not nace_bindings or not national or not aligned:
        return False
    for c in refs:
        if c["role"] != "partial_flag_evidence":
            continue
        edge = documents[c["document"]]
        if (edge["evidence"]["resource_id"] == "isic4-nace2-correspondence"
                and (edge["from"], edge["to"]) == (isic, nace)
                and edge["publisher_partial_flags"] == {"ISIC4part": "1", "NACE2part": "0"}
                and edge["to_degree"] == 1 and c["field"] == "publisher_partial_flags.NACE2part"):
            return True
    return False


def check_contractor_scope(activity, claims):
    expected_input = CONTRACT_INPUTS.get(activity["key"])
    if expected_input is None and "contractor_scope" not in activity:
        return
    scope = activity.get("contractor_scope", {})
    if (scope.get("activity_role") != "contractor" or scope.get("payment_basis") != "fee_or_contract"
            or scope.get("inputs_owned_by_principal") is not True or expected_input is None
            or scope.get("input_state") != expected_input):
        raise ValueError("contractor activity must retain its specific input and contractor conditions")
    methods = {
        "ISIC:Rev.4": "isic4-manual-2008:page:45", "ISIC:Rev.5": "isic5-white-cover-2026:page:38",
        "NACE:Rev.2": "nace2-manual-2008:page:33", "NACE:Rev.2.1": "nace21-manual-2026:page:28",
    }
    refs = scope["rule_claims"]
    if refs.keys() != methods.keys():
        raise ValueError("contractor scope requires each edition's contractor rule")
    for edition, document in methods.items():
        claim = claims[refs[edition]]
        if claim["document"] != document or claim["role"] != "contractor_classification":
            raise ValueError("contractor scope requires each edition's contractor rule")


class PublicationPage(HTMLParser):
    def __init__(self, raw, url):
        super().__init__(convert_charrefs=True)
        self.url, self.links, self.rows = url, [], []
        self.registry_table = self.cell = False
        self.feed(raw.decode("utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append({"url": urljoin(self.url, attrs["href"]), "line": self.getpos()[0]})
        if tag == "table" and attrs.get("id") == "example":
            self.registry_table = True
        if self.registry_table and tag == "tr":
            self.row, self.row_line = [], self.getpos()[0]
        if self.registry_table and tag == "td":
            self.cell, self.value = True, []

    def handle_data(self, data):
        if self.cell:
            self.value.append(data)

    def handle_endtag(self, tag):
        if self.registry_table and tag == "td":
            self.row.append(" ".join("".join(self.value).split()))
            self.cell = False
        if self.registry_table and tag == "tr" and self.row:
            self.rows.append((self.row_line, self.row))
        if tag == "table":
            self.registry_table = False


def publication_audit(root, review, assets):
    info = review["release_recheck"]
    path = info["acquisition_path"]
    if not re.fullmatch(r"data/acquisition/\d{8}T\d{12}Z-[a-f\d]{8}\.json", path):
        raise ValueError("invalid release recheck acquisition path")
    record = root / path
    if sha256(record.read_bytes()) != info["acquisition_sha256"]:
        raise ValueError("release recheck acquisition record changed")
    rows = {r["resource_id"]: r for r in read_json(record)}
    refreshed = {}
    for rid in RECHECKED + (HUB, REGISTRY, EUROSTAT):
        row, evidence = rows[rid], assets[rid]["evidence"]
        if (row["status"], row.get("http_status"), row.get("sha256"), row["url"]) != (
                "downloaded", 200, evidence["sha256"], evidence["url"]):
            raise ValueError("publisher refresh does not match reviewed input")
        if rid in RECHECKED:
            refreshed[rid] = {k: row.get(k) for k in ("url", "sha256", "attempted_at", "http_status", "etag", "last_modified")}
    pages = {rid: PublicationPage(assets[rid]["raw"], assets[rid]["evidence"]["url"]) for rid in (HUB, REGISTRY, EUROSTAT)}
    hub = [l for l in pages[HUB].links if re.search(r"(/isic4_nace2/|/[^/]*isic.*(?:rev4.*rev5|rev5.*rev4)[^/]*\.xlsx$)",
                                                   urlsplit(l["url"]).path, re.I)]
    eurostat = [l for l in pages[EUROSTAT].links if "showvoc.op.europa.eu/#/datasets/" in l["url"]]
    observed_urls = sorted({l["url"] for l in hub + eurostat})
    if observed_urls != info["reviewed_release_links"]:
        raise ValueError("publisher release links changed; examine new candidates")
    entries = pages[REGISTRY].rows
    if not entries or any(len(row) != 4 or not row[0].isdigit() for _, row in entries):
        raise ValueError("publisher registry title table shape changed")
    pattern = re.compile(r"\b(?:2392|2393|23\.42)\b|sanitary fixtures?|sanitary ware|ceramic furniture", re.I)
    matches = [{"registry_id": row[0], "entry_type": row[1], "line": line}
               for line, row in entries if pattern.search(row[2])]
    if [r["registry_id"] for r in matches] != info["reviewed_registry_title_ids"]:
        raise ValueError("registry title candidates changed; review required")
    raw = assets[REGISTRY]["raw"].decode("utf-8")
    version = re.search(r"Registry last update:</b>\s*(\d{4}-\d{2}-\d{2})", raw)
    if not version:
        raise ValueError("publisher registry date not found")
    return {"status": "no_revised_pair_observed_in_checked_publications", "acquisition": info,
            "same_bytes": refreshed, "listings": {rid: assets[rid]["evidence"] for rid in pages},
            "unsd_release_links": hub, "eurostat_showvoc_links": eurostat, "registry_date": version[1],
            "registry_titles_checked": len(entries), "registry_title_matches": matches,
            "scope": "Fresh downloads of fixed table URLs and Cellar queries. Registry title review is limited to the captured listing."}
