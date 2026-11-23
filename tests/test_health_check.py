import json
import unittest
from unittest.mock import mock_open, patch

import httpx
from typer.testing import CliRunner

from prom_health_check.cli.main import app
from prom_health_check.collectors.prom_api import PrometheusAPICollector


class TestHealthCheck(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.base_url = "http://localhost:9090/prometheus/"
        self.config = 'global: {scrape_interval: 1m30s, external_labels: {note: "München <edge> & QA"}}'
        self.responses = {
            "status/config": {"yaml": self.config},
            "status/flags": {"agent": "false"},
            "status/buildinfo": dict.fromkeys(
                ["version", "revision", "branch", "buildUser", "buildDate", "goVersion"],
                "3.16.0",
            ),
            "status/tsdb": {
                "headStats": {
                    "numSeries": 0,
                    "chunkCount": 0,
                    "minTime": 9223372036854775807,
                    "maxTime": -9223372036854775808,
                },
                "seriesCountByMetricName": [],
                "labelValueCountByLabelName": [],
                "memoryInBytesByLabelName": [],
            },
            "rules": {"groups": []},
            "query": {"resultType": "vector", "result": []},
        }

    def handler(self, request):
        endpoint = request.url.path.removeprefix("/prometheus/api/v1/")
        return httpx.Response(200, json={"status": "success", "data": self.responses[endpoint]})

    def invoke(self, handler=None, output_format="json"):
        with httpx.Client(transport=httpx.MockTransport(handler or self.handler)) as client:
            collector = PrometheusAPICollector(self.base_url, client=client)
            with patch("prom_health_check.collectors.prom_api.PrometheusAPICollector", return_value=collector):
                return self.runner.invoke(app, ["--prom-url", self.base_url, "--output-format", output_format])

    def test_empty_head_with_prefixed_url(self):
        result = self.invoke()
        self.assertEqual(result.exit_code, 0, result.output)
        report = json.loads(result.stdout)
        self.assertIsNone(report["tsdb_status"]["headStats"]["minTime"])
        self.assertIsNone(report["tsdb_status"]["headStats"]["maxTime"])
        self.assertEqual(report["recommendations"][0]["internal_cause"], "No active scrape targets observed")

    def test_empty_head_and_utf8_text_render_in_html(self):
        with patch("prom_health_check.cli.main.open", mock_open()) as report_file:
            result = self.invoke(output_format="html")
            self.assertEqual(result.exit_code, 0, result.output)
            report_file.assert_called_once_with("prometheus_health_report.html", "w", encoding="utf-8")
            report = report_file().write.call_args.args[0]
        self.assertIn("Min Time:</strong> N/A", report)
        self.assertIn("Max Time:</strong> N/A", report)
        self.assertIn("München &lt;edge&gt; &amp; QA", report)
        self.assertNotIn("<edge>", report)

    def test_agent_mode_is_detected_before_server_only_requests(self):
        self.responses["status/flags"]["agent"] = "true"
        del self.responses["status/tsdb"]
        result = self.invoke()
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Prometheus Agent mode", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_unexpected_http_response_identifies_endpoint(self):
        for response, message in [
            (httpx.Response(401), "returned HTTP 401"),
            (httpx.Response(200, text="<html>login</html>"), "did not return JSON"),
            (httpx.Response(200, json={"status": "error"}), "did not return a successful Prometheus API response"),
        ]:
            with self.subTest(message=message):
                result = self.invoke(lambda request: response)
                self.assertEqual(result.exit_code, 1)
                self.assertIn("/api/v1/status/config", result.stderr)
                self.assertIn(message, " ".join(result.stderr.split()))

    def test_snapshot_detects_down_targets_and_failed_rules(self):
        self.responses["rules"]["groups"] = [
            {"rules": [{"health": "ok"}, {"health": "err"}]},
            {"rules": [{"health": "unknown"}, {"health": "err"}]},
        ]
        def handler(request):
            if request.url.path.endswith("/query"):
                value = {
                    "count(last_over_time(up[1h]))": "3",
                    "count(last_over_time(up[1h]) == 0)": "1",
                }.get(request.url.params["query"])
                self.responses["query"]["result"] = [{"value": [0, value]}] if value is not None else []
            return self.handler(request)

        result = self.invoke(handler)
        self.assertEqual(result.exit_code, 0, result.output)
        recommendations = json.loads(result.stdout)["recommendations"]
        causes = [entry["internal_cause"] for entry in recommendations]
        self.assertEqual(causes, ["Scrape failures on 1 of 3 observed targets", "Rule evaluation failures (2)"])
        self.assertIn("remote-written up samples", recommendations[0]["recommendation"])
        self.assertIn("own Targets page", recommendations[0]["recommendation"])

    def test_unavailable_operational_check_does_not_hide_other_findings(self):
        self.responses["rules"]["groups"] = [{"rules": [{"health": "err"}]}]
        for blocked_endpoint, skipped, cause in [
            ("/query", "scrape health", "Rule evaluation failures (1)"),
            ("/rules", "rule health", "No active scrape targets observed"),
        ]:
            with self.subTest(blocked_endpoint=blocked_endpoint):
                def handler(request):
                    if request.url.path.endswith(blocked_endpoint):
                        return httpx.Response(403)
                    return self.handler(request)

                with self.assertLogs("prom_health_check.analyzers.operational", level="WARNING") as logs:
                    result = self.invoke(handler)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn(f"Could not check {skipped}", logs.output[0])
                causes = [entry["internal_cause"] for entry in json.loads(result.stdout)["recommendations"]]
                self.assertEqual(causes, [cause])

    def test_timeout_identifies_endpoint(self):
        def timeout(request):
            raise httpx.ReadTimeout("timed out", request=request)

        result = self.invoke(timeout)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("/api/v1/status/config request failed (ReadTimeout)", result.stderr)

    def test_latest_self_metrics(self):
        samples = {
            'max(go_gc_duration_seconds{quantile=~"1|1[.]0"})': "0.2",
            'histogram_quantile(0.99, sum by (le) (rate(prometheus_engine_query_duration_histogram_seconds_bucket{slice="inner_eval"}[5m])))': "2.5",
            'sum(rate(prometheus_engine_query_duration_seconds_sum{slice="inner_eval"}[5m]))': "10",
            'sum(rate(prometheus_engine_query_duration_seconds_count{slice="inner_eval"}[5m]))': "4",
        }

        def handler(request):
            if request.url.path.endswith("/query"):
                value = samples.get(request.url.params["query"])
                self.responses["query"]["result"] = [{"value": [0, value]}] if value is not None else []
            return self.handler(request)

        result = self.invoke(handler)
        self.assertEqual(result.exit_code, 0, result.output)
        report = json.loads(result.stdout)
        self.assertEqual(report["gc_pause_time_max"], 0.2)
        self.assertEqual(report["query_duration_p99"], 2.5)
        self.assertEqual(report["query_duration_avg"], 2.5)
        causes = [entry["internal_cause"] for entry in report["recommendations"]]
        self.assertIn("High GC pause time", causes)
        self.assertIn("High p99 PromQL evaluation duration", causes)

    def test_query_p99_falls_back_to_native_histogram(self):
        queries = []
        native_query = (
            'histogram_quantile(0.99, sum(rate('
            'prometheus_engine_query_duration_histogram_seconds{slice="inner_eval"}[5m])))'
        )

        def handler(request):
            if request.url.path.endswith("/query"):
                query = request.url.params["query"]
                queries.append(query)
                self.responses["query"]["result"] = [{"value": [0, "3.5"]}] if query == native_query else []
            return self.handler(request)

        result = self.invoke(handler)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("_bucket", queries[queries.index(native_query) - 1])
        self.assertEqual(json.loads(result.stdout)["query_duration_p99"], 3.5)

    def test_query_p99_uses_maximum_finite_histogram_estimate(self):
        for classic, native, expected in [("1", "3.5", 3.5), ("4", "1", 4.0), ("NaN", "2.5", 2.5)]:
            with self.subTest(classic=classic, native=native):
                def handler(request):
                    if request.url.path.endswith("/query"):
                        query = request.url.params["query"]
                        samples = []
                        if query.startswith("histogram_quantile("):
                            value = classic if "_bucket" in query else native
                            samples = [{"value": [0, value]}]
                        self.responses["query"]["result"] = samples
                    return self.handler(request)

                result = self.invoke(handler)
                self.assertEqual(result.exit_code, 0, result.output)
                report = json.loads(result.stdout)
                self.assertEqual(report["query_duration_p99"], expected)
                causes = [entry["internal_cause"] for entry in report["recommendations"]]
                self.assertEqual(causes.count("High p99 PromQL evaluation duration"), 1)
