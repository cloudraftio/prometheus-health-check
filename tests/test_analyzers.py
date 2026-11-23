import unittest
from prom_health_check.analyzers.tsdb import TsdbAnalyzer
from prom_health_check.analyzers.config import ConfigAnalyzer
from prom_health_check.models.prometheus import TsdbStatus, PrometheusConfig

class TestAnalyzers(unittest.TestCase):

    def test_tsdb_analyzer(self):
        # Test with high number of series
        tsdb_status = TsdbStatus(
            headStats={"numSeries": 2000000},
            seriesCountByMetricName=[
                {"name": "test_metric", "value": "200000"}
            ],
            labelValueCountByLabelName=[],
            memoryInBytesByLabelName=[]
        )
        analyzer = TsdbAnalyzer(tsdb_status)
        recommendations = analyzer.analyze()
        self.assertEqual(len(recommendations), 2)
        self.assertEqual(recommendations[0].severity, "critical")
        self.assertEqual(recommendations[1].severity, "high")

        # Test with normal number of series
        tsdb_status = TsdbStatus(
            headStats={"numSeries": 500000},
            seriesCountByMetricName=[
                {"name": "test_metric", "value": "50000"}
            ],
            labelValueCountByLabelName=[],
            memoryInBytesByLabelName=[]
        )
        analyzer = TsdbAnalyzer(tsdb_status)
        recommendations = analyzer.analyze()
        self.assertEqual(len(recommendations), 0)

    def test_config_analyzer(self):
        # Test with low scrape interval
        config = PrometheusConfig(
            yaml="global: {scrape_interval: 5s}"
        )
        analyzer = ConfigAnalyzer(config)
        recommendations = analyzer.analyze()
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].severity, "low")

        # Test with normal scrape interval
        config = PrometheusConfig(
            yaml="global: {scrape_interval: 15s}"
        )
        analyzer = ConfigAnalyzer(config)
        recommendations = analyzer.analyze()
        self.assertEqual(len(recommendations), 0)

    def test_prometheus_duration_units(self):
        for interval, expected in [("500ms", 1), ("14s999ms", 1), ("15s1ms", 0), ("1m30s", 0), ("1h", 0)]:
            with self.subTest(interval=interval):
                config = PrometheusConfig(yaml=f"global: {{scrape_interval: {interval}}}")
                self.assertEqual(len(ConfigAnalyzer(config).analyze()), expected)

if __name__ == "__main__":
    unittest.main()