import pytest

from parcel_lookup import core
from parcel_lookup.cli import main

HEADER = "parcel_id,address,owner,zoning,land_use,lot_sqft,assessed_value\n"


@pytest.fixture
def csv_file(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text(HEADER +
                 "A1,1 Oak St,Acme LLC,R-1,Single family,5000,500000\n"
                 "A2,2 Elm Ct,Demo Trust,C-1,Retail,43560,2178000\n"
                 "A3,3 Oak St,Demo Trust,R-1,Vacant,10000,100000\n")
    return f


def test_load(csv_file):
    assert len(core.load(csv_file)) == 3


def test_missing_column(tmp_path):
    f = tmp_path / "b.csv"
    f.write_text("parcel_id,address\nA,B\n")
    with pytest.raises(ValueError, match="missing columns"):
        core.load(f)


def test_bad_number(tmp_path):
    f = tmp_path / "b.csv"
    f.write_text(HEADER + "A,B,C,R-1,Vacant,abc,5\n")
    with pytest.raises(ValueError, match="line 2"):
        core.load(f)


def test_by_id_case_insensitive(csv_file):
    assert core.by_id(core.load(csv_file), "a2").address == "2 Elm Ct"


def test_by_id_missing(csv_file):
    assert core.by_id(core.load(csv_file), "zzz") is None


def test_search_text_owner_or_address(csv_file):
    ps = core.load(csv_file)
    assert len(core.search(ps, "oak")) == 2
    assert len(core.search(ps, "demo")) == 2


def test_search_zoning_and_size(csv_file):
    ps = core.load(csv_file)
    assert [p.parcel_id for p in core.search(ps, zoning="r-1", min_sqft=6000)] == ["A3"]


def test_value_per_sqft(csv_file):
    assert core.by_id(core.load(csv_file), "A1").value_per_sqft == 100


def test_summary(csv_file):
    s = core.summary(core.load(csv_file))
    assert s["C-1"]["acres"] == 1.0
    assert s["R-1"]["count"] == 2


def test_cli_missing_file(capsys):
    assert main(["--data", "nope.csv", "summary"]) == 2


def test_cli_unknown_id(csv_file, capsys):
    assert main(["--data", str(csv_file), "id", "zzz"]) == 1


def test_cli_search(csv_file, capsys):
    assert main(["--data", str(csv_file), "search", "oak"]) == 0
    assert "2 parcel(s)" in capsys.readouterr().out
