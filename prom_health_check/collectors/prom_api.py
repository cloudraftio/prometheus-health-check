import httpx
from typing import Dict, Any, Optional
from prom_health_check.models.prometheus import (
    PrometheusConfig,
    PrometheusFlags,
    TsdbStatus,
    PrometheusBuildInfo,
)

class PrometheusAPICollector:
    """
    A class to collect data from the Prometheus API.
    """

    def __init__(self, prom_url: str, client: Optional[httpx.Client] = None):
        """
        Initialize the PrometheusAPICollector.

        Args:
            prom_url: The URL of the Prometheus server.
            client: An optional httpx.Client to use for requests.
        """
        self.prom_url = prom_url.rstrip("/")
        self.client = client or httpx.Client()

    def _get_data(self, endpoint: str, **kwargs) -> dict:
        try:
            response = self.client.get(f"{self.prom_url}/api/v1/{endpoint}", **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ValueError(f"/api/v1/{endpoint} returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ValueError(f"/api/v1/{endpoint} request failed ({type(exc).__name__}): {exc}") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError(f"/api/v1/{endpoint} did not return JSON") from exc
        if not isinstance(payload, dict) or payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
            raise ValueError(f"/api/v1/{endpoint} did not return a successful Prometheus API response")
        return payload["data"]

    def get_config(self) -> PrometheusConfig:
        """
        Get the Prometheus configuration.

        Returns:
            A PrometheusConfig object.
        """
        return PrometheusConfig(yaml=self._get_data("status/config")["yaml"])

    def get_flags(self) -> PrometheusFlags:
        """
        Get the Prometheus flags.

        Returns:
            A PrometheusFlags object.
        """
        return PrometheusFlags(flags=self._get_data("status/flags"))

    def get_tsdb_status(self) -> TsdbStatus:
        """
        Get the Prometheus TSDB status.

        Returns:
            A TsdbStatus object.
        """
        status = TsdbStatus(**self._get_data("status/tsdb"))
        head = status.headStats
        if head["minTime"] > head["maxTime"]:
            head.update(minTime=None, maxTime=None)
        return status
        
    def get_buildinfo(self) -> PrometheusBuildInfo:
        """
        Get the Prometheus build information.

        Returns:
            A PrometheusBuildInfo object.
        """
        return PrometheusBuildInfo(**self._get_data("status/buildinfo"))

    def get_active_targets(self) -> list[dict]:
        return self._get_data("targets", params={"state": "active"})["activeTargets"]

    def get_rule_groups(self) -> list[dict]:
        return self._get_data("rules", params={"exclude_alerts": "true"})["groups"]

    def query(self, query: str) -> Dict[str, Any]:
        """
        Execute a PromQL query.

        Args:
            query: The PromQL query string.

        Returns:
            A dictionary representing the query result.
        """
        return self._get_data("query", params={"query": query})
