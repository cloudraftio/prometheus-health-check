import typer
from typing_extensions import Annotated
import prom_health_check
from rich.console import Console

# Used to gracefully exit the CLI on an error
err_console = Console(stderr=True, style="bold red")

# Create the typer app
app = typer.Typer(
    add_completion=False,
    help="A command line tool to perform health checks on Prometheus.",
    name="prom-healthcheck",
)

# Add a command to the app
@app.command()
def run(
    prom_url: Annotated[
        str,
        typer.Option(
            "--prom-url",
            help="The URL of the Prometheus server to check.",
            envvar="PROM_URL",
        ),
    ] = "http://localhost:9090",
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            help="The output format for the health check report.",
            envvar="OUTPUT_FORMAT",
        ),
    ] = "html",
) -> None:
    """
    Perform a health check on a Prometheus server.
    """
    err_console.print(f"Running health check on {prom_url} with output format {output_format}")

    from prom_health_check.collectors.prom_api import PrometheusAPICollector
    from prom_health_check.analyzers.tsdb import TsdbAnalyzer
    from prom_health_check.analyzers.config import ConfigAnalyzer
    from prom_health_check.analyzers.metrics import MetricsAnalyzer
    from prom_health_check.renderers.json import JsonRenderer
    from prom_health_check.renderers.html import HtmlRenderer
    from prom_health_check.models.prometheus import HealthReport

    collector = PrometheusAPICollector(prom_url)

    try:
        config = collector.get_config()
        flags = collector.get_flags()
        buildinfo = collector.get_buildinfo()
        tsdb_status = collector.get_tsdb_status()

        tsdb_analyzer = TsdbAnalyzer(tsdb_status)
        config_analyzer = ConfigAnalyzer(config)
        metrics_analyzer = MetricsAnalyzer(collector)

        metrics_analysis_result = metrics_analyzer.analyze()
        recommendations = (
            tsdb_analyzer.analyze()
            + config_analyzer.analyze()
            + metrics_analysis_result["recommendations"]
        )

        score = 100 - (len(recommendations) * 10)
        if score < 0:
            score = 0

        if score >= 90:
            score_category = "Production-grade"
            score_category_class = "score-production-grade"
        elif score >= 70:
            score_category = "Needs tuning"
            score_category_class = "score-needs-tuning"
        else:
            score_category = "High operational risk"
            score_category_class = "score-high-risk"

        report = HealthReport(
            score=score,
            score_category=score_category,
            score_category_class=score_category_class,
            recommendations=recommendations,
            prometheus_config=config,
            prometheus_flags=flags,
            tsdb_status=tsdb_status,
            prometheus_build_info=buildinfo,
            **metrics_analysis_result["metrics"],
        )

        if output_format == "json":
            renderer = JsonRenderer(report)
            print(renderer.render())
        else:
            renderer = HtmlRenderer(report)
            with open("prometheus_health_report.html", "w") as f:
                f.write(renderer.render())
            err_console.print("Health check report saved to prometheus_health_report.html")

    except Exception as e:
        err_console.print(f"Error fetching data from Prometheus: {e}")
        raise typer.Exit(code=1)

def main() -> None:
    """
    Run the main CLI app
    """
    app()

if __name__ == "__main__":
    main()