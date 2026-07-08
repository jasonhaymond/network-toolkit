"""
Report export engine.

The toolkit collects structured dictionaries/lists from each diagnostic module.
This file turns those results into JSON, CSV, and readable HTML reports.

The HTML renderer tries to preserve command output formatting because raw dumps
stuffed into table cells are a crime against eyesight.
"""

import csv
import html
import json
from pathlib import Path
from datetime import datetime


RAW_TEXT_KEYS = {
    "stdout",
    "stderr",
    "raw_output",
    "command_output",
    "output",
    "raw",
}


class ReportSession:
    def __init__(self):
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.results = []

    def add_result(self, section_name, data):
        self.results.append({
            "section": section_name,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "data": data,
        })

    def _export_dir(self, config):
        export_path = Path(config.get("report_export_path", "reports"))
        export_path.mkdir(parents=True, exist_ok=True)
        return export_path

    def _base_filename(self):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"network-report-{stamp}"

    def as_dict(self):
        return {
            "started_at": self.started_at,
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "result_count": len(self.results),
            "results": self.results,
        }

    def export_json(self, config):
        path = self._export_dir(config) / f"{self._base_filename()}.json"
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.as_dict(), file, indent=2)
        return f"[green]JSON exported:[/green] {path}"

    def export_csv(self, config):
        path = self._export_dir(config) / f"{self._base_filename()}.csv"

        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["section", "timestamp", "key", "value"])

            for result in self.results:
                section = result["section"]
                timestamp = result["timestamp"]
                data = result["data"]

                if isinstance(data, list):
                    for index, item in enumerate(data):
                        if isinstance(item, dict):
                            for key, value in item.items():
                                writer.writerow([section, timestamp, f"{index}.{key}", value])
                        else:
                            writer.writerow([section, timestamp, index, item])

                elif isinstance(data, dict):
                    for key, value in flatten_dict(data).items():
                        writer.writerow([section, timestamp, key, value])

                else:
                    writer.writerow([section, timestamp, "value", data])

        return f"[green]CSV exported:[/green] {path}"

    def export_html(self, config):
        path = self._export_dir(config) / f"{self._base_filename()}.html"

        sections = []
        for result in self.results:
            section = html.escape(pretty_label(result["section"]))
            timestamp = html.escape(result["timestamp"])
            body = render_html_data(result["data"])
            sections.append(
                f"""
                <section>
                    <h2>{section}</h2>
                    <p class="timestamp">{timestamp}</p>
                    {body}
                </section>
                """
            )

        doc = f"""
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Network Toolkit Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 32px;
            background: #f6f8fa;
            color: #222;
            line-height: 1.35;
        }}
        h1 {{
            color: #0b5cad;
        }}
        h2 {{
            margin-top: 0;
        }}
        section {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            table-layout: auto;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background: #eef4fb;
            width: 260px;
        }}
        pre {{
            white-space: pre-wrap;
            word-break: break-word;
            overflow-wrap: anywhere;
            background: #111827;
            color: #e5e7eb;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
            font-size: 13px;
            line-height: 1.35;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
        .nested {{
            margin-left: 0;
            margin-top: 8px;
        }}
        .summary-table th {{
            width: 220px;
        }}
        .empty {{
            color: #777;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>Network Toolkit Report</h1>
    <p>Started: {html.escape(self.started_at)}</p>
    <p>Exported: {html.escape(datetime.now().isoformat(timespec="seconds"))}</p>
    {''.join(sections)}
</body>
</html>
"""

        with open(path, "w", encoding="utf-8") as file:
            file.write(doc)

        return f"[green]HTML exported:[/green] {path}"

    def export_all(self, config):
        return "\n".join([
            self.export_json(config),
            self.export_csv(config),
            self.export_html(config),
        ])


def pretty_label(value):
    return str(value).replace("_", " ").replace(".", " → ").title()


def flatten_dict(data, parent_key=""):
    items = {}

    for key, value in data.items():
        new_key = f"{parent_key}.{key}" if parent_key else str(key)

        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key))
        elif isinstance(value, list):
            items[new_key] = json.dumps(value)
        else:
            items[new_key] = value

    return items


def is_raw_text_key(key):
    key = str(key).lower()
    return key in RAW_TEXT_KEYS or key.endswith("_raw") or key.endswith("_output") or "stdout" in key or "stderr" in key


def render_value(key, value):
    if value is None or value == "":
        return '<span class="empty">(blank)</span>'

    if isinstance(value, (dict, list)):
        return render_html_data(value)

    text = str(value)

    if is_raw_text_key(key) or "\n" in text or len(text) > 180:
        return f"<pre>{html.escape(text)}</pre>"

    return html.escape(text)


def render_dict_as_table(data):
    rows = []

    priority_keys = [
        "score", "rating", "method", "target", "success", "included_in_score",
        "avg_ms", "jitter_ms", "loss_percent", "notes", "command",
        "returncode", "stdout", "stderr", "raw_output"
    ]

    keys = []
    for key in priority_keys:
        if key in data:
            keys.append(key)
    for key in data:
        if key not in keys:
            keys.append(key)

    for key in keys:
        value = data[key]
        rows.append(
            f"<tr><th>{html.escape(pretty_label(key))}</th><td>{render_value(key, value)}</td></tr>"
        )

    return f'<table class="summary-table">{"".join(rows)}</table>'


def render_list_of_dicts(data):
    if not data:
        return '<p class="empty">No data.</p>'

    keys = sorted({key for item in data if isinstance(item, dict) for key in item.keys()})

    # If rows contain raw dumps, render each dict as its own block instead of a giant unreadable table.
    if any(any(is_raw_text_key(k) or isinstance(item.get(k), (dict, list)) for k in item.keys()) for item in data if isinstance(item, dict)):
        blocks = []
        for idx, item in enumerate(data, start=1):
            blocks.append(f"<h3>Item {idx}</h3>{render_dict_as_table(item)}")
        return "".join(blocks)

    rows = []
    for item in data:
        row = "".join(f"<td>{render_value(key, item.get(key, ''))}</td>" for key in keys)
        rows.append(f"<tr>{row}</tr>")

    header = "".join(f"<th>{html.escape(pretty_label(key))}</th>" for key in keys)
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def render_html_data(data):
    if isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            return render_list_of_dicts(data)
        return "<pre>" + html.escape(json.dumps(data, indent=2)) + "</pre>"

    if isinstance(data, dict):
        return render_dict_as_table(data)

    return f"<pre>{html.escape(str(data))}</pre>"
