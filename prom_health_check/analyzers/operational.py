from prom_health_check.collectors.prom_api import PrometheusAPICollector
from prom_health_check.models.prometheus import Recommendation


class OperationalAnalyzer:
    def __init__(self, collector: PrometheusAPICollector):
        self.collector = collector

    def _query_count(self, query: str) -> int:
        result = self.collector.query(query)["result"]
        return int(result[0]["value"][1]) if result else 0

    def analyze(self) -> list[Recommendation]:
        recommendations = []
        target_count = self._query_count("count(up)")
        down_count = self._query_count("count(up == 0)") if target_count else 0
        if not target_count:
            recommendations.append(Recommendation(
                severity="low",
                category="Scraping",
                internal_cause="No active scrape targets observed",
                impact="There are no recent up samples to assess scrape health",
                recommendation="If scraping is expected and Prometheus has had time to scrape, check scrape configuration, service discovery, and relabeling.",
                reference="https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config",
            ))
        elif down_count:
            recommendations.append(Recommendation(
                severity="high",
                category="Scraping",
                internal_cause=f"Scrape failures on {down_count} of {target_count} active targets",
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
