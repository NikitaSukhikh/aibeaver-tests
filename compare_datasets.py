"""Compare original dev_50.json with unpacked MCD format - CONTENT ONLY comparison."""
import json
import csv
import re
from pathlib import Path
from html.parser import HTMLParser

ORIGINAL = Path("datasets/multihiertt-mini/original_disconnected/dev_50.json")
UNPACKED = Path("datasets/multihiertt-mini/unpacked")

class HTMLTableParser(HTMLParser):
    """Parse HTML table and extract all non-empty cell text."""
    def __init__(self):
        super().__init__()
        self.cells = []
        self.current_cell = ""
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag in ("td", "th"):
            self.in_cell = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self.in_cell = False
            text = self.current_cell.strip()
            if text:  # Only add non-empty cells
                self.cells.append(text)

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data

def extract_html_table_content(html):
    """Extract all non-empty cell values from HTML table as a set."""
    parser = HTMLTableParser()
    parser.feed(html)
    # Normalize whitespace in all cells
    return set(" ".join(c.split()) for c in parser.cells)

def normalize_value(val):
    """Normalize a value for comparison."""
    val = str(val).strip()
    # Normalize all whitespace (including internal multiple spaces/newlines)
    val = " ".join(val.split())
    return val

def normalize_cell_value(val):
    """Normalize cell value more aggressively for content comparison."""
    val = normalize_value(val)
    # Additional normalizations for table cells
    val = val.replace("   ", " ").replace("  ", " ")  # Collapse multiple spaces
    return val

def load_original():
    with open(ORIGINAL, "r", encoding="utf-8") as f:
        return json.load(f)

def load_csv(name):
    path = UNPACKED / "tables" / f"{name}.csv"
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def compare_paragraphs(original_data, paragraphs_csv):
    """Compare paragraph content."""
    issues = []

    # Group by UID
    csv_by_uid = {}
    for row in paragraphs_csv:
        uid = row["source_uid"]
        if uid not in csv_by_uid:
            csv_by_uid[uid] = set()
        text = normalize_value(row["paragraph_text"])
        if text:
            csv_by_uid[uid].add(text)

    for record in original_data:
        uid = record["uid"]
        if uid not in csv_by_uid:
            issues.append(f"Missing UID {uid} in paragraphs")
            continue

        orig_paragraphs = set()
        for para in record["paragraphs"]:
            text = normalize_value(para)
            if text:
                orig_paragraphs.add(text)

        csv_paragraphs = csv_by_uid[uid]

        missing_in_csv = orig_paragraphs - csv_paragraphs
        extra_in_csv = csv_paragraphs - orig_paragraphs

        for m in missing_in_csv:
            issues.append(f"[{uid[:8]}] Missing paragraph in CSV: {m[:80]}...")
        for e in extra_in_csv:
            issues.append(f"[{uid[:8]}] Extra paragraph in CSV: {e[:80]}...")

    return issues

def compare_table_content(original_data, cells_csv):
    """Compare table cell values (content only, not structure)."""
    issues = []

    # Group cell values by UID and table_index
    csv_by_uid = {}
    for row in cells_csv:
        uid = row["source_uid"]
        tbl_idx = int(row["table_index"])
        cell_text = normalize_value(row["cell_text"])

        if uid not in csv_by_uid:
            csv_by_uid[uid] = {}
        if tbl_idx not in csv_by_uid[uid]:
            csv_by_uid[uid][tbl_idx] = set()

        if cell_text:
            csv_by_uid[uid][tbl_idx].add(cell_text)

    for record in original_data:
        uid = record["uid"]

        for tbl_idx, html_table in enumerate(record.get("tables", [])):
            orig_cells = extract_html_table_content(html_table)

            if uid not in csv_by_uid or tbl_idx not in csv_by_uid[uid]:
                if orig_cells:
                    issues.append(f"[{uid[:8]}] Missing table {tbl_idx} in CSV (had {len(orig_cells)} cells)")
                continue

            csv_cells = csv_by_uid[uid][tbl_idx]

            # Compare content sets
            missing_in_csv = orig_cells - csv_cells
            extra_in_csv = csv_cells - orig_cells

            for m in missing_in_csv:
                issues.append(f"[{uid[:8]}] Table {tbl_idx} missing cell value: '{m}'")
            for e in extra_in_csv:
                issues.append(f"[{uid[:8]}] Table {tbl_idx} extra cell value: '{e}'")

    return issues

def compare_descriptions(original_data, cells_csv):
    """Compare table_description content."""
    issues = []

    # Get all descriptions from CSV
    csv_desc = {}
    for row in cells_csv:
        uid = row["source_uid"]
        cell_ref = row["cell_ref"]
        desc = normalize_value(row.get("cell_description", ""))

        if uid not in csv_desc:
            csv_desc[uid] = {}
        if desc:
            csv_desc[uid][cell_ref] = desc

    for record in original_data:
        uid = record["uid"]
        table_desc = record.get("table_description", {})

        for cell_ref, orig_desc in table_desc.items():
            orig_norm = normalize_value(orig_desc)
            csv_norm = csv_desc.get(uid, {}).get(cell_ref, "")

            if orig_norm and not csv_norm:
                issues.append(f"[{uid[:8]}] Description missing for {cell_ref}: {orig_desc[:60]}...")
            elif orig_norm != csv_norm:
                issues.append(f"[{uid[:8]}] Description differs for {cell_ref}")

    return issues

def main():
    print("Loading data...")
    original_data = load_original()
    paragraphs_csv = load_csv("multihiertt_paragraphs")
    cells_csv = load_csv("multihiertt_cells")

    print(f"Original records: {len(original_data)}")
    print(f"CSV paragraphs: {len(paragraphs_csv)}")
    print(f"CSV cells: {len(cells_csv)}")

    print("\n--- Comparing Paragraph CONTENT ---")
    para_issues = compare_paragraphs(original_data, paragraphs_csv)
    if para_issues:
        print(f"Found {len(para_issues)} issues:")
        for issue in para_issues[:10]:
            print(f"  - {issue}")
        if len(para_issues) > 10:
            print(f"  ... and {len(para_issues) - 10} more")
    else:
        print("All paragraph content matches!")

    print("\n--- Comparing Table Cell CONTENT ---")
    table_issues = compare_table_content(original_data, cells_csv)
    if table_issues:
        print(f"Found {len(table_issues)} issues:")
        for issue in table_issues[:10]:
            print(f"  - {issue}")
        if len(table_issues) > 10:
            print(f"  ... and {len(table_issues) - 10} more")
    else:
        print("All table cell content matches!")

    print("\n--- Comparing Description CONTENT ---")
    desc_issues = compare_descriptions(original_data, cells_csv)
    if desc_issues:
        print(f"Found {len(desc_issues)} issues:")
        for issue in desc_issues[:10]:
            print(f"  - {issue}")
        if len(desc_issues) > 10:
            print(f"  ... and {len(desc_issues) - 10} more")
    else:
        print("All description content matches!")

    print("\n--- Summary ---")
    total = len(para_issues) + len(table_issues) + len(desc_issues)
    if total == 0:
        print("SUCCESS: All content is identical!")
    else:
        print(f"CONTENT DIFFERENCES: {total}")
        print(f"  Paragraphs: {len(para_issues)}")
        print(f"  Table cells: {len(table_issues)}")
        print(f"  Descriptions: {len(desc_issues)}")

    return total

if __name__ == "__main__":
    exit(main())
