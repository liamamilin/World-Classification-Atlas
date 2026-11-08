"""Immutable byte snapshots. A URL or successful HTTP response is never a node count."""
import hashlib
import json
import time
import urllib.error
import urllib.request
import urllib.robotparser
import uuid
import zipfile
import io
from datetime import datetime, timezone
from pathlib import Path
from .registry import read_json, write_json

USER_AGENT = "WorldClassificationAtlas/0.1 (+https://github.com/liamamilin/World-Classification-Atlas)"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def check_payload(data, resource):
    if not data:
        raise ValueError("empty response")
    head = data[:512].lstrip().lower()
    if resource["format"] != "html" and (head.startswith(b"<!doctype html") or head.startswith(b"<html")):
        raise ValueError("HTML response instead of expected data (possibly login/error page)")
    if resource["format"] in ("zip", "xlsx"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            bad = z.testzip()
            if bad:
                raise ValueError(f"corrupt ZIP member: {bad}")
            if resource["format"] == "xlsx" and "[Content_Types].xml" not in z.namelist():
                raise ValueError("not an XLSX package")
    elif resource["format"] in ("json", "jsonld"):
        json.loads(data)
    elif resource["format"] == "pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("not a PDF payload")
    elif resource["format"] in ("csv", "tsv", "txt"):
        data.decode(resource["encoding"], errors="strict")


def storage_root(root, resource):
    return root / ("data/raw" if resource["rights"]["redistribute"] is True else "data/local/raw")


def snapshot_dir(root, resource, digest):
    return storage_root(root, resource) / resource["source_id"] / resource["edition"] / resource["id"] / digest


class HTTPClient:
    def __init__(self, timeout=25, delay=1.0, retries=1):
        self.timeout, self.delay, self.retries = timeout, delay, retries
        self.last_request = 0
        self.robots = {}

    def get(self, url):
        for attempt in range(self.retries + 1):
            time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    # Deliberately bounded; large taxonomic dumps need a streaming adapter.
                    data = response.read(50 * 1024 * 1024 + 1)
                    if len(data) > 50 * 1024 * 1024:
                        raise ValueError("resource exceeds 50 MiB limit")
                    return data, {"final_url": response.url, "http_status": response.status,
                                  "content_type": response.headers.get("Content-Type"),
                                  "etag": response.headers.get("ETag"),
                                  "last_modified": response.headers.get("Last-Modified")}
            except urllib.error.HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504) or attempt == self.retries:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == self.retries:
                    raise
            time.sleep(min(2 ** attempt, 8))

    def allowed(self, url):
        from urllib.parse import urlsplit
        p = urlsplit(url)
        origin = f"{p.scheme}://{p.netloc}"
        if origin not in self.robots:
            robots_url = origin + "/robots.txt"
            try:
                data, _ = self.get(robots_url)
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(data.decode("utf-8", errors="replace").splitlines())
                self.robots[origin] = (parser, "fetched")
            except urllib.error.HTTPError as error:
                if error.code not in (404, 410):
                    raise ValueError(f"robots unavailable: HTTP {error.code}") from error
                self.robots[origin] = (None, f"HTTP {error.code}; no robots rules")
        parser, note = self.robots[origin]
        if parser is not None and not parser.can_fetch(USER_AGENT, url):
            raise ValueError("robots.txt disallows this URL")
        if parser is not None:
            delay = parser.crawl_delay(USER_AGENT) or parser.crawl_delay("*")
            if delay:
                self.delay = max(self.delay, delay)
        return {"url": origin + "/robots.txt", "result": note, "allowed": True}


def collect(root, resources, refresh=False, freeze=False, client=None):
    client = client or HTTPClient()
    lock_path = root / "data/resources.lock.json"
    lock = read_json(lock_path) if lock_path.exists() else {}
    results = []
    for resource in resources:
        rid = resource["id"]
        result = {"resource_id": rid, "source_id": resource["source_id"],
                  "edition": resource["edition"], "url": resource["url"], "attempted_at": now()}
        try:
            if resource["rights"]["download"] is not True or resource["rights"]["local_processing"] is not True:
                result.update(status="blocked_rights", error="download/local processing permission is not confirmed")
                results.append(result)
                continue
            pinned = lock.get(rid)
            if pinned and any(pinned.get(key) != resource[key] for key in ("url", "source_id", "edition")):
                raise ValueError("resource URL/source/edition changed; use a new resource ID or review the lock")
            cached_path = (snapshot_dir(root, resource, pinned["sha256"]) / resource["filename"]) if pinned else None
            if pinned and not refresh and cached_path.exists():
                folder = snapshot_dir(root, resource, pinned["sha256"])
                data = (folder / resource["filename"]).read_bytes()
                if sha256(data) != pinned["sha256"]:
                    raise ValueError("cached snapshot hash mismatch")
                check_payload(data, resource)
                result.update(status="cached", sha256=pinned["sha256"], path=str((folder / resource["filename"]).relative_to(root)), bytes=len(data))
            else:
                robots = client.allowed(resource["url"])
                data, response = client.get(resource["url"])
                digest = sha256(data)
                folder = snapshot_dir(root, resource, digest)
                folder.mkdir(parents=True, exist_ok=True)
                target = folder / resource["filename"]
                if target.exists():
                    if target.read_bytes() != data:
                        raise ValueError("snapshot collision")
                else:
                    with target.open("xb") as stream:
                        stream.write(data)
                manifest = {**result, **response, "sha256": digest, "bytes": len(data),
                            "path": str(target.relative_to(root)), "rights": resource["rights"],
                            "role": resource["role"], "language": resource["language"],
                            "format": resource["format"], "publication_date": resource.get("publication_date"),
                            "robots": robots}
                if not (folder / "manifest.json").exists():
                    write_json(folder / "manifest.json", manifest)
                # Preserve failed payloads as evidence too, without pinning or parsing them.
                result.update(sha256=digest, path=manifest["path"], bytes=len(data), **response)
                check_payload(data, resource)
                status = "drift" if pinned and pinned["sha256"] != digest else "downloaded"
                result.update(status=status, sha256=digest, path=manifest["path"], bytes=len(data), **response)
                if status == "drift":
                    result["error"] = "upstream bytes changed; old pin retained; review new snapshot"
                if freeze and not pinned:
                    lock[rid] = {"sha256": digest, "url": resource["url"],
                                 "source_id": resource["source_id"], "edition": resource["edition"]}
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            result.update(status="failed", error=f"{type(error).__name__}: {error}")
        results.append(result)
        print(f"{rid}: {result['status']}", flush=True)
    if freeze:
        write_json(lock_path, lock)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:8]
    write_json(root / "data/acquisition" / (run_id + ".json"), results)
    return results
