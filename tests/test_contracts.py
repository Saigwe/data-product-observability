"""Every raw file meets its source contract: columns, types, grain and allowed values per schema version."""
from pathlib import Path

import duckdb
import pyarrow.parquet as pq
import pytest
import yaml

from conftest import RAW, ROOT

CONTRACTS = yaml.safe_load((ROOT / "contracts" / "sources.yml").read_text(encoding="utf-8"))
TYPES = {"string": ("string", "large_string", "null"), "date": ("date32[day]", "timestamp[ns]", "timestamp[us]"),
         "timestamp": ("timestamp[ns]", "timestamp[us]", "null"), "int": ("int64", "int32"), "float": ("double", "float")}


@pytest.mark.parametrize("table", sorted(CONTRACTS))
def test_contract(table):
    f = RAW / f"{table}.parquet"
    if not f.exists():
        pytest.skip("run `make data` first")
    spec = CONTRACTS[table]
    schema = pq.read_schema(f)
    assert list(schema.names) == list(spec["columns"]), f"{table}: columns differ from the contract"
    for col, t in spec["columns"].items():
        assert str(schema.field(col).type) in TYPES[t], f"{table}.{col}: {schema.field(col).type} is not {t}"
    p = Path(f).as_posix()
    grain = ", ".join(spec["grain"])
    assert duckdb.sql(f"select count(*) from (select {grain} from '{p}' group by all having count(*) > 1)").fetchone()[0] == 0
    for col, by_version in spec.get("allowed", {}).items():
        for v, values in by_version.items():
            bad = duckdb.sql(f"select count(*) from '{p}' where schema_version = {v} and {col} not in ({', '.join(repr(x) for x in values)})").fetchone()[0]
            assert bad == 0, f"{table}.{col} has values outside schema v{v}"
