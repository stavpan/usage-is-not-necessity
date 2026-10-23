#!/usr/bin/env python3
"""Fetch abstracts for the 520 seeds, so classification stops being title-based.

The method/theory split in the paper rests on a title classifier, and a title
classifier cannot see a paper called *On the electrodynamics of moving bodies*. That
made the theory group a lower bound of 33 works in 520 and biased it toward works
whose titles advertise their genre -- a limitation the paper states and this closes.

Abstracts are cheap: OpenAlex returns them as an inverted index and the 520 seeds can
be requested in eleven batches of fifty, against the 26 seed requests the corpus
itself needs. The inverted index is reconstructed to plain text here rather than
stored raw, because the only consumer is a classifier reading prose.

No citation contexts are fetched, and that is worth stating: the experiment that could
*falsify* Section 5 is citation-intent classification, which needs the sentences
around a citation, not abstracts. OpenAlex does not carry them.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://api.openalex.org"
UA = "world-impact/0.1 (abstract fetch; mailto:panagist32@gmail.com)"
MAILTO = "panagist32@gmail.com"


def reconstruct(inverted: dict[str, list[int]] | None) -> str:
    """OpenAlex returns abstracts as {word: [positions]}; put them back in order."""
    if not inverted:
        return ""
    positions: list[tuple[int, str]] = []
    for word, places in inverted.items():
        for place in places:
            positions.append((int(place), word))
    positions.sort()
    return " ".join(word for _, word in positions)


def fetch(ids: list[str], batch: int = 50, delay: float = 0.3) -> dict[str, str]:
    out: dict[str, str] = {}
    for start in range(0, len(ids), batch):
        chunk = ids[start : start + batch]
        try:
            response = requests.get(
                f"{BASE}/works",
                params={
                    "filter": "ids.openalex:" + "|".join(chunk),
                    "per-page": batch,
                    "select": "id,abstract_inverted_index",
                    "mailto": MAILTO,
                },
                headers={"User-Agent": UA},
                timeout=90.0,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"  batch {start // batch}: {type(error).__name__}")
            time.sleep(3.0)
            continue
        for row in response.json().get("results", []):
            work_id = (row.get("id") or "").rsplit("/", 1)[-1]
            text = reconstruct(row.get("abstract_inverted_index"))
            if work_id and text:
                out[work_id] = text
        print(f"  {min(start + batch, len(ids))}/{len(ids)} requested, {len(out)} abstracts")
        time.sleep(delay)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=ROOT / "data" / "openalex" / "corpus.json")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "openalex" / "abstracts.json")
    args = parser.parse_args()

    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    ids = [work["id"] for work in corpus["seeds"]]
    existing: dict[str, str] = {}
    if args.out.exists():
        existing = json.loads(args.out.read_text(encoding="utf-8"))
    pending = [work_id for work_id in ids if work_id not in existing]
    print(f"{len(existing)} cached, {len(pending)} to fetch")

    abstracts = {**existing, **fetch(pending)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(abstracts, indent=2), encoding="utf-8")
    covered = sum(1 for work_id in ids if work_id in abstracts)
    print(f"\nabstracts for {covered} of {len(ids)} seeds ({covered / len(ids):.1%})")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
