"""Tests for the generic preprocessing workflow runner."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from echo_run.preprocessing import (
    PLATE_MODE_NEW,
    PLATE_MODE_PREMADE,
    PreprocessingRequest,
    run_echo_protocol_preprocessing,
)


class PreprocessingRunnerTests(unittest.TestCase):
    def test_premade_plate_materializes_fixture_outputs(self) -> None:
        request = PreprocessingRequest(
            experiment_name="plate_a_validation",
            plate_mode=PLATE_MODE_PREMADE,
            premade_plate_name="20240813_ML_L1_source_plateA.csv",
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

            self.assertEqual(result.execution_mode, "fixture_replay")
            self.assertTrue(result.protocol_csv and result.protocol_csv.exists())
            self.assertTrue(result.source_plate_csv and result.source_plate_csv.exists())
            self.assertTrue(result.destination_composition_csv and result.destination_composition_csv.exists())
            self.assertTrue(result.run_manifest_json.exists())

            composition_df = pd.read_csv(result.destination_composition_csv)
            self.assertIn("Destination Well", composition_df.columns)
            self.assertIn("Composition", composition_df.columns)
            self.assertTrue(composition_df["Composition"].str.contains("antigen").any())

    def test_new_plate_requires_custom_workflow_implementation(self) -> None:
        request = PreprocessingRequest(
            experiment_name="new_plate_validation",
            plate_mode=PLATE_MODE_NEW,
            premade_plate_name=None,
            new_plate_label="new_plate",
            doses=6,
            doses2=3,
            highest_dose=4.0,
            vol_cellextract=2000,
            vol_antigen=2000,
            samples=["sample1", "sample2"],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(NotImplementedError):
                run_echo_protocol_preprocessing(request, output_dir=Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
