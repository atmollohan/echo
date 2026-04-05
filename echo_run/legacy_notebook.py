"""Helpers for executing legacy notebook workflows without a live Jupyter kernel."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd


def install_pandas_legacy_compat() -> None:
    """Restore minimal pandas APIs relied on by the historical notebooks."""
    if hasattr(pd.DataFrame, "append"):
        return

    def _append(
        self: pd.DataFrame,
        other: Any,
        ignore_index: bool = False,
        verify_integrity: bool = False,
        sort: bool = False,
    ) -> pd.DataFrame:
        if isinstance(other, pd.Series):
            other = other.to_frame().T
        elif isinstance(other, dict):
            other = pd.DataFrame([other])
        elif not isinstance(other, pd.DataFrame):
            other = pd.DataFrame(other)

        return pd.concat(
            [self, other],
            ignore_index=ignore_index,
            verify_integrity=verify_integrity,
            sort=sort,
        )

    setattr(pd.DataFrame, "append", _append)


def iter_code_cells(notebook_path: Path) -> list[tuple[int, str]]:
    """Return executable code cells from a notebook JSON document."""
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells: list[tuple[int, str]] = []

    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code":
            continue
        code_cells.append((index, "".join(cell.get("source", []))))

    return code_cells


def execute_legacy_notebook(
    notebook_path: Path,
    *,
    working_dir: Path | None = None,
    extra_namespace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute notebook code cells sequentially in-process.

    The historical Echo notebooks are plain Python cells, so we can execute them
    directly and avoid depending on Jupyter kernel startup in constrained
    environments such as tests or sandboxed CI.
    """
    install_pandas_legacy_compat()

    namespace: dict[str, Any] = {"__name__": "__main__"}
    if extra_namespace:
        namespace.update(extra_namespace)

    original_cwd = Path.cwd()
    stdout = io.StringIO()

    try:
        if working_dir is not None:
            os.chdir(working_dir)

        with contextlib.redirect_stdout(stdout):
            for cell_index, source in iter_code_cells(notebook_path):
                exec(compile(source, f"{notebook_path.name}#cell{cell_index}", "exec"), namespace)
    finally:
        os.chdir(original_cwd)

    namespace["_captured_stdout"] = stdout.getvalue()
    return namespace
