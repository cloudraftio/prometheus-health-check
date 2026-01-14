from jinja2 import Environment, FileSystemLoader
from prom_health_check.models.prometheus import HealthReport
import os
import datetime

def human_readable_bytes(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Y{suffix}"

def human_readable_number(num):
    abs_num = abs(num)
    if abs_num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"{num/1_000:.2f}K"
    else:
        return str(num)

def timestamp_to_datetime(ts):
    return datetime.datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')

def human_readable_bytes(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Y{suffix}"

def human_readable_number(num):
    abs_num = abs(num)
    if abs_num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"{num/1_000:.2f}K"
    else:
        return str(num)

class HtmlRenderer:
    """
    A class to render the health report in HTML format.
    """

    def __init__(self, report: HealthReport):
        """
        Initialize the HtmlRenderer.

        Args:
            report: A HealthReport object.
        """
        self.report = report
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.env.filters['timestamp_to_datetime'] = timestamp_to_datetime
        self.env.filters['human_readable_bytes'] = human_readable_bytes
        self.env.filters['human_readable_number'] = human_readable_number


    def render(self) -> str:
        """
        Render the health report in HTML format.

        Returns:
            An HTML string representing the health report.
        """
        template = self.env.get_template("detailed_report.html.jinja")

        tsdb_status_json = {}
        if self.report.tsdb_status:
            tsdb_status_json = self.report.tsdb_status.model_dump()

        return template.render(report=self.report, tsdb_status_json=tsdb_status_json)
