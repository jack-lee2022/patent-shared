#!/usr/bin/env python3
"""
abstract_enricher.py — Enrich patent CSV with abstracts and IPC codes
by fetching Google Patents detail pages.

Adds two columns to the CSV:
  abstract    — full abstract text (improves effect classification accuracy)
  ipc_detail  — detailed IPC/CPC codes from the detail page (improves tech classification)

Usage:
    python abstract_enricher.py --csv patents.csv --out patents_enriched.csv
    python abstract_enricher.py --csv patents.csv --out patents_enriched.csv --no-tor
    python abstract_enricher.py --csv patents.csv --out patents_enriched.csv --max 50
"""

import sys
import csv
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from google_patents_collector import GooglePatentsDetailEnricher


def enrich_csv(
    input_csv: str,
    output_csv: str,
    max_enrich: int = 0,
    use_tor: bool = True,
    delay: float = 3.0,
) -> dict:
    """
    Enrich a patent CSV with abstract and detailed IPC codes.

    Skips rows that already have a non-empty abstract.
    max_enrich=0 (default) means enrich ALL patents that are missing abstracts.
    Returns a stats dict: {total, enriched, failed, abstract_added, ipc_added}.
    """
    # ── Read CSV ──────────────────────────────────────────────────────────────
    with open(input_csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if not rows:
        print("[ENRICH] Input CSV is empty.")
        return {}

    # Add new columns at the end if missing
    for col in ("abstract", "ipc_detail"):
        if col not in fieldnames:
            fieldnames.append(col)
    for row in rows:
        row.setdefault("abstract", "")
        row.setdefault("ipc_detail", "")

    # ── Decide which rows need enrichment ────────────────────────────────────
    to_enrich = [
        (i, r) for i, r in enumerate(rows)
        if not r.get("abstract", "").strip()
        and r.get("publication_number", "").strip()
    ]
    if max_enrich > 0:
        to_enrich = to_enrich[:max_enrich]

    print(f"[ENRICH] {len(to_enrich)} patents need enrichment (total: {len(rows)})")
    if not to_enrich:
        print("[ENRICH] Nothing to do — all rows already have abstracts.")
        _write_csv(rows, fieldnames, output_csv)
        return {"total": len(rows), "enriched": 0, "failed": 0, "abstract_added": 0, "ipc_added": 0}

    enricher = GooglePatentsDetailEnricher(tor_enabled=use_tor)

    enriched = 0
    failed = 0
    abstract_added = 0
    ipc_added = 0

    for seq, (row_idx, row) in enumerate(to_enrich, 1):
        pid = row["publication_number"].strip()
        print(f"[ENRICH] {seq}/{len(to_enrich)}  {pid} ...", end=" ", flush=True)

        try:
            detail = enricher.fetch_detail(pid)
        except Exception as e:
            print(f"ERROR {e}")
            failed += 1
            time.sleep(delay)
            continue

        if not detail:
            print("fetch returned None")
            failed += 1
            time.sleep(delay)
            continue

        # ── Abstract ──────────────────────────────────────────────────────────
        abstract_text = ""
        if detail.get("abstract"):
            abstract_text = detail["abstract"].replace("\n", " ").strip()
        elif detail.get("claims"):
            # First sentence of claims as a rough proxy
            abstract_text = detail["claims"].split("\n")[0][:400].strip()

        if abstract_text:
            rows[row_idx]["abstract"] = abstract_text
            abstract_added += 1

        # ── IPC / CPC codes ───────────────────────────────────────────────────
        ipc_list = detail.get("ipc_codes", [])
        if ipc_list:
            rows[row_idx]["ipc_detail"] = "; ".join(ipc_list[:8])
            # Also back-fill the original 'ipc' column if it was empty
            if not rows[row_idx].get("ipc", "").strip():
                rows[row_idx]["ipc"] = ipc_list[0]  # most specific code first
            ipc_added += 1

        status_parts = []
        if abstract_text:
            status_parts.append(f"abs={len(abstract_text)}ch")
        if ipc_list:
            status_parts.append(f"ipc={len(ipc_list)}")
        print(", ".join(status_parts) if status_parts else "no new data")
        enriched += 1
        time.sleep(delay)

    # ── Write output ──────────────────────────────────────────────────────────
    _write_csv(rows, fieldnames, output_csv)

    stats = {
        "total": len(rows),
        "enriched": enriched,
        "failed": failed,
        "abstract_added": abstract_added,
        "ipc_added": ipc_added,
        "output": output_csv,
    }
    print(
        f"\n[ENRICH] Complete: {enriched} processed, "
        f"{abstract_added} abstracts added, {ipc_added} IPC codes added, "
        f"{failed} failed"
    )
    print(f"[ENRICH] Output: {output_csv}")
    return stats


def _write_csv(rows: list, fieldnames: list, output_csv: str) -> None:
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patent Abstract & IPC Enricher")
    parser.add_argument("--csv",   required=True,  help="Input CSV path")
    parser.add_argument("--out",   required=True,  help="Output enriched CSV path")
    parser.add_argument("--max",   type=int, default=0, help="Max patents to enrich (default 0 = all)")
    parser.add_argument("--delay", type=float, default=3.0, help="Delay between requests in seconds (default 3.0)")
    parser.add_argument("--no-tor", action="store_true", help="Disable Tor proxy")
    args = parser.parse_args()

    enrich_csv(
        input_csv=args.csv,
        output_csv=args.out,
        max_enrich=args.max,
        use_tor=not args.no_tor,
        delay=args.delay,
    )
