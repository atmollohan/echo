"""Tests for the generic preprocessing workflow runner."""

from __future__ import annotations

from dataclasses import dataclass
import tempfile
import unittest
from pathlib import Path

from echo_run.preprocessing import (
    PLATE_MODE_MANUAL,
    PLATE_MODE_NEW,
    PLATE_MODE_PREMADE,
    PreprocessingRequest,
    run_echo_protocol_preprocessing,
)


@dataclass(frozen=True)
class PremadePlateCase:
    """Reference premade-plate scenario that should stay stable over time."""

    case_id: str
    experiment_name: str
    premade_plate_name: str


PREMADE_PLATE_CASES = {
    "library_plate_a": PremadePlateCase(
        case_id="library_plate_a",
        experiment_name="plate_a_validation",
        premade_plate_name="20240813_ML_L1_source_plateA.csv",
    ),
    "library_plate_b": PremadePlateCase(
        case_id="library_plate_b",
        experiment_name="plate_b_validation",
        premade_plate_name="20240813_ML_L1_source_plateB.csv",
    ),
}


class PreprocessingRunnerTests(unittest.TestCase):
    def assert_premade_plate_case_uses_notebook_workflow(
        self, case: PremadePlateCase
    ) -> None:
        request = PreprocessingRequest(
            experiment_name=case.experiment_name,
            plate_mode=PLATE_MODE_PREMADE,
            premade_plate_name=case.premade_plate_name,
            new_plate_label=None,
            doses=6,
            doses2=3,
            highest_dose=4.0,
            vol_cellextract=2000,
            vol_antigen=2000,
            samples=["sample1", "sample2"],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_echo_protocol_preprocessing(request, output_dir=Path(temp_dir))

            self.assertTrue(result.execution_mode.startswith("notebook"))
            self.assertTrue(result.protocol_csv and result.protocol_csv.exists())
            self.assertTrue(
                result.source_plate_csv and result.source_plate_csv.exists()
            )
            self.assertTrue(
                result.destination_composition_csv
                and result.destination_composition_csv.exists()
            )
            self.assertTrue(result.notebook_output_path.exists())

    def test_library_plate_a_runs_via_notebook(self) -> None:
        self.assert_premade_plate_case_uses_notebook_workflow(
            PREMADE_PLATE_CASES["library_plate_a"]
        )

    def test_library_plate_b_runs_via_notebook(self) -> None:
        self.assert_premade_plate_case_uses_notebook_workflow(
            PREMADE_PLATE_CASES["library_plate_b"]
        )

    def test_new_plate_from_scratch_runs_via_notebook(self) -> None:
        request = PreprocessingRequest(
            experiment_name="new_plate_validation",
            plate_mode=PLATE_MODE_NEW,
            premade_plate_name=None,
            new_plate_label="new_plate",
            doses=3,
            doses2=0,
            highest_dose=4.0,
            vol_cellextract=2000,
            vol_antigen=2000,
            samples=["sample1", "sample2"],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_echo_protocol_preprocessing(request, output_dir=Path(temp_dir))

            self.assertTrue(result.execution_mode.startswith("notebook"))
            self.assertTrue(result.protocol_csv and result.protocol_csv.exists())
            self.assertTrue(
                result.source_plate_csv and result.source_plate_csv.exists()
            )
            self.assertTrue(
                result.destination_composition_csv
                and result.destination_composition_csv.exists()
            )
            self.assertTrue(result.notebook_output_path.exists())

    def test_manual_plate_runs_via_python_workflow(self) -> None:
        request = PreprocessingRequest(
            experiment_name="manual_plate_validation",
            plate_mode=PLATE_MODE_MANUAL,
            premade_plate_name=None,
            new_plate_label=None,
            doses=2,
            doses2=0,
            highest_dose=4.0,
            vol_cellextract=2000,
            vol_antigen=500,
            samples=["sample1", "sample2"],
            manual_source_plate={
                "A1": ("sample1", 60000),
                "A2": ("sample2", 60000),
                "B1": ("antigen", 65000),
                "B2": ("PBS", 65000),
            },
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_echo_protocol_preprocessing(request, output_dir=Path(temp_dir))

            self.assertEqual(result.execution_mode, "manual_plate")
            self.assertTrue(result.protocol_csv and result.protocol_csv.exists())
            self.assertTrue(
                result.source_plate_csv and result.source_plate_csv.exists()
            )
            self.assertTrue(
                result.destination_composition_csv
                and result.destination_composition_csv.exists()
            )
            self.assertIsNone(result.notebook_output_path)

    def test_premade_plate_can_run_as_customized_editable_plate(self) -> None:
        request = PreprocessingRequest(
            experiment_name="premade_customized_validation",
            plate_mode=PLATE_MODE_PREMADE,
            premade_plate_name="20240813_ML_L1_source_plateA.csv",
            new_plate_label=None,
            doses=2,
            doses2=0,
            highest_dose=4.0,
            vol_cellextract=2000,
            vol_antigen=500,
            samples=["sample1", "sample2"],
            manual_source_plate={
                "A1": ("sample1", 60000),
                "A2": ("sample2", 60000),
                "B1": ("antigen", 65000),
                "B2": ("PBS", 65000),
            },
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_echo_protocol_preprocessing(request, output_dir=Path(temp_dir))

            self.assertEqual(result.execution_mode, "premade_customized")
            self.assertTrue(result.protocol_csv and result.protocol_csv.exists())
            self.assertTrue(
                result.source_plate_csv and result.source_plate_csv.exists()
            )
            self.assertTrue(
                result.destination_composition_csv
                and result.destination_composition_csv.exists()
            )
            self.assertIsNone(result.notebook_output_path)


if __name__ == "__main__":
    unittest.main()
