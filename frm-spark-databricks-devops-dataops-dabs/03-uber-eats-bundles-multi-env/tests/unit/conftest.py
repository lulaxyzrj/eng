"""
Fixtures for Bronze layer unit tests.

FakeSpark and FakeDLT mock Databricks runtime components,
allowing tests to run on plain Python (no Spark cluster needed).
"""

import pytest
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Fake Spark Components
# ---------------------------------------------------------------------------

class FakeColumn:
    """Mimics pyspark.sql.Column for select() assertions."""

    def __init__(self, expr: str):
        self.expr = expr

    def alias(self, name: str) -> "FakeColumn":
        return FakeColumn(f"{self.expr} AS {name}")

    def __repr__(self) -> str:
        return self.expr


class FakeDataFrame:
    """Minimal DataFrame stub that captures select() calls."""

    def __init__(self, source: str):
        self.source = source
        self.selected_columns: list[str] = []

    def select(self, *cols) -> "FakeDataFrame":
        self.selected_columns = [str(c) for c in cols]
        return self


@dataclass
class FakeStreamReader:
    """
    Mimics Spark's DataStreamReader API.
    Captures all method calls for assertion.
    """

    calls: list[tuple[str, Any]] = field(default_factory=list)
    _options: dict = field(default_factory=dict)
    _format: str = ""
    _path: str = ""

    def format(self, fmt: str) -> "FakeStreamReader":
        self.calls.append(("format", fmt))
        self._format = fmt
        return self

    def option(self, key: str, value: Any) -> "FakeStreamReader":
        self.calls.append(("option", (key, value)))
        self._options[key] = value
        return self

    def load(self, path: str) -> FakeDataFrame:
        self.calls.append(("load", path))
        self._path = path
        return FakeDataFrame(source=path)


@dataclass
class FakeConf:
    """Mimics spark.conf for pipeline parameters."""

    _values: dict = field(default_factory=dict)

    def get(self, key: str, default: str = "") -> str:
        return self._values.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._values[key] = value


@dataclass
class FakeSparkSession:
    """
    Minimal SparkSession stub.
    Captures readStream calls without needing a real cluster.
    """

    conf: FakeConf = field(default_factory=FakeConf)
    _stream_reader: FakeStreamReader = field(default_factory=FakeStreamReader)

    @property
    def readStream(self) -> FakeStreamReader:
        return self._stream_reader


# ---------------------------------------------------------------------------
# Fake DLT Components
# ---------------------------------------------------------------------------

@dataclass
class FakeDLTTable:
    """Captures @dlt.table decorator parameters."""

    name: str
    comment: str
    table_properties: dict
    func: callable


class FakeDLT:
    """
    Mocks the dlt module.
    Captures table registrations for assertion.
    """

    def __init__(self):
        self.tables: dict[str, FakeDLTTable] = {}

    def table(
        self,
        name: str = "",
        comment: str = "",
        table_properties: dict = None,
    ):
        """Decorator that captures table definition."""
        def decorator(func):
            self.tables[name] = FakeDLTTable(
                name=name,
                comment=comment,
                table_properties=table_properties or {},
                func=func,
            )
            return func
        return decorator


# ---------------------------------------------------------------------------
# Fake PySpark Functions
# ---------------------------------------------------------------------------

class FakeFunctions:
    """Mimics pyspark.sql.functions module."""

    @staticmethod
    def col(name: str) -> FakeColumn:
        return FakeColumn(name)

    @staticmethod
    def current_timestamp() -> FakeColumn:
        return FakeColumn("current_timestamp()")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_spark() -> FakeSparkSession:
    """Provides a fresh FakeSparkSession per test."""
    spark = FakeSparkSession()
    spark.conf.set("pipeline.landing_path", "/mnt/landing")
    spark.conf.set("pipeline.bronze_schema", "bronze")
    return spark


@pytest.fixture
def fake_dlt() -> FakeDLT:
    """Provides a fresh FakeDLT instance per test."""
    return FakeDLT()


@pytest.fixture
def fake_functions() -> FakeFunctions:
    """Provides fake pyspark.sql.functions."""
    return FakeFunctions()


# ---------------------------------------------------------------------------
# Bronze Layer Specifications (from DATA_CATALOG.md)
# ---------------------------------------------------------------------------

BRONZE_SPECS = {
    "kafka_orders": {
        "source_path": "kafka/orders/*.jsonl",
        "schema_location": "/_schemas/kafka/orders",
        "z_order_col": "order_id",
        "comment": "Raw orders from landing zone.",
    },
    "kafka_order_status": {
        "source_path": "kafka/status/*.jsonl",
        "schema_location": "/_schemas/kafka/status",
        "z_order_col": "order_identifier",
        "comment": "Raw order status transitions (state machine).",
    },
    "kafka_payments": {
        "source_path": "kafka/payments/*.jsonl",
        "schema_location": "/_schemas/kafka/payments",
        "z_order_col": "payment_id",
        "comment": "Raw payments from landing zone.",
    },
}

EXPECTED_METADATA_COLUMNS = [
    "_source_file",
    "_ingestion_time",
    "_processed_time",
]

EXPECTED_AUTOLOADER_OPTIONS = {
    "cloudFiles.format": "json",
    "cloudFiles.inferColumnTypes": "true",
    "cloudFiles.schemaEvolutionMode": "addNewColumns",
}


@pytest.fixture
def bronze_specs() -> dict:
    """Bronze layer specifications from DATA_CATALOG."""
    return BRONZE_SPECS


@pytest.fixture
def expected_metadata_columns() -> list:
    """Expected lineage columns added in Bronze."""
    return EXPECTED_METADATA_COLUMNS


@pytest.fixture
def expected_autoloader_options() -> dict:
    """Expected Auto Loader configuration."""
    return EXPECTED_AUTOLOADER_OPTIONS
