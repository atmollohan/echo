"""Tests for the protocol validation layer."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from echo_run.validation import (
    Severity,
    ValidationResult,
    validate_protocol,
    validate_source_plate,
    validate_protocol_columns,
    validate_source_wells,
    validate_destination_wells,
    validate_transfer_volumes,
    validate_destination_duplicates,
    validate_conflicting_transfers,
)


def _make_result() -> ValidationResult:
    return ValidationResult(issues=[], valid=True)


class ColumnValidationTests(unittest.TestCase):
    def test_valid_protocol_passes_column_validation(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Sample Name": ["S1"],
                "Source Plate Name": ["src"],
                "Source Well": ["A1"],
                "Destination Well": ["A1"],
                "Transfer Volume": [100],
                "Destination Plate Name": ["dest"],
                "Source Plate Type": ["384PP_AQ_BP"],
            }
        )

        result = _make_result()
        validate_protocol_columns(protocol_df, result)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors()), 0)

    def test_missing_columns_fails_with_errors(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Sample Name": ["S1"],
                "Destination Well": ["A1"],
            }
        )

        result = _make_result()
        validate_protocol_columns(protocol_df, result)
        self.assertFalse(result.valid)
        self.assertGreater(len(result.errors()), 0)


class SourceWellValidationTests(unittest.TestCase):
    def test_valid_384_well_format_passes(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Source Well": ["A1", "P24", "C12"],
            }
        )

        result = _make_result()
        validate_source_wells(protocol_df, result)
        self.assertTrue(result.valid)

    def test_invalid_well_format_fails(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Source Well": ["AA1", "Q1", "A25", ""],
            }
        )

        result = _make_result()
        validate_source_wells(protocol_df, result)
        self.assertFalse(result.valid)
        errors = result.errors()
        self.assertGreaterEqual(len(errors), 3)


class DestinationWellValidationTests(unittest.TestCase):
    def test_valid_96_well_format_passes(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Destination Well": ["A1", "H12", "B6"],
            }
        )

        result = _make_result()
        validate_destination_wells(protocol_df, result, max_wells=96)
        self.assertTrue(result.valid)

    def test_96_well_strictness_for_384_well_input_fails(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Destination Well": ["A1", "P24"],
            }
        )

        result = _make_result()
        validate_destination_wells(protocol_df, result, max_wells=96)
        self.assertFalse(result.valid)

    def test_valid_384_well_format_passes(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Destination Well": ["A1", "P24", "M17"],
            }
        )

        result = _make_result()
        validate_destination_wells(protocol_df, result, max_wells=384)
        self.assertTrue(result.valid)


class TransferVolumeValidationTests(unittest.TestCase):
    def test_valid_volume_passes(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Transfer Volume": [100, 5000, 25000],
            }
        )

        result = _make_result()
        validate_transfer_volumes(protocol_df, result)
        self.assertTrue(result.valid)

    def test_volume_below_minimum_warns(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Transfer Volume": [10],
            }
        )

        result = _make_result()
        validate_transfer_volumes(protocol_df, result)
        self.assertTrue(result.valid)
        warnings = result.warnings()
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].severity, Severity.WARNING)

    def test_volume_above_maximum_errors(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Transfer Volume": [600000],
            }
        )

        result = _make_result()
        validate_transfer_volumes(protocol_df, result)
        self.assertFalse(result.valid)

    def test_non_numeric_volume_errors(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Transfer Volume": ["abc"],
            }
        )

        result = _make_result()
        validate_transfer_volumes(protocol_df, result)
        self.assertFalse(result.valid)


class DuplicateDetectionTests(unittest.TestCase):
    def test_no_duplicates_passes(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Destination Well": ["A1", "A2"],
                "Source Well": ["A1", "A1"],
            }
        )

        result = _make_result()
        validate_destination_duplicates(protocol_df, result)
        self.assertTrue(result.valid)

    def test_duplicate_source_to_same_dest_warns(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Destination Well": ["A1", "A1"],
                "Source Well": ["A1", "A1"],
            }
        )

        result = _make_result()
        validate_destination_duplicates(protocol_df, result)
        self.assertTrue(result.valid)
        warnings = result.warnings()
        self.assertGreater(len(warnings), 0)


class ConflictDetectionTests(unittest.TestCase):
    def test_single_sample_passes(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Destination Well": ["A1", "A1"],
                "Sample Name": ["S1", "S1"],
            }
        )

        result = _make_result()
        validate_conflicting_transfers(protocol_df, result)
        self.assertTrue(result.valid)

    def test_multiple_samples_to_same_dest_fails(self) -> None:
        protocol_df = pd.DataFrame(
            {
                "Destination Well": ["A1", "A1"],
                "Sample Name": ["S1", "S2"],
            }
        )

        result = _make_result()
        validate_conflicting_transfers(protocol_df, result)
        self.assertFalse(result.valid)
        errors = result.errors()
        self.assertGreater(len(errors), 0)


class FullProtocolValidationTests(unittest.TestCase):
    def test_valid_echo_protocol_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "valid_protocol.csv"
            csv_path.write_text(
                (
                    "Sample Name,Source Plate Name,Source Well,Destination Well,"
                    "Transfer Volume,Destination Plate Name,Source Plate Type\n"
                    "S1,src,A1,A1,100,dest,384PP_AQ_BP\n"
                    "S1,src,B1,A1,200,dest,384PP_AQ_BP\n"
                    "S1,src,A1,B1,100,dest,384PP_AQ_BP\n"
                ),
                encoding="utf-8",
            )

            result = validate_protocol(csv_path)

            self.assertTrue(result.valid, f"Errors: {result.errors()}")
            self.assertEqual(result.summary()["errors"], 0)

    def test_missing_source_column_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "invalid_protocol.csv"
            csv_path.write_text(
                ("Sample Name,Destination Well,Transfer Volume\nS1,A1,100\n"),
                encoding="utf-8",
            )

            result = validate_protocol(csv_path)

            self.assertFalse(result.valid)
            self.assertGreater(result.summary()["errors"], 0)

    def test_validation_summary_counts_issues(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "summary_test.csv"
            csv_path.write_text(
                (
                    "Sample Name,Source Plate Name,Source Well,Destination Well,"
                    "Transfer Volume,Destination Plate Name,Source Plate Type\n"
                    "S1,src,A1,A1,100,dest,384PP_AQ_BP\n"
                    "S2,src,A1,A1,100,dest,384PP_AQ_BP\n"
                ),
                encoding="utf-8",
            )

            result = validate_protocol(csv_path)

            summary = result.summary()
            self.assertFalse(summary["valid"])
            self.assertTrue(summary["errors"] > 0)


class SourcePlateValidationTests(unittest.TestCase):
    def test_valid_source_plate_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "valid_source.csv"
            csv_path.write_text(
                ",1,2\nA,antigen: 55000nL,\nB,PBS: 12000nL,\n",
                encoding="utf-8",
            )

            result = validate_source_plate(csv_path)

            self.assertTrue(result.valid)
            self.assertEqual(len(result.errors()), 0)

    def test_volume_exceeding_capacity_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "overfilled_source.csv"
            csv_path.write_text(
                ",1\nA,m reagent: 70000nL\n",
                encoding="utf-8",
            )

            result = validate_source_plate(csv_path)

            self.assertTrue(result.valid, "Volume warnings should not invalidate")
            warnings = result.warnings()
            self.assertGreater(len(warnings), 0)


if __name__ == "__main__":
    unittest.main()
