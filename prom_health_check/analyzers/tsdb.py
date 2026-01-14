from prom_health_check.models.prometheus import TsdbStatus, Recommendation

class TsdbAnalyzer:
    """
    A class to analyze the Prometheus TSDB status.
    """

    def __init__(self, tsdb_status: TsdbStatus):
        """
        Initialize the TsdbAnalyzer.

        Args:
            tsdb_status: A TsdbStatus object.
        """
        self.tsdb_status = tsdb_status

    def analyze(self) -> list[Recommendation]:
        """
        Analyze the TSDB status and provide recommendations.

        Returns:
            A list of Recommendation objects.
        """
        recommendations = []

        # Analyze head stats
        if self.tsdb_status.headStats["numSeries"] > 1000000:
            recommendations.append(
                Recommendation(
                    severity="critical",
                    category="TSDB",
                    internal_cause="Excessive head block growth",
                    impact="High memory usage, slow compaction",
                    recommendation="Reduce scrape interval or introduce recording rules",
                    reference="Prometheus TSDB design",
                )
            )

        # Analyze series count by metric name
        for metric in self.tsdb_status.seriesCountByMetricName:
            if metric.value > 100000:
                recommendations.append(
                    Recommendation(
                        severity="high",
                        category="Cardinality",
                        internal_cause="High series count for a single metric",
                        impact="Increased memory usage, slower queries",
                        recommendation=f"Investigate the metric '{metric.name}' for high cardinality labels",
                        reference="https://prometheus.io/docs/practices/naming/#labels-and-metrics",
                    )
                )

        # Analyze label value count by label name
        for metric in self.tsdb_status.labelValueCountByLabelName:
            if metric.value > 1000:
                recommendations.append(
                    Recommendation(
                        severity="high",
                        category="Cardinality",
                        internal_cause="High cardinality for a single label",
                        impact="Increased memory usage, slower queries",
                        recommendation=f"Investigate the label '{metric.name}' for high cardinality values",
                        reference="https://prometheus.io/docs/practices/naming/#labels-and-metrics",
                    )
                )

        # Analyze memory in bytes by label name
        for metric in self.tsdb_status.memoryInBytesByLabelName:
            if metric.value > 100000000: # 100MB
                recommendations.append(
                    Recommendation(
                        severity="high",
                        category="Memory",
                        internal_cause="High memory usage for a single label",
                        impact="Increased memory usage",
                        recommendation=f"Investigate the label '{metric.name}' for high memory usage",
                        reference="Prometheus memory usage",
                    )
                )

        return recommendations
