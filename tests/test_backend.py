"""Backend smoke tests for Echo Lab Protocol Generator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from echo_run.backend import (
    DEFAULT_CONFIG,
    build_sanity_report,
    get_notebooks,
    normalize_ini_text,
    parse_config_text,
)


class ConfigParsingTests(unittest.TestCase):
    def test_flat_ini_is_wrapped_with_experiment_section(self) -> None:
        self.assertTrue(normalize_ini_text("doses = 6\n").startswith("[experiment]\n"))

    def test_parse_flat_config_uses_expected_types(self) -> None:
        config_text = "\n".join(
            [
                "experiment_name = assay_1",
                "doses = 8",
                "doses2 = 2",
                "highest_dose = 9.5",
                "vol_cellextract = 1500",
                "vol_antigen = 1200",
                "samples = a,b,c",
                "notebook = library-PLATE-B.ipynb",
            ]
        )

        values, notebook = parse_config_text(config_text)

        self.assertEqual(values["experiment_name"], "assay_1")
        self.assertEqual(values["doses"], 8)
        self.assertEqual(values["doses2"], 2)
        self.assertEqual(values["highest_dose"], 9.5)
        self.assertEqual(values["vol_cellextract"], 1500)
        self.assertEqual(values["vol_antigen"], 1200)
        self.assertEqual(values["samples"], "a,b,c")
        self.assertEqual(notebook, "library-PLATE-B.ipynb")

    def test_parse_sectioned_config_overrides_defaults(self) -> None:
        values, notebook = parse_config_text("[experiment]\ndoses = 10\n")
        self.assertEqual(values["doses"], 10)
        self.assertEqual(notebook, None)

    def test_defaults_are_preserved_when_fields_missing(self) -> None:
        values, _ = parse_config_text("[experiment]\nexperiment_name = quick_check\n")
        self.assertEqual(values["experiment_name"], "quick_check")
        self.assertEqual(values["samples"], DEFAULT_CONFIG["samples"])


class RepoSanityTests(unittest.TestCase):
    def test_get_notebooks_filters_checkpoint_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "keep.ipynb").write_text("", encoding="utf-8")
            (root / "also-keep-notebook.ipynb").write_text("", encoding="utf-8")
            (root / "skip-checkpoint-checkpoint.ipynb").write_text("", encoding="utf-8")

            self.assertEqual(get_notebooks(root), ["also-keep-notebook.ipynb", "keep.ipynb"])

    def test_build_sanity_report_matches_repo_shape(self) -> None:
        report = build_sanity_report()

        self.assertGreaterEqual(len(report.notebooks), 1)
        self.assertIn("library_plate_a_protocol.ipynb", report.notebooks)
        self.assertGreaterEqual(len(report.data_files), 1)
        self.assertEqual(report.selected_notebook, "library_plate_a_protocol.ipynb")
        self.assertEqual(report.config_values["doses"], 6)


if __name__ == "__main__":
    unittest.main()
