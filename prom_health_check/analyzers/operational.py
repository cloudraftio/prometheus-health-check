from prom_health_check.collectors.prom_api import PrometheusAPICollector
from prom_health_check.models.prometheus import Recommendation


class OperationalAnalyzer:
    def __init__(self, collector: PrometheusAPICollector):
        self.collector = collector

    def analyze(self) -> list[Recommendation]:
        recommendations = []
        targets = self.collector.get_active_targets()
        down_count = sum(target["health"] == "down" for target in targets)
        if not targets:
            recommendations.append(Recommendation(
                severity="low",
                category="Scraping",
                internal_cause="No active scrape targets",
                impact="Prometheus is not scraping any targets",
                recommendation="If scraping is expected, check scrape configuration, service discovery, and relabeling.",
                reference="https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config",
            ))
        elif down_count:
            recommendations.append(Recommendation(
                severity="high",
                category="Scraping",
                internal_cause=f"Scrape failures on {down_count} of {len(targets)} active targets",
                impact="Missing or stale metrics for affected targets",
                recommendation="Review the last scrape errors on the Prometheus Targets page.",
                reference="https://prometheus.io/docs/prometheus/latest/querying/api/#targets",
            ))

        failed_rules = sum(
            rule["health"] == "err"
            for group in self.collector.get_rule_groups()
            for rule in group["rules"]
        )
        if failed_rules:
            recommendations.append(Recommendation(
                severity="high",
                category="Rules",
                internal_cause=f"Rule evaluation failures ({failed_rules})",
                impact="Affected recording rules or alerts may be stale or missing",
                recommendation="Review the evaluation errors on the Prometheus Rules page.",
                reference="https://prometheus.io/docs/prometheus/latest/querying/api/#rules",
            ))
        return recommendations
