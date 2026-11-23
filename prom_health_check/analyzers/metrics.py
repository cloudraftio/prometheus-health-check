from prom_health_check.collectors.prom_api import PrometheusAPICollector
from prom_health_check.models.prometheus import Recommendation
import math

class MetricsAnalyzer:
    """
    A class to analyze Prometheus metrics.
    """

    def __init__(self, collector: PrometheusAPICollector):
        """
        Initialize the MetricsAnalyzer.

        Args:
            collector: A PrometheusAPICollector object.
        """
        self.collector = collector

    def analyze(self) -> dict:
        """
        Analyze Prometheus metrics and provide recommendations.

        Returns:
            A dictionary with recommendations and collected metrics.
        """
        recommendations = []
        metrics = {}

        # Check for failed compactions
        try:
            failed_compactions_result = self.collector.query("prometheus_tsdb_compactions_failed_total")
            if failed_compactions_result and failed_compactions_result["result"]:
                for result in failed_compactions_result["result"]:
                    failed_compactions_value = int(result["value"][1])
                    metrics['failed_compactions'] = failed_compactions_value
                    if failed_compactions_value > 0:
                        recommendations.append(
                            Recommendation(
                                severity="critical",
                                category="TSDB",
                                internal_cause="Failed compactions",
                                impact="Data loss, query failures",
                                recommendation="Investigate the cause of the failed compactions. Check the Prometheus logs for more details.",
                                reference="Prometheus TSDB",
                            )
                        )
                        break # Only one recommendation is needed
        except Exception:
            # The metric might not be present
            pass

        # Check for series churn
        try:
            series_churn_result = self.collector.query("rate(prometheus_tsdb_head_series_created_total[5m])")
            if series_churn_result and series_churn_result["result"]:
                for result in series_churn_result["result"]:
                    series_churn_value = float(result["value"][1])
                    metrics['series_churn_rate'] = series_churn_value
                    if series_churn_value > 100:
                        recommendations.append(
                            Recommendation(
                                severity="high",
                                category="Cardinality",
                                internal_cause="High series churn rate",
                                impact="Increased memory usage, slower queries",
                                recommendation="Investigate the source of the new series. This could be due to high cardinality labels.",
                                reference="Prometheus series churn",
                            )
                        )
                        break
        except Exception:
            pass

        # Check for GC pause time
        try:
            gc_pause_result = self.collector.query('max(go_gc_duration_seconds{quantile=~"1|1[.]0"})')
            if gc_pause_result and gc_pause_result["result"]:
                for result in gc_pause_result["result"]:
                    gc_pause_value = float(result["value"][1])
                    if not math.isfinite(gc_pause_value):
                        continue
                    metrics['gc_pause_time_max'] = gc_pause_value
                    if gc_pause_value > 0.1: # 100ms
                        recommendations.append(
                            Recommendation(
                                severity="high",
                                category="Performance",
                                internal_cause="High GC pause time",
                                impact="Slows down Prometheus, can cause gaps in scrapes",
                                recommendation="Tune Go GC parameters (GOGC), or reduce memory usage.",
                                reference="Go GC tuning",
                            )
                        )
                        break
        except Exception:
            pass

        # Query performance aggregation
        try:
            p99_result = self.collector.query(
                'histogram_quantile(0.99, sum by (le) (rate(prometheus_engine_query_duration_histogram_seconds_bucket{slice="inner_eval"}[5m])))'
            )
            if not p99_result or not p99_result["result"]:
                p99_result = self.collector.query(
                    'histogram_quantile(0.99, sum(rate(prometheus_engine_query_duration_histogram_seconds{slice="inner_eval"}[5m])))'
                )
            if p99_result and p99_result["result"]:
                for result in p99_result["result"]:
                    p99_value = float(result["value"][1])
                    if not math.isfinite(p99_value):
                        continue
                    metrics['query_duration_p99'] = p99_value
                    if p99_value > 2.0:
                        recommendations.append(
                            Recommendation(
                                severity="high",
                                category="Query Performance",
                                internal_cause="High p99 PromQL evaluation duration",
                                impact="Slow queries can impact user experience and Prometheus performance",
                                recommendation="Investigate slow queries using Prometheus metrics and consider optimizing them.",
                                reference="https://prometheus.io/docs/prometheus/latest/querying/troubleshooting/",
                            )
                        )
                    break

            avg_sum_result = self.collector.query(
                'sum(rate(prometheus_engine_query_duration_seconds_sum{slice="inner_eval"}[5m]))'
            )
            avg_count_result = self.collector.query(
                'sum(rate(prometheus_engine_query_duration_seconds_count{slice="inner_eval"}[5m]))'
            )
            avg_value = None
            if (
                avg_sum_result and avg_sum_result["result"]
                and avg_count_result and avg_count_result["result"]
            ):
                sum_val = float(avg_sum_result["result"][0]["value"][1])
                count_val = float(avg_count_result["result"][0]["value"][1])
                if count_val > 0:
                    avg_value = sum_val / count_val
                    metrics['query_duration_avg'] = avg_value
        except Exception:
            pass

        return {"recommendations": recommendations, "metrics": metrics}
