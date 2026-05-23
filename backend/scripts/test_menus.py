"""
test_menus.py
=============
Run a set of test menus through the classify API to verify performance.

Usage:
    .venv/bin/python scripts/test_menus.py
    .venv/bin/python scripts/test_menus.py --report  (generate HTML report)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.core.settings import settings


API_BASE = f"http://localhost:{8000}"
MENUS_PATH = Path(settings.dataset_dir) / "test_menus.json"
REPORT_PATH = Path(settings.dataset_dir) / "processed" / "test_menus_report.html"


def _login() -> str:
    resp = httpx.post(
        f"{API_BASE}/api/v1/auth/login",
        json={"email": "koor@nutrimbg.go.id", "password": "koor123"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _load_menus() -> List[Dict[str, Any]]:
    if not MENUS_PATH.exists():
        print(f"Test menus not found: {MENUS_PATH}")
        sys.exit(1)
    return json.loads(MENUS_PATH.read_text(encoding="utf-8"))


async def _classify(
    client: httpx.AsyncClient, token: str, text: str, education_level: str
) -> Dict[str, Any]:
    resp = await client.post(
        f"{API_BASE}/api/v1/ai/classify",
        json={"text": text, "education_level": education_level},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _grade(score: float) -> str:
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "D"


def _grade_color(grade: str) -> str:
    return {"A": "green", "B": "blue", "C": "orange", "D": "red"}[grade]


def _pass_fail(score: float, expected: List[float]) -> tuple[str, str]:
    low, high = expected
    if low <= score <= high:
        return "✅ PASS", "green"
    return "❌ FAIL", "red"


def _label_icon(label: str) -> str:
    return {"adequate": "✅", "deficient": "⬇️", "excess": "⬆️"}.get(label, "❓")


def _generate_html(results: List[Dict[str, Any]]) -> str:
    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    avg_time = sum(r["elapsed"] for r in results) / total if total else 0

    rows = ""
    for r in results:
        grade = _grade(r["score"])
        pf, _ = _pass_fail(r["score"], r["expected"])
        labels = " | ".join(
            f"{k}: {_label_icon(v)}" for k, v in r["labels"].items()
        )
        rows += f"""
        <tr>
            <td>{r['scenario']}</td>
            <td>{r['education_level']}</td>
            <td><span class="grade grade-{grade}">{grade}</span></td>
            <td>{r['score']:.1f}</td>
            <td>{r['expected'][0]}–{r['expected'][1]}</td>
            <td class="{pf.split()[0].lower()}">{pf.split()[0]}</td>
            <td style="font-size:0.8em">{labels}</td>
            <td>{r['unmatched']}</td>
            <td>{r['elapsed']:.2f}s</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Test Menu Report — NutriMBG</title>
<style>
body {{ font-family: -apple-system, 'Segoe UI', sans-serif; background: #f5f7fa; margin: 0; padding: 20px; }}
h1 {{ color: #2E7D32; }}
table {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
th {{ background: #2E7D32; color: white; padding: 12px; text-align: left; font-size: 0.85em; }}
td {{ padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 0.85em; }}
tr:hover {{ background: #f0fdf4; }}
.summary {{ display: flex; gap: 20px; margin: 20px 0; }}
.card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; text-align: center; }}
.card .num {{ font-size: 2em; font-weight: bold; color: #2E7D32; }}
.card .label {{ color: #666; font-size: 0.85em; }}
.grade {{ font-weight: bold; padding: 2px 8px; border-radius: 4px; }}
.grade-A {{ background: #e8f5e9; color: #2e7d32; }}
.grade-B {{ background: #e3f2fd; color: #1565c0; }}
.grade-C {{ background: #fff3e0; color: #e65100; }}
.grade-D {{ background: #fbe9e7; color: #c62828; }}
.pass {{ color: #2e7d32; font-weight: bold; }}
.fail {{ color: #c62828; font-weight: bold; }}
.bg-pass {{ background: #e8f5e9 !important; }}
.bg-fail {{ background: #ffebee !important; }}
</style>
</head>
<body>
<h1>📊 NutriMBG — Test Menu Report</h1>
<div class="summary">
    <div class="card"><div class="num">{total}</div><div class="label">Total Menu</div></div>
    <div class="card"><div class="num">{passed}</div><div class="label">Passed</div></div>
    <div class="card"><div class="num">{total - passed}</div><div class="label">Failed</div></div>
    <div class="card"><div class="num">{avg_time:.2f}s</div><div class="label">Avg Response Time</div></div>
</div>
<table>
<thead><tr>
    <th>Scenario</th><th>Level</th><th>Grade</th><th>Score</th>
    <th>Expected</th><th>Result</th><th>Labels</th><th>Unmatched</th><th>Time</th>
</tr></thead>
<tbody>
{rows}
</tbody>
</table>
<p style="color:#999; margin-top:12px; font-size:0.8em">
Generated by NutriMBG Test Runner
</p>
</body>
</html>"""


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    args = parser.parse_args()

    menus = _load_menus()
    token = _login()
    results: List[Dict[str, Any]] = []

    print(f"Running {len(menus)} test menus...\n")
    print(f"{'Scenario':35s} {'Level':10s} {'Score':8s} {'Expected':12s} {'Result':6s} {'Time':8s}")
    print("-" * 85)

    async with httpx.AsyncClient() as client:
        for menu in menus:
            scenario = menu["scenario"]
            level = menu["education_level"]
            expected = menu["expected_score_range"]

            start = time.time()
            try:
                data = await _classify(client, token, menu["text"], level)
                elapsed = time.time() - start
                score = data["score"]
                labels = data["labels"]
                unmatched = data.get("unmatched_items", [])
                pf, _ = _pass_fail(score, expected)

                results.append({
                    "scenario": scenario,
                    "education_level": level,
                    "score": score,
                    "expected": expected,
                    "pass": pf == "✅ PASS",
                    "labels": labels,
                    "unmatched": len(unmatched),
                    "elapsed": elapsed,
                })

                print(
                    f"{scenario:35s} {level:10s} {score:6.1f}/100 "
                    f"{f'{expected[0]}-{expected[1]}':12s} {pf:6s} {elapsed:5.2f}s"
                )

            except Exception as e:
                elapsed = time.time() - start
                print(f"{scenario:35s} {level:10s} {'ERR':8s} {'':12s} {'❌':6s} {elapsed:5.2f}s — {e}")
                results.append({
                    "scenario": scenario,
                    "education_level": level,
                    "score": 0,
                    "expected": expected,
                    "pass": False,
                    "labels": {},
                    "unmatched": 0,
                    "elapsed": 0,
                    "error": str(e),
                })

    passed = sum(1 for r in results if r["pass"])
    print(f"\nResults: {passed}/{len(results)} passed")

    if args.report:
        html = _generate_html(results)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(html, encoding="utf-8")
        print(f"Report saved: {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
