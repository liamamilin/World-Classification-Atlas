"""Resolve the notation in CPC 3.0 notes against the locked HS 2022 catalogue."""
import re
from collections import defaultdict

# These source-specific editorial readings are kept alongside the untouched clauses.
PERIOD_SEPARATOR = "CPC:3.0:41609"
BARE_SUFFIXES = "CPC:3.0:46533"


def full_code(token):
    if re.fullmatch(r"[0-9]{4}|[0-9]{4}\.[0-9]{2}", token):
        return token
    if re.fullmatch(r"[0-9]{2}\.[0-9]{2}", token):
        return token.replace(".", "")
    return None


def suffix_code(token, heading, allow_bare):
    if heading and (re.fullmatch(r"\.[0-9]{2}", token) or (
        allow_bare and re.fullmatch(r"[0-9]{2}", token)
    )):
        return heading + "." + token.lstrip(".")
    return None


def resolve(references, catalogue):
    by_code = {node["code"]: node["id"] for node in catalogue if node["level"] in ("heading", "subheading")}
    subheadings = defaultdict(list)
    for code in by_code:
        if "." in code:
            subheadings[code[:4]].append(code)

    for ref in references:
        terms = []
        for group in ref["hs_notation"].split(";"):
            heading = None
            separator = r"\s*(?:[,&]|\band\b)\s*"
            if ref["cpc_id"] == PERIOD_SEPARATOR:
                separator += r"|(?<=8105\.30\.) (?=8108\.30)"
            for raw in re.split(separator, group.strip()):
                term = raw.removesuffix(".") if ref["cpc_id"] == PERIOD_SEPARATOR else raw
                parts = re.split(r"\s*([/-])\s*", term)
                first = full_code(parts[0])
                form = "code"
                if first is None:
                    first = suffix_code(parts[0], heading, ref["cpc_id"] == BARE_SUFFIXES)
                    form = "suffix" if parts[0].startswith(".") else "bare_suffix"
                codes = [first] if first else []
                if first:
                    heading = first[:4]
                if len(parts) == 3 and first and "." in first:
                    last = full_code(parts[2]) or suffix_code(parts[2], heading, True)
                    if last and "." in last and last[:4] == heading:
                        codes.append(last)
                        form = "range" if parts[1] == "-" else "slash_list"
                    else:
                        codes = []
                elif len(parts) != 1:
                    codes = []

                missing = [code for code in codes if code not in by_code]
                issue = "unreadable_notation" if not codes else None
                if missing:
                    issue = "code_not_in_hs2022"
                if form == "range" and not issue:
                    start, end = codes
                    codes = sorted(code for code in subheadings[heading] if start <= code <= end)
                    if not codes:
                        issue = "empty_or_reversed_range"
                terms.append({
                    "raw": raw, "form": form, "target_ids": [] if issue else [by_code[code] for code in codes],
                    **({"issue": issue, "attempted_codes": codes} if issue else {}),
                })
        ref["terms"] = terms
        ref["target_ids"] = list(dict.fromkeys(target for term in terms for target in term["target_ids"]))
        ref["resolution_status"] = "pending" if any("issue" in term for term in terms) else "verified_codes"
    return references
