"""Manual CPU evaluation entry point; never invoked by pytest."""

import argparse
import json
import os
from pathlib import Path
import platform
from time import perf_counter
from typing import Any

from gridworld.sphinx_service import (
    CPU_OPTIONS,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    DEFAULT_URL,
    OllamaSphinxService,
    Riddle,
    ServiceError,
    SphinxService,
)

# Valeurs attendues du corpus qui passent par le modèle.
# ADAPTER si le corpus S2-02 utilise d'autres noms (clés "expected", "answer", "id").
JUDGED = ("accepted", "rejected", "ambiguous")


def evaluate_cases(
    service: SphinxService, riddle: Riddle, cases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Evaluate labelled answers and record failures and timings separately."""
    results = []
    for case in cases:
        expected = case.get("expected")
        if expected not in JUDGED:
            continue  # API invalide, panne simulée, annulation : tests déterministes

        entry: dict[str, Any] = {
            "id": case.get("id"),
            "answer": case.get("answer"),
            "expected": expected,
            "accepted": None,
            "message": None,
            "error": None,
        }
        start = perf_counter()
        try:
            verdict = service.judge(riddle, case["answer"])
            entry["accepted"] = verdict.accepted
            entry["message"] = verdict.message
        except ServiceError as exc:
            entry["error"] = type(exc).__name__
        entry["seconds"] = round(perf_counter() - start, 3)

        if entry["error"] is not None:
            entry["outcome"] = "technical_error"  # jamais compté comme un refus
        elif expected == "ambiguous":
            entry["outcome"] = "ambiguous"  # hors score binaire
        elif entry["accepted"] == (expected == "accepted"):
            entry["outcome"] = "correct"
        elif entry["accepted"]:
            entry["outcome"] = "false_positive"
        else:
            entry["outcome"] = "false_negative"
        results.append(entry)
    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate a local sphinx model")
    parser.add_argument("--riddle", required=True, help="S2-02 map JSON")
    parser.add_argument("--corpus", required=True, help="S2-02 evaluation corpus")
    parser.add_argument("--output", required=True, help="Local JSON report")
    parser.add_argument("--url", default=DEFAULT_URL, help="Ollama base URL, without /api")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--cpu-note", required=True, help="CPU/RAM and observed CPU execution")
    args = parser.parse_args()

    map_data = json.loads(Path(args.riddle).read_text(encoding="utf-8"))
    riddle = Riddle(**map_data["sphinx"]["riddle"])
    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    service = OllamaSphinxService(args.url, args.model, args.timeout)
    results = evaluate_cases(service, riddle, corpus["cases"])
    report = {
        "model": args.model,
        "url": args.url,
        "timeout_seconds": args.timeout,
        "options": CPU_OPTIONS,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": platform.python_version(),
        "cpu_note": args.cpu_note,
        "riddle_id": riddle.id,
        "results": results,
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
