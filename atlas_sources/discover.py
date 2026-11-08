"""Reproducible discovery metadata; discovery never promotes records to verified."""
import re
import urllib.parse
from html.parser import HTMLParser
from .acquire import HTTPClient, now, sha256
from .registry import write_json

FAMILY = "https://unstats.un.org/unsd/classifications/Family/ListByName"
PORTALS = [FAMILY, "https://ec.europa.eu/eurostat/ramon/",
           "https://ec.europa.eu/eurostat/web/metadata/classifications"]


class FamilyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.started = False
        self.finished = False
        self.depth = 0
        self.item = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if not self.started or self.finished:
            return
        if tag == "ul":
            self.depth += 1
        if tag == "li" and self.depth:
            self.item = {"parts": [], "url": None}
        if tag == "a" and self.item is not None:
            href = dict(attrs).get("href", "")
            if "Detail" in href:
                self.item["url"] = urllib.parse.urljoin(FAMILY, href)

    def handle_data(self, data):
        if "A total number of" in data:
            self.started = True
        if self.item is not None:
            self.item["parts"].append(data)

    def handle_endtag(self, tag):
        if tag == "li" and self.item is not None:
            name = " ".join(" ".join(self.item.pop("parts")).split())
            self.rows.append({"name": name, "official_detail_url": self.item["url"],
                              "verification_status": "candidate"})
            self.item = None
        if tag == "ul" and self.started and self.depth:
            self.depth -= 1
            if not self.depth:
                self.finished = True


def parse_family(html):
    parser = FamilyParser()
    parser.feed(html)
    match = re.search(r"A total number of\s*(\d+)", html)
    expected = int(match[1]) if match else None
    if not parser.rows or (expected is not None and len(parser.rows) != expected):
        raise ValueError(f"Family page layout/count changed: parsed={len(parser.rows)}, advertised={expected}")
    return parser.rows, expected


def discover(root):
    client = HTTPClient()
    attempts = []
    failed = False
    for url in PORTALS:
        result = {"url": url, "checked_at": now()}
        try:
            robots = client.allowed(url)
            data, response = client.get(url)
            digest = sha256(data)
            # Full pages are local evidence, not copied into the public repository.
            local = root / "data/local/discovery" / (digest + ".html")
            if not local.exists():
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(data)
            result.update(status="reachable", sha256=digest, bytes=len(data), robots=robots, **response)
            if url == FAMILY:
                rows, expected = parse_family(data.decode("utf-8-sig"))
                write_json(root / "data/discovery/unsd-family.json",
                           {"url": url, "retrieved_at": result["checked_at"], "sha256": digest,
                            "advertised_count": expected, "parsed_count": len(rows),
                            "note": "Discovery facts only; original portal metadata may be stale. No download/rights verification implied.",
                            "candidates": rows})
        except (OSError, ValueError) as error:
            result.update(status="failed", error=f"{type(error).__name__}: {error}")
            failed = True
        attempts.append(result)
        print(f"{url}: {result['status']}", flush=True)
    write_json(root / "data/discovery/portals.json", attempts)
    return int(failed)
