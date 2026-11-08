"""Read-only OOXML extraction with original cells, rows and sheet identities retained."""
import io
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def unescape(value):
    # One pass preserves escaped literal sequences such as _x005F_x000D_.
    return re.sub(r"_x([0-9a-fA-F]{4})_", lambda m: chr(int(m[1], 16)), value)


def read_workbook(data):
    sheets = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = ["".join(t.text or "" for t in si.findall(".//m:t", NS))
                       for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        rels = {r.attrib["Id"]: posixpath.normpath("xl/" + r.attrib["Target"])
                if not r.attrib["Target"].startswith("/") else r.attrib["Target"].lstrip("/")
                for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        for sheet in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", NS):
            rows = []
            tree = ET.fromstring(z.read(rels[sheet.attrib[REL]]))
            for row in tree.findall("m:sheetData/m:row", NS):
                cells, wire = {}, {}
                for cell in row.findall("m:c", NS):
                    if cell.find("m:f", NS) is not None:
                        raise ValueError(f"unexpected formula in source: {sheet.get('name')}!{cell.get('r')}")
                    value = cell.find("m:v", NS)
                    value = value.text if value is not None else None
                    if cell.get("t") == "s":
                        value = strings[int(value)]
                    elif cell.get("t") == "inlineStr":
                        value = "".join(t.text or "" for t in cell.findall(".//m:t", NS))
                    column = re.fullmatch(r"([A-Z]+)\d+", cell.get("r"))[1]
                    wire[column] = value
                    cells[column] = unescape(value) if value is not None else None
                rows.append({"row": int(row.get("r")), "cells": cells, "wire_values": wire})
            sheets[sheet.get("name")] = rows
    return sheets
