from __future__ import annotations

import io
import base64
from typing import Dict, Any
from jinja2 import Template
import pandas as pd

try:
    from weasyprint import HTML  # type: ignore
except Exception:  # noqa: BLE001
    HTML = None


def generate_html_report(results: Dict[str, Any]) -> str:
    tpl = Template(
        """
        <html>
        <head><meta charset='utf-8'><title>Mutation Report</title></head>
        <body>
            <h1>Mutation Report</h1>
            <h2>Summary</h2>
            <p>{{ results.variants | length }} variants processed.</p>
            <h2>Scores</h2>
            <pre>{{ results.scores | tojson(indent=2) }}</pre>
            <h2>Ensemble</h2>
            <pre>{{ results.ensemble | tojson(indent=2) }}</pre>
            <h2>Annotations</h2>
            <pre>{{ results.annotations | tojson(indent=2) }}</pre>
            <h2>Clinical</h2>
            <pre>{{ results.clinical | tojson(indent=2) }}</pre>
        </body>
        </html>
        """
    )
    return tpl.render(results=results)


def generate_pdf_report(results: Dict[str, Any]) -> str:
    html = generate_html_report(results)
    if HTML is None:
        # Fallback: return HTML base64 as a stand-in
        return base64.b64encode(html.encode("utf-8")).decode("utf-8")
    pdf_bytes = HTML(string=html).write_pdf()
    return base64.b64encode(pdf_bytes).decode("utf-8")


def generate_excel_report(results: Dict[str, Any]) -> str:
    rows = []
    for var_key, algos in results.get("scores", {}).items():
        base_row = {"variant": var_key}
        for algo, val in algos.items():
            base_row[algo] = val
        rows.append(base_row)
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Scores")
    return base64.b64encode(buf.getvalue()).decode("utf-8")
