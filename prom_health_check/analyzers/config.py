import re

from prom_health_check.models.prometheus import PrometheusConfig, Recommendation
from ruamel.yaml import YAML

DURATION_SECONDS = {"y": 31536000, "w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}


class ConfigAnalyzer:
    """
    A class to analyze the Prometheus configuration.
    """

    def __init__(self, config: PrometheusConfig):
        """
        Initialize the ConfigAnalyzer.

        Args:
            config: A PrometheusConfig object.
        """
        self.config_str = config.yaml
        yaml_parser = YAML(typ="safe")
        self.config = yaml_parser.load(self.config_str)

    def _check_summary_aggregation(self) -> list[Recommendation]:
        recommendations = []
        aggregating_functions = [
            "sum",
            "avg",
            "max",
            "min",
            "stddev",
            "stdvar",
            "group",
        ]

        if not self.config:
            return recommendations

        rule_groups = self.config.get("rule_groups", [])
        if not rule_groups:
            # Fallback for older prometheus versions
            if "rules" in self.config:
                rule_groups = self.config["rules"]

        if not rule_groups:
            return recommendations

        for group in rule_groups:
            for rule in group.get("rules", []):
                expression = rule.get("expr", "")
                for func in aggregating_functions:
                    if f"{func}(" in expression and "quantile=" in expression:
                        recommendations.append(
                            Recommendation(
                                severity="high",
                                category="Config Hygiene",
                                internal_cause="Aggregation of summary quantiles",
                                impact="The calculated value is statistically incorrect.",
                                recommendation="Do not aggregate summary quantiles. Use histograms instead.",
                                reference="https://prometheus.io/docs/practices/histograms/#quantiles",
                            )
                        )
        return recommendations

    def analyze(self) -> list[Recommendation]:
        """
        Analyze the Prometheus configuration and provide recommendations.

        Returns:
            A list of Recommendation objects.
        """
        recommendations = []

        if not self.config:
            return recommendations

        # Analyze global scrape interval
        global_config = self.config.get("global", {})
        scrape_interval = global_config.get("scrape_interval", "15s")
        parts = re.findall(r"(\d+)(ms|[ywdhms])", scrape_interval)
        if "".join(value + unit for value, unit in parts) == scrape_interval and parts and sum(
            int(value) * DURATION_SECONDS[unit] for value, unit in parts
        ) < 15:
            recommendations.append(
                Recommendation(
                    severity="low",
                    category="Config Hygiene",
                    internal_cause="Low scrape interval",
                    impact="Increased load on Prometheus and targets",
                    recommendation="Increase the scrape interval to 15s or higher",
                    reference="Prometheus scrape interval",
                )
            )

        recommendations.extend(self._check_summary_aggregation())

        return recommendations