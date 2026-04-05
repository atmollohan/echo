"""Backend helpers shared by the CLI and Streamlit UI."""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_notebooks_dir() -> Path:
    """Return the configured notebook directory."""
    return Path(os.environ.get("ECHO_NOTEBOOKS_DIR", PROJECT_ROOT / "notebooks"))


def get_data_dir() -> Path:
    """Return the configured data directory."""
    return Path(os.environ.get("ECHO_DATA_DIR", PROJECT_ROOT / "data"))

DEFAULT_CONFIG = {
    "experiment_name": "my_experiment",
    "doses": 6,
    "doses2": 3,
    "highest_dose": 4.0,
    "vol_cellextract": 2000,
    "vol_antigen": 2000,
    "samples": "sample1,sample2,sample3",
}


@dataclass(frozen=True)
class SanityReport:
    """Summary of the repository state needed for backend smoke checks."""

    notebooks: list[str]
    data_files: list[str]
    config_values: dict[str, object]
    selected_notebook: str | None
    streamlit_available: bool


def get_notebooks(notebooks_dir: Path | None = None) -> list[str]:
    """Get the user-facing notebook list."""
    if notebooks_dir is None:
        notebooks_dir = get_notebooks_dir()
    if not notebooks_dir.exists():
        return []
    return sorted(
        file.name
        for file in notebooks_dir.glob("*.ipynb")
        if not file.name.endswith("-checkpoint.ipynb")
    )


def normalize_ini_text(raw_text: str) -> str:
    """Support both flat INI files and [experiment]-section INI files."""
    if raw_text.lstrip().startswith("["):
        return raw_text
    return "[experiment]\n" + raw_text


def load_config_text(config_text: str) -> configparser.ConfigParser:
    """Parse uploaded or file-based config text."""
    config = configparser.ConfigParser()
    config.read_string(normalize_ini_text(config_text))
    return config


def parse_config_text(config_text: str) -> tuple[dict[str, object], str | None]:
    """Return normalized config values and selected notebook."""
    config = load_config_text(config_text)
    values = DEFAULT_CONFIG.copy()

    config_items: dict[str, str] = {}
    if config.defaults():
        config_items.update(config.defaults())
    if config.has_section("experiment"):
        config_items.update(dict(config["experiment"].items()))

    for key in ("experiment_name", "samples"):
        if key in config_items:
            values[key] = config_items[key]

    for key in ("doses", "doses2", "vol_cellextract", "vol_antigen"):
        if key in config_items:
            values[key] = int(config_items[key])

    if "highest_dose" in config_items:
        values["highest_dose"] = float(config_items["highest_dose"])

    return values, config_items.get("notebook")


def parse_uploaded_config(uploaded_file: BinaryIO) -> tuple[dict[str, object], str | None]:
    """Return normalized config values from a Streamlit-uploaded file."""
    return parse_config_text(uploaded_file.getvalue().decode("utf-8"))


def list_data_files(data_dir: Path | None = None) -> list[str]:
    """List sample data files included with the repo."""
    if data_dir is None:
        data_dir = get_data_dir()
    if not data_dir.exists():
        return []
    return sorted(str(path.relative_to(PROJECT_ROOT)) for path in data_dir.rglob("*") if path.is_file())


def streamlit_is_available() -> bool:
    """Check whether the runtime dependency needed for the UI is importable."""
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def build_sanity_report(
    config_path: Path | None = None,
    notebooks_dir: Path | None = None,
    data_dir: Path | None = None,
) -> SanityReport:
    """Create a backend-only sanity report without importing Streamlit UI code."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config.example.ini"
    if notebooks_dir is None:
        notebooks_dir = get_notebooks_dir()
    if data_dir is None:
        data_dir = get_data_dir()

    config_values, selected_notebook = parse_config_text(config_path.read_text(encoding="utf-8"))
    return SanityReport(
        notebooks=get_notebooks(notebooks_dir),
        data_files=list_data_files(data_dir),
        config_values=config_values,
        selected_notebook=selected_notebook,
        streamlit_available=streamlit_is_available(),
    )
