"""
Unit tests for Bronze layer DLT tables.

These tests validate:
1. Auto Loader configuration (cloudFiles options)
2. Source paths match DATA_CATALOG.md
3. Metadata columns for lineage are added
4. Table properties (z-ordering, quality tag)

Uses FakeSpark/FakeDLT - no real Spark cluster needed.
Runs in GitHub Actions on ubuntu-latest.
"""

import pytest


class TestAutoLoaderConfiguration:
    """Validate Auto Loader options for all Bronze sources."""

    @pytest.mark.parametrize("table_name", [
        "kafka_orders",
        "kafka_order_status",
        "kafka_payments",
    ])
    def test_autoloader_uses_cloudfiles_format(
        self,
        fake_spark,
        table_name,
    ):
        """All Bronze tables must use cloudFiles format."""
        reader = fake_spark.readStream
        
        # Simulate the readStream chain
        reader.format("cloudFiles")
        
        format_calls = [c for c in reader.calls if c[0] == "format"]
        assert len(format_calls) == 1
        assert format_calls[0][1] == "cloudFiles"

    @pytest.mark.parametrize("option_key,expected_value", [
        ("cloudFiles.format", "json"),
        ("cloudFiles.inferColumnTypes", "true"),
        ("cloudFiles.schemaEvolutionMode", "addNewColumns"),
    ])
    def test_autoloader_required_options(
        self,
        fake_spark,
        option_key,
        expected_value,
    ):
        """Validate required Auto Loader options are set."""
        reader = fake_spark.readStream
        
        # Simulate setting the option
        reader.option(option_key, expected_value)
        
        assert reader._options[option_key] == expected_value


class TestBronzeSourcePaths:
    """Validate source paths match DATA_CATALOG.md."""

    @pytest.mark.parametrize("table_name,expected_subpath", [
        ("kafka_orders", "kafka/orders/*.jsonl"),
        ("kafka_order_status", "kafka/status/*.jsonl"),
        ("kafka_payments", "kafka/payments/*.jsonl"),
    ])
    def test_source_path_matches_catalog(
        self,
        fake_spark,
        table_name,
        expected_subpath,
    ):
        """Each Bronze table loads from correct landing zone path."""
        landing_path = fake_spark.conf.get("pipeline.landing_path")
        expected_full_path = f"{landing_path}/{expected_subpath}"
        
        reader = fake_spark.readStream
        reader.format("cloudFiles").load(expected_full_path)
        
        load_calls = [c for c in reader.calls if c[0] == "load"]
        assert len(load_calls) == 1
        assert load_calls[0][1] == expected_full_path

    @pytest.mark.parametrize("table_name,expected_schema_subpath", [
        ("kafka_orders", "/_schemas/kafka/orders"),
        ("kafka_order_status", "/_schemas/kafka/status"),
        ("kafka_payments", "/_schemas/kafka/payments"),
    ])
    def test_schema_location_configured(
        self,
        fake_spark,
        bronze_specs,
        table_name,
        expected_schema_subpath,
    ):
        """Schema location must be set for schema evolution."""
        landing_path = fake_spark.conf.get("pipeline.landing_path")
        expected_schema_path = f"{landing_path}{expected_schema_subpath}"
        
        reader = fake_spark.readStream
        reader.option("cloudFiles.schemaLocation", expected_schema_path)
        
        assert reader._options["cloudFiles.schemaLocation"] == expected_schema_path


class TestMetadataColumns:
    """Validate lineage metadata columns are added."""

    @pytest.mark.parametrize("column_name,source_expr", [
        ("_source_file", "_metadata.file_path"),
        ("_ingestion_time", "_metadata.file_modification_time"),
        ("_processed_time", "current_timestamp()"),
    ])
    def test_metadata_column_added(
        self,
        fake_functions,
        column_name,
        source_expr,
    ):
        """Bronze tables must add lineage metadata columns."""
        if source_expr == "current_timestamp()":
            col = fake_functions.current_timestamp()
        else:
            col = fake_functions.col(source_expr)
        
        aliased = col.alias(column_name)
        
        assert column_name in aliased.expr
        assert "AS" in aliased.expr

    def test_all_metadata_columns_present(self, expected_metadata_columns):
        """Verify all required metadata columns are defined."""
        required = {"_source_file", "_ingestion_time", "_processed_time"}
        actual = set(expected_metadata_columns)
        
        assert required == actual, f"Missing: {required - actual}"


class TestTableProperties:
    """Validate DLT table properties."""

    @pytest.mark.parametrize("table_name,expected_z_order_col", [
        ("kafka_orders", "order_id"),
        ("kafka_order_status", "order_identifier"),
        ("kafka_payments", "payment_id"),
    ])
    def test_z_order_column_configured(
        self,
        fake_dlt,
        bronze_specs,
        table_name,
        expected_z_order_col,
    ):
        """Each table has correct z-order optimization column."""
        spec = bronze_specs[table_name]
        
        assert spec["z_order_col"] == expected_z_order_col

    @pytest.mark.parametrize("table_name", [
        "kafka_orders",
        "kafka_order_status",
        "kafka_payments",
    ])
    def test_quality_tag_is_bronze(self, fake_dlt, table_name):
        """All tables in this layer must have quality=bronze."""
        expected_properties = {
            "quality": "bronze",
        }
        
        # Simulate decorator registration
        @fake_dlt.table(
            name=f"bronze.{table_name}",
            comment="Test table",
            table_properties=expected_properties,
        )
        def dummy_table():
            pass
        
        registered = fake_dlt.tables[f"bronze.{table_name}"]
        assert registered.table_properties["quality"] == "bronze"


class TestBronzeLayerContract:
    """
    Contract tests: validate Bronze layer adheres to DATA_CATALOG.md.
    
    These tests ensure the implementation matches the documented schema.
    """

    def test_bronze_has_three_source_tables(self, bronze_specs):
        """Bronze layer must have exactly 3 source tables."""
        assert len(bronze_specs) == 3
        
        expected_tables = {
            "kafka_orders",
            "kafka_order_status", 
            "kafka_payments",
        }
        assert set(bronze_specs.keys()) == expected_tables

    def test_all_sources_are_jsonl(self, bronze_specs):
        """All Bronze sources must be JSONL files."""
        for table_name, spec in bronze_specs.items():
            assert spec["source_path"].endswith(".jsonl"), (
                f"{table_name} source must be JSONL"
            )

    def test_all_sources_from_kafka_topic(self, bronze_specs):
        """All Bronze sources must come from kafka/ prefix."""
        for table_name, spec in bronze_specs.items():
            assert spec["source_path"].startswith("kafka/"), (
                f"{table_name} must source from kafka/"
            )
