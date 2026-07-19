"""Regression test suite for utils/property_normalizer.py
All 11 mandatory fixtures must pass.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils.property_normalizer import (
    parse_raw_property_dump,
    normalize_property,
    parsed_to_normalized,
    build_meta_title,
    build_meta_description,
    build_whatsapp_caption,
    build_whatsapp_title,
)
from tests.fixtures.property_examples import FIXTURES


class TestParseRawPropertyDump:
    """Test label-based parsing of raw text dumps."""

    def _parse(self, raw: str):
        p = parse_raw_property_dump(raw)
        n = parsed_to_normalized(p)
        return p, n

    @pytest.mark.parametrize("fixture", FIXTURES, ids=[f["name"] for f in FIXTURES])
    def test_canonical_fields(self, fixture):
        p, n = self._parse(fixture["raw"])
        exp = fixture["expected"]

        if "furnishing" in exp:
            assert n.furnishing == exp["furnishing"], (
                f"{fixture['name']}: furnishing mismatch: got {n.furnishing!r}"
            )
        if "bhk" in exp:
            assert n.bhk == exp["bhk"], (
                f"{fixture['name']}: bhk mismatch: got {n.bhk!r}"
            )
        if "bathrooms" in exp:
            assert n.bathrooms == exp["bathrooms"], (
                f"{fixture['name']}: bathrooms mismatch: got {n.bathrooms!r}"
            )
        if "bathroom_type" in exp:
            assert n.bathroom_type == exp["bathroom_type"], (
                f"{fixture['name']}: bathroom_type mismatch: got {n.bathroom_type!r}"
            )
        if "balconies" in exp:
            assert n.balconies == exp["balconies"], (
                f"{fixture['name']}: balconies mismatch: got {n.balconies!r}"
            )
        if "has_utility" in exp:
            assert n.has_utility == exp["has_utility"], (
                f"{fixture['name']}: has_utility mismatch: got {n.has_utility!r}"
            )
        if "rent" in exp:
            assert n.rent == exp["rent"], (
                f"{fixture['name']}: rent mismatch: got {n.rent!r}"
            )
        if "maintenance" in exp:
            assert n.maintenance == exp["maintenance"], (
                f"{fixture['name']}: maintenance mismatch: got {n.maintenance!r}"
            )
        if "deposit" in exp:
            # case-insensitive for L/l suffix
            assert n.deposit.lower() == exp["deposit"].lower(), (
                f"{fixture['name']}: deposit mismatch: got {n.deposit!r}"
            )
        if "area_sqft" in exp:
            assert n.area_sqft == exp["area_sqft"], (
                f"{fixture['name']}: area_sqft mismatch: got {n.area_sqft!r}"
            )
        if "floor" in exp:
            assert n.floor == exp["floor"], (
                f"{fixture['name']}: floor mismatch: got {n.floor!r}"
            )
        if "available_from" in exp:
            assert n.available_from == exp["available_from"], (
                f"{fixture['name']}: available_from mismatch: got {n.available_from!r}"
            )
        if "property_name" in exp:
            assert n.property_name == exp["property_name"], (
                f"{fixture['name']}: property_name mismatch: got {n.property_name!r}"
            )
        if "location" in exp:
            assert n.location == exp["location"], (
                f"{fixture['name']}: location mismatch: got {n.location!r}"
            )

    @pytest.mark.parametrize("fixture", FIXTURES, ids=[f["name"] for f in FIXTURES])
    def test_meta_title(self, fixture):
        p, n = self._parse(fixture["raw"])
        title = build_meta_title(n)
        assert title == fixture["meta_title"], (
            f"{fixture['name']}: meta_title mismatch:\n  got: {title!r}\n  expected: {fixture['meta_title']!r}"
        )

    @pytest.mark.parametrize("fixture", FIXTURES, ids=[f["name"] for f in FIXTURES])
    def test_whatsapp_heading(self, fixture):
        p, n = self._parse(fixture["raw"])
        heading = build_whatsapp_title(n)
        assert heading == fixture["whatsapp_heading"], (
            f"{fixture['name']}: whatsapp_heading mismatch:\n  got: {heading!r}\n  expected: {fixture['whatsapp_heading']!r}"
        )


class TestAreaFloorNeverSwapped:
    """Sqft must never be assigned to floor and floor must never be assigned to area_sqft."""

    def test_candeur_area_is_1110_not_floor(self):
        raw = FIXTURES[7]["raw"]  # Candeur Landmark
        p = parse_raw_property_dump(raw)
        assert p.area_sqft == "1110", f"area_sqft should be 1110, got {p.area_sqft!r}"
        assert p.floor == "6/14", f"floor should be 6/14, got {p.floor!r}"

    def test_deposit_not_converted_2L(self):
        """Deposit 2L must stay as 2L, not become 2 or 200000."""
        raw = FIXTURES[7]["raw"]
        p = parse_raw_property_dump(raw)
        assert p.deposit.lower() == "2l", f"deposit should be 2L, got {p.deposit!r}"


class TestMaintenancePreservation:
    """Inclusive and Water charges must be preserved verbatim."""

    def test_inclusive_maintenance(self):
        p = parse_raw_property_dump(FIXTURES[1]["raw"])  # Orchid Lakeview
        assert p.maintenance == "Inclusive"

    def test_water_charges_maintenance(self):
        p = parse_raw_property_dump(FIXTURES[5]["raw"])  # Prima Hilife
        assert p.maintenance == "Water charges"


class TestLocationBlankForPrimaHilife:
    def test_no_location(self):
        p = parse_raw_property_dump(FIXTURES[5]["raw"])  # Prima Hilife
        assert p.location == ""

    def test_meta_title_no_location(self):
        p = parse_raw_property_dump(FIXTURES[5]["raw"])
        n = parsed_to_normalized(p)
        title = build_meta_title(n)
        assert title == "Fully Furnished | 3BHK"


class TestImmediatelyNormalized:
    def test_immediately_becomes_ready_to_occupy(self):
        p = parse_raw_property_dump(FIXTURES[6]["raw"])  # Trifecta Joli
        assert p.available_from == "Ready to occupy"
