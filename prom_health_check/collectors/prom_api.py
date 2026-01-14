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
        self.prom_url = prom_url
        self.client = client or httpx.Client()

    def get_config(self) -> PrometheusConfig:
        """
        Get the Prometheus configuration.

        Returns:
            A PrometheusConfig object.
        """
        response = self.client.get(f"{self.prom_url}/api/v1/status/config")
        response.raise_for_status()
        config_data = response.json()
        return PrometheusConfig(yaml=config_data["data"]["yaml"])

    def get_flags(self) -> PrometheusFlags:
        """
        Get the Prometheus flags.

        Returns:
            A PrometheusFlags object.
        """
        response = self.client.get(f"{self.prom_url}/api/v1/status/flags")
        response.raise_for_status()
        return PrometheusFlags(flags=response.json()["data"])

    def get_tsdb_status(self) -> TsdbStatus:
        """
        Get the Prometheus TSDB status.

        Returns:
            A TsdbStatus object.
        """
        response = self.client.get(f"{self.prom_url}/api/v1/status/tsdb")
        response.raise_for_status()
        return TsdbStatus(**response.json()["data"])
        
    def get_buildinfo(self) -> PrometheusBuildInfo:
        """
        Get the Prometheus build information.

        Returns:
            A PrometheusBuildInfo object.
        """
        response = self.client.get(f"{self.prom_url}/api/v1/status/buildinfo")
        response.raise_for_status()
        buildinfo_data = response.json()
        return PrometheusBuildInfo(**buildinfo_data["data"])

    def query(self, query: str) -> Dict[str, Any]:
        """
        Execute a PromQL query.

        Args:
            query: The PromQL query string.

        Returns:
            A dictionary representing the query result.
        """
        response = self.client.get(f"{self.prom_url}/api/v1/query", params={"query": query})
        response.raise_for_status()
        return response.json()["data"]
