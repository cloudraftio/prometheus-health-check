# Prometheus Support Tool

This tool is designed to help you diagnose and troubleshoot your Prometheus setup. It runs a series of health checks and provides a detailed report with recommendations.

## Installation

To install the necessary dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Usage

To run the health checks against a Prometheus instance, use the following command:

```bash
python3 -m prom_health_check
```

By default, the tool will connect to a Prometheus server at `http://localhost:9090` and generate an HTML report named `prometheus_health_report.html`.

You can customize the behavior of the tool using the following options:

*   `--prom-url`: The URL of the Prometheus server to check. You can also set the `PROM_URL` environment variable.
*   `--output-format`: The output format for the health check report. Supported formats are `html` and `json`. You can also set the `OUTPUT_FORMAT` environment variable.

Example:

```bash
python3 -m prom_health_check --prom-url http://my-prometheus:9090 --output-format json
```

Pass the full base URL when Prometheus uses a route prefix (for example, `https://monitor.example.com/prometheus/`). The report requires **Prometheus server mode**; Agent mode does not expose the TSDB and PromQL APIs used by the check.

## Features

-   **Comprehensive Health Checks**: The tool runs a range of checks on your Prometheus server's configuration and TSDB status.
-   **Scrape and Rule Health**: Uses the last `up` sample per series within one hour to detect missing or down scrapes without downloading target labels, and checks for failed rule evaluations. A new server may not have scrape samples yet, and recently removed targets may still be counted in that window.
    If the server receives remote-written `up` samples, the counts include upstream scrapes: a reported failure may be upstream rather than local. Check the receiving server's own **Targets** page to confirm which local scrapes are failing.
-   **Performance**: Reports the maximum GC pause from the Go runtime summary and p99/average PromQL evaluation duration (not including queue time). If both classic and native histograms provide a p99 estimate, the report shows the higher estimate, not a combined percentile. These metrics require Prometheus self-metrics to be scraped and enough data to evaluate them. The former `gc_pause_time_p99` JSON field remains present for compatibility; use `gc_pause_time_max` for the current check.
-   **Detailed Reports**: The health check report can be generated in a user-friendly HTML format or as a JSON object for programmatic use.
-   **Easy to Extend**: The tool is designed to be easily extensible. You can add your own health checks by creating new Python modules in the `prom_health_check/analyzers` directory.

## Contributing

Contributions are welcome! If you have a new health check that you'd like to add, please open a pull request.
