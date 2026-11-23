from pydantic import BaseModel, RootModel
from typing import List, Dict, Optional

class PrometheusConfig(BaseModel):
    """Pydantic model for Prometheus configuration."""
    yaml: str

class PrometheusFlags(BaseModel):
    """Pydantic model for Prometheus flags."""
    flags: Dict[str, str]

class Metric(BaseModel):
    """Pydantic model for a metric."""
    name: str
    value: float


class TsdbStatus(BaseModel):
    """Pydantic model for Prometheus TSDB status."""
    headStats: Dict
    seriesCountByMetricName: List[Metric]
    labelValueCountByLabelName: List[Metric]
    memoryInBytesByLabelName: List[Metric]

class Recommendation(BaseModel):
    """Pydantic model for a recommendation."""
    severity: str
    category: str
    internal_cause: str
    impact: str
    recommendation: str
    reference: str

class PrometheusBuildInfo(BaseModel):
    """Pydantic model for Prometheus build information."""
    version: str
    revision: str
    branch: str
    buildUser: str
    buildDate: str
    goVersion: str

class HealthReport(BaseModel):
    """Pydantic model for the health report."""
    score: float
    score_category: Optional[str] = None
    score_category_class: Optional[str] = None
    recommendations: List[Recommendation]
    prometheus_config: Optional[PrometheusConfig] = None
    prometheus_flags: Optional[PrometheusFlags] = None
    tsdb_status: Optional[TsdbStatus] = None
    prometheus_build_info: Optional[PrometheusBuildInfo] = None
    series_churn_rate: Optional[float] = None
    gc_pause_time_p99: Optional[float] = None
    gc_pause_time_max: Optional[float] = None
    failed_compactions: Optional[int] = None
    query_duration_p99: Optional[float] = None
    query_duration_avg: Optional[float] = None
