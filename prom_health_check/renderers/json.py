import json
from prom_health_check.models.prometheus import HealthReport

class JsonRenderer:
    """
    A class to render the health report in JSON format.
    """

    def __init__(self, report: HealthReport):
        """
        Initialize the JsonRenderer.

        Args:
            report: A HealthReport object.
        """
        self.report = report

    def render(self) -> str:
        """
        Render the health report in JSON format.

        Returns:
            A JSON string representing the health report.
        """
        return self.report.model_dump_json(indent=4)