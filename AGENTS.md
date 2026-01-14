# AGENTS.md

## Overview

Prometheus Health Check tool is designed to collect the data from a Prometheus instance for analysis, troubleshooting and finding common issues. The tool is designed to help SREs and support engineers to get data from air-gapped environments.  It doesn't collect any sensitive information.

This document provides essential context for contributors, especially those building or extending automated agents, analyzers, or integrations within this codebase.

---

## Project Purpose

This tool is designed to **diagnose and troubleshoot Prometheus setups**. It performs automated health checks, analyzes Prometheus metrics and configuration, and generates actionable reports (HTML/JSON) with recommendations for improving reliability, performance, and maintainability.

---

## Key Concepts

### 1. **Collectors**
- **Purpose:** Fetch data from Prometheus APIs (e.g., config, flags, TSDB status, metrics).
- **Location:** `prom_health_check/collectors/`
- **Example:** `PrometheusAPICollector` handles HTTP requests to Prometheus endpoints.

### 2. **Analyzers**
- **Purpose:** Analyze collected data and generate recommendations.
- **Location:** `prom_health_check/analyzers/`
- **Examples:**
  - `tsdb.py`: Checks TSDB health, cardinality, and memory usage.
  - `metrics.py`: Analyzes runtime metrics (e.g., compactions, churn, query performance).
  - `config.py`: Validates Prometheus configuration best practices.

### 3. **Models**
- **Purpose:** Define data structures for configs, metrics, recommendations, and reports.
- **Location:** `prom_health_check/models/`
- **Example:** `HealthReport`, `Recommendation`, `Metric`.

### 4. **Renderers**
- **Purpose:** Generate human-readable reports (HTML, JSON) from analysis results.
- **Location:** `prom_health_check/renderers/`
- **Example:** `HtmlRenderer` uses Jinja templates for report generation.

---

## Agent/Analyzer Development Guidelines

- **Stateless:** Agents/analyzers should not maintain state between runs.
- **Extensible:** Add new analyzers by creating a module in `analyzers/` and integrating it in the CLI pipeline.
- **Recommendations:** Use the `Recommendation` model for all findings. Include severity, category, impact, and actionable advice.
- **Metrics:** If your agent collects new metrics, update the `HealthReport` model and the relevant renderer/template.
- **Performance:** Avoid expensive queries or operations that could overload the Prometheus server.

---

## Adding a New Agent/Analyzer

1. **Create a new file** in `prom_health_check/analyzers/` (e.g., `my_analyzer.py`).
2. **Implement a class** with an `analyze()` method that returns a list of `Recommendation` objects or a dict with metrics.
3. **Update the CLI pipeline** in `cli/main.py` to invoke your analyzer and merge its results into the `HealthReport`.
4. **Update models** in `models/prometheus.py` if you introduce new report fields.
5. **Update renderers/templates** to display new findings or metrics.

---

## Example: Adding a Query Performance Analyzer

- **Collector:** Use `PrometheusAPICollector.query()` to fetch metrics like `prometheus_engine_query_duration_seconds`.
- **Analyzer:** Compute p99/average durations, add recommendations if thresholds are exceeded.
- **Report:** Add fields to `HealthReport` and display them in the HTML report.

---

## Testing

- Add or update tests in the `tests/` directory.
- Use realistic Prometheus data or mock responses for unit tests.

---

## Documentation

- Prometheus documentation is available in the `prom/docs/` directory for more accurate context.

## Contribution Tips

- Follow PEP8 and existing code style.
- Document new analyzers and metrics clearly.
- Keep recommendations actionable and reference official Prometheus docs where possible.
- Open a pull request with a clear description of your changes.

---


## Questions?

If you have questions about the agent/analyzer architecture or want to propose a new health check, open an issue or discussion on GitHub.

---

Happy contributing!
