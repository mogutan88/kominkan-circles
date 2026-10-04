#!/usr/bin/env python3
"""Build the single-file SPAs by embedding the circle CSVs into the templates.

    python3 spa/build.py

Outputs (self-contained, no server needed):
    docs/index.html     table view  (search / filter / sortable columns)
    docs/calendar.html  weekly calendar view (rows = 公民館, columns = 曜日)

`docs/` is what GitHub Pages serves.
"""
import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    ("ダンス", ROOT / "data" / "target-dance-circle.csv"),
    ("太極拳", ROOT / "data" / "target-taichi-circle.csv"),
]
TEMPLATES = ["index", "calendar"]

# ---------------------------------------------------------------- parsing --
KANJI_NUM = str.maketrans("一二三四五", "12345")
_T = r"(\d{1,2})(?::(\d{2})|時(?:(\d{1,2})分)?)"
TIME_RE = re.compile(_T + r"\s*(?:(?:~|-|ー|から)\s*(?:" + _T + r")?)?")


def _hm(h, m):
    return f"{int(h)}:{int(m or 0):02d}"


def parse_time(text):
    """Return (display, start_minutes) for the first time range in text."""
    ranges = []
    for m in TIME_RE.finditer(text):
        g = m.groups()
        h1 = g[0]
        m1 = g[1] or g[2]
        start = _hm(h1, m1)
        s = m.group(0)
        if g[3] is not None:  # has end time
            end = _hm(g[3], g[4] or g[5])
            ranges.append((f"{start}〜{end}", int(h1) * 60 + int(m1 or 0)))
        elif re.search(r"(~|-|ー|から)\s*$", s):
            ranges.append((f"{start}〜", int(h1) * 60 + int(m1 or 0)))
        else:
            ranges.append((start, int(h1) * 60 + int(m1 or 0)))
        if len(ranges) >= 2:
            break
    if not ranges:
        return "", None
    return " / ".join(r[0] for r in ranges), ranges[0][1]


WEEK_RE = re.compile(r"第\s*([1-5](?:\s*[・,、~\-]\s*第?\s*[1-5])*)")


def parse_weeks(text):
    t = text.translate(KANJI_NUM)
    # drop "…第5週お休み" style exclusions so they are not read as schedule
    t = re.sub(r"[^\s]*(?:第\s*[1-5]\s*週?)[^\s]*休み", " ", t)
    t = re.sub(r"[^\s]*休み", " ", t)
    m = WEEK_RE.search(t)
    if m:
        raw = m.group(1)
        if re.search(r"[~\-]", raw):
            nums = [int(x) for x in re.findall(r"[1-5]", raw)]
            weeks = list(range(min(nums), max(nums) + 1))
        else:
            weeks = sorted({int(x) for x in re.findall(r"[1-5]", raw)})
        if weeks == [1, 2, 3, 4] or weeks == [1, 2, 3, 4, 5]:
            return "毎週"
        return "第" + "・".join(str(w) for w in weeks)
    if "毎週" in t:
        return "毎週"
    m = re.search(r"(?:月\s*([1-5])\s*回|([1-5])\s*回\s*[/／]?\s*月)", t)
    if m:
        n = int(m.group(1) or m.group(2))
        return "毎週" if n >= 4 else f"月{n}回"
    return ""


AMOUNT_RE = re.compile(
    r"(?:(年|月)(?:額)?\s*)?(\d[\d,]*(?:~\d[\d,]*)?)円(?:\s*[/／]\s*(月|年|回))?"
)


def parse_fee(text):
    if re.search(r"(?:会費|運営費|月会費)\s*[:：]?\s*(?:なし|無料)", text) or "会費無料" in text:
        return "無料"
    cands = []
    for m in AMOUNT_RE.finditer(text):
        unit = m.group(3) or m.group(1) or ""
        amount = m.group(2)
        cands.append((unit, amount))
    if not cands:
        return ""
    chosen = next((c for c in cands if c[0] == "月"), None) or cands[0]
    unit, amount = chosen
    amount = "~".join(f"{int(p.replace(',', '')):,}" for p in amount.split("~"))
    return f"¥{amount}" + (f"/{unit}" if unit else "")


def parse_notes(raw):
    text = unicodedata.normalize("NFKC", " ".join(raw.split()))
    time_disp, start = parse_time(text)
    return {
        "weeks": parse_weeks(text),
        "time": time_disp,
        "start": start,
        "fee": parse_fee(text),
    }


# ----------------------------------------------------------------- build --
def load():
    records = []
    for type_name, path in SOURCES:
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                notes = " ".join(r["備考"].split())
                rec = {
                    "type": type_name,
                    "ku": r["区"],
                    "kominkan": r["公民館名"],
                    "name": r["サークル名"],
                    "genre": r.get("ダンスジャンル") or type_name,
                    "category": r["分類"],
                    "day": r["曜日"],
                    "dist": r["自宅からの距離"].replace("km", "").strip(),
                    "notes": notes,
                    "tel": r["電話番号"],
                    "address": r["住所"].replace("福岡県福岡市", ""),
                }
                rec.update(parse_notes(notes))
                records.append(rec)
    return records


def main():
    records = load()
    data = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
    for name in TEMPLATES:
        src = ROOT / "spa" / f"{name}.template.html"
        if name == "index" and not src.exists():
            src = ROOT / "spa" / "index.template.html"
        template = src.read_text(encoding="utf-8")
        out = template.replace("/*__DATA__*/[]", data)
        dest = ROOT / "docs" / f"{name}.html"
        dest.parent.mkdir(exist_ok=True)
        dest.write_text(out, encoding="utf-8")
        print(f"wrote {dest} ({len(records)} circles)")


if __name__ == "__main__":
    main()
