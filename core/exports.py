import csv
import html
import json
from pathlib import Path
from datetime import datetime


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
            section = html.escape(result["section"])
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
        }}
        h1 {{
            color: #0b5cad;
        }}
        section {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 18px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background: #eef4fb;
        }}
        pre {{
            white-space: pre-wrap;
            background: #111827;
            color: #e5e7eb;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
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


def render_html_data(data):
    if isinstance(data, list):
        if not data:
            return "<p>No data.</p>"

        if all(isinstance(item, dict) for item in data):
            keys = sorted({key for item in data for key in item.keys()})
            rows = []
            for item in data:
                row = "".join(f"<td>{html.escape(str(item.get(key, '')))}</td>" for key in keys)
                rows.append(f"<tr>{row}</tr>")
            header = "".join(f"<th>{html.escape(str(key))}</th>" for key in keys)
            return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"

    if isinstance(data, dict):
        rows = []
        for key, value in flatten_dict(data).items():
            rows.append(
                f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
            )
        return f"<table>{''.join(rows)}</table>"

    return f"<pre>{html.escape(str(data))}</pre>"
