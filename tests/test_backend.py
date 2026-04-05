"""Backend smoke tests for Echo Protocol."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from echo_run.backend import (
    DEFAULT_CONFIG,
    build_echo_protocol_summary,
    build_sanity_report,
    build_source_plate_summary,
    get_echo_protocol_paths,
    get_notebooks,
    get_source_plate_map_paths,
    load_echo_protocol,
    load_source_plate_map,
    normalize_ini_text,
    parse_plate_entry,
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
                "notebook = library_plate_b_protocol.ipynb",
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
        self.assertEqual(notebook, "library_plate_b_protocol.ipynb")

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


class SourcePlateMapTests(unittest.TestCase):
    def test_parse_plate_entry_extracts_substance_and_volume(self) -> None:
        self.assertEqual(parse_plate_entry("antigen: 55000nL"), ("antigen", 55000))
        self.assertEqual(parse_plate_entry(""), (None, None))

    def test_summary_counts_loaded_wells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "example_source_plate.csv"
            csv_path.write_text(
                ",1,2\nA,antigen: 55000nL,\nB,PBS: 12000nL,B2: 60000nL\n",
                encoding="utf-8",
            )

            plate_map = load_source_plate_map(csv_path)
            summary = build_source_plate_summary(plate_map)

            self.assertEqual(summary["occupied_wells"], 3)
            self.assertEqual(summary["empty_wells"], 1)
            self.assertEqual(summary["max_volume_nl"], 60000)
            self.assertEqual(summary["substances"], ["B2", "PBS", "antigen"])

    def test_get_source_plate_map_paths_finds_repo_examples(self) -> None:
        plate_paths = get_source_plate_map_paths()

        self.assertGreaterEqual(len(plate_paths), 1)
        self.assertTrue(any(path.name.endswith("source_plateA.csv") for path in plate_paths))


class EchoProtocolTests(unittest.TestCase):
    def test_get_echo_protocol_paths_finds_repo_examples(self) -> None:
        protocol_paths = get_echo_protocol_paths()

        self.assertGreaterEqual(len(protocol_paths), 1)
        self.assertTrue(any(path.name.endswith("echo_protocol_plateA.csv") for path in protocol_paths))

    def test_echo_protocol_summary_builds_destination_and_source_views(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "example_echo_protocol.csv"
            csv_path.write_text(
                (
                    "Unnamed: 0,Sample Name,Source Plate Name,Source Well,Destination Well,"
                    "Transfer Volume,Destination Plate Name,Source Plate Type\n"
                    "0,S1,src,A1,A1,100,dest,384PP_AQ_BP\n"
                    "1,S1,src,A1,A1,200,dest,384PP_AQ_BP\n"
                    "2,S2,src,B2,B3,150,dest,384PP_AQ_BP\n"
                ),
                encoding="utf-8",
            )

            protocol_df = load_echo_protocol(csv_path)
            summary = build_echo_protocol_summary(protocol_df)

            self.assertEqual(summary["transfer_count"], 3)
            self.assertEqual(summary["sample_count"], 2)
            self.assertEqual(summary["source_well_count"], 2)
            self.assertEqual(summary["destination_well_count"], 2)
            self.assertEqual(summary["total_transfer_volume_nl"], 450)
            self.assertIn("S1@A1: 300 nL", summary["destination_composition_grid"].loc["A", 1])
            self.assertEqual(int(summary["destination_component_count_grid"].loc["A", 1]), 1)
            self.assertEqual(int(summary["destination_count_grid"].loc["A", 1]), 2)
            self.assertEqual(int(summary["source_count_grid"].loc["A", 1]), 2)


if __name__ == "__main__":
    unittest.main()
