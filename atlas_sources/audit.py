"""Live link observations, separate from human content/rights verification."""
from html.parser import HTMLParser
from .acquire import HTTPClient, now, sha256
from .registry import write_json


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.parts.append(data)


def audit(root, registry):
    client = HTTPClient(timeout=15, retries=0)
    cache, rows = {}, []
    for source in registry["sources"]:
        url = source["official_url"]
        if url not in cache:
            row = {"url": url, "checked_at": now()}
            try:
                robots = client.allowed(url)
                data, response = client.get(url)
                digest = sha256(data)
                path = root / "data/local/link-evidence" / digest
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                title = TitleParser()
                if "html" in (response["content_type"] or ""):
                    title.feed(data.decode("utf-8", errors="replace"))
                title_text = " ".join(" ".join(title.parts).split())
                challenge = any(x in title_text.lower() for x in ("checking your browser", "just a moment", "access denied", "captcha"))
                row.update(status="challenge" if challenge else "reachable", title=title_text,
                           sha256=digest, bytes=len(data), robots=robots, **response)
            except (OSError, ValueError) as error:
                row.update(status="failed", error=f"{type(error).__name__}: {error}")
            cache[url] = row
        rows.append({"source_id": source["id"], **cache[url]})
        print(f"{source['id']}: {cache[url]['status']}", flush=True)
    write_json(root / "data/registry/link-audit.json", rows)
    return int(any(r["status"] != "reachable" for r in rows))
