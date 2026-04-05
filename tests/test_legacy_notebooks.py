"""Regression tests for the historical library plate notebooks."""

from __future__ import annotations

from dataclasses import dataclass
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from echo_run.backend import PROJECT_ROOT, load_echo_protocol, load_source_plate_map
from echo_run.legacy_notebook import execute_legacy_notebook


@dataclass(frozen=True)
class ReferenceWorkflowCase:
    """Historical notebook workflow captured as a regression reference case."""

    case_id: str
    notebook_name: str
    fixture_dir: str
    source_plate_fixture: str
    protocol_fixture: str


REFERENCE_WORKFLOW_CASES = {
    "library_plate_a": ReferenceWorkflowCase(
        case_id="library_plate_a",
        notebook_name="library_plate_a_protocol.ipynb",
        fixture_dir="library_plate_a",
        source_plate_fixture="20240813_ML_L1_source_plateA.csv",
        protocol_fixture="20240813_ML_L1_echo_protocol_plateA.csv",
    ),
    "library_plate_b": ReferenceWorkflowCase(
        case_id="library_plate_b",
        notebook_name="library_plate_b_protocol.ipynb",
        fixture_dir="library_plate_b",
        source_plate_fixture="20240813_ML_L1_source_plateB.csv",
        protocol_fixture="20240813_ML_L1_echo_protocol_plateB.csv",
    ),
}


class LegacyNotebookRegressionTests(unittest.TestCase):
    maxDiff = None

    def assert_reference_workflow_case_matches_outputs(self, case: ReferenceWorkflowCase) -> None:
        notebook_path = PROJECT_ROOT / "notebooks" / case.notebook_name
        fixture_dir = PROJECT_ROOT / "data" / "raw" / case.fixture_dir
        source_fixture_path = fixture_dir / case.source_plate_fixture
        protocol_fixture_path = fixture_dir / case.protocol_fixture

        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = execute_legacy_notebook(notebook_path, working_dir=Path(temp_dir))

            generated_source_plate = runtime["source_plate_df"].fillna("").astype(str)
            generated_source_plate.columns = [str(column) for column in generated_source_plate.columns]
            generated_protocol = runtime["echo_protocol"].reset_index(drop=True)

            expected_source_plate = load_source_plate_map(source_fixture_path).fillna("").astype(str)
            expected_source_plate.columns = [str(column) for column in expected_source_plate.columns]
            expected_protocol = load_echo_protocol(protocol_fixture_path).reset_index(drop=True)

            pd.testing.assert_frame_equal(generated_source_plate, expected_source_plate, check_dtype=False)
            pd.testing.assert_frame_equal(generated_protocol, expected_protocol, check_dtype=False)

            generated_protocol_path = Path(temp_dir) / case.protocol_fixture
            self.assertTrue(generated_protocol_path.exists(), f"{case.protocol_fixture} was not written by the notebook")

            generated_protocol_csv = load_echo_protocol(generated_protocol_path).reset_index(drop=True)
            pd.testing.assert_frame_equal(generated_protocol_csv, expected_protocol, check_dtype=False)

    def test_library_plate_a_notebook_matches_committed_outputs(self) -> None:
        self.assert_reference_workflow_case_matches_outputs(REFERENCE_WORKFLOW_CASES["library_plate_a"])

    def test_library_plate_b_notebook_matches_committed_outputs(self) -> None:
        self.assert_reference_workflow_case_matches_outputs(REFERENCE_WORKFLOW_CASES["library_plate_b"])


if __name__ == "__main__":
    unittest.main()
