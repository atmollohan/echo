"""Protocol validation for Echo liquid handler outputs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pandas as pd


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation finding."""

    severity: Severity
    rule: str
    message: str
    row: int | None = None
    column: str | None = None
    well: str | None = None


@dataclass
class ValidationResult:
    """Aggregated validation results."""

    issues: list[ValidationIssue]
    valid: bool

    def add_issue(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)
        if issue.severity == Severity.ERROR:
            self.valid = False

    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def summary(self) -> dict:
        return {
            "valid": self.valid,
            "total_issues": len(self.issues),
            "errors": len(self.errors()),
            "warnings": len(self.warnings()),
        }


REQUIRED_COLUMNS = {
    "Sample Name",
    "Source Plate Name",
    "Source Well",
    "Destination Well",
    "Transfer Volume",
    "Destination Plate Name",
    "Source Plate Type",
}

WELL_PATTERN_ROW = r"^[A-Z]$"
WELL_PATTERN_384 = r"^[A-P]([12]?[0-9]|[1-2][0-9])$"
WELL_PATTERN_96 = r"^[A-H]([1-9]|1[0-2])$"
MIN_TRANSFER_VOLUME = 25
MAX_TRANSFER_VOLUME = 500000
MIN_WELL_CAPACITY = 1000
MAX_WELL_CAPACITY = 65000


def _create_result() -> ValidationResult:
    return ValidationResult(issues=[], valid=True)


def validate_protocol_columns(protocol_df: pd.DataFrame, result: ValidationResult) -> None:
    """Validate that all required columns are present."""
    present_columns = set(protocol_df.columns)
    missing = REQUIRED_COLUMNS - present_columns
    for column in missing:
        result.add_issue(
            ValidationIssue(
                severity=Severity.ERROR,
                rule="required_columns",
                message=f"Missing required column: {column}",
            )
        )


def validate_well_format(well: str, max_row: str, pattern: str) -> bool:
    """Check if a well string matches the expected pattern."""
    import re
    full_pattern = f"^{pattern}$"
    return bool(re.match(full_pattern, well))


def validate_source_wells(protocol_df: pd.DataFrame, result: ValidationResult) -> None:
    """Validate source well formats (384-well plate)."""
    if "Source Well" not in protocol_df.columns:
        return

    for idx, well in enumerate(protocol_df["Source Well"], start=1):
        well_str = str(well).strip()
        if not well_str:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="source_well_format",
                    message="Empty source well value",
                    row=idx,
                    column="Source Well",
                )
            )
        elif not validate_well_format(well_str, "P", WELL_PATTERN_384):
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="source_well_format",
                    message=f"Invalid 384-well format: {well_str}",
                    row=idx,
                    column="Source Well",
                    well=well_str,
                )
            )


def validate_destination_wells(
    protocol_df: pd.DataFrame, result: ValidationResult, max_wells: int = 96
) -> None:
    """Validate destination well formats (supports 96 or 384 well plates)."""
    if "Destination Well" not in protocol_df.columns:
        return

    pattern = WELL_PATTERN_96 if max_wells <= 96 else WELL_PATTERN_384

    for idx, well in enumerate(protocol_df["Destination Well"], start=1):
        well_str = str(well).strip()
        if not well_str:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="destination_well_format",
                    message="Empty destination well value",
                    row=idx,
                    column="Destination Well",
                )
            )
        elif not validate_well_format(well_str, "H" if max_wells <= 96 else "P", pattern):
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="destination_well_format",
                    message=f"Invalid {'96' if max_wells <= 96 else '384'}-well format: {well_str}",
                    row=idx,
                    column="Destination Well",
                    well=well_str,
                )
            )


def validate_transfer_volumes(protocol_df: pd.DataFrame, result: ValidationResult) -> None:
    """Validate transfer volumes are within Echo-recommended bounds."""
    if "Transfer Volume" not in protocol_df.columns:
        return

    for idx, value in enumerate(protocol_df["Transfer Volume"], start=1):
        try:
            volume = int(value)
        except (ValueError, TypeError):
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="transfer_volume_type",
                    message=f"Invalid transfer volume: {value}",
                    row=idx,
                    column="Transfer Volume",
                )
            )
            continue

        if volume < MIN_TRANSFER_VOLUME:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="transfer_volume_bounds",
                    message=f"Transfer volume {volume} nL below minimum {MIN_TRANSFER_VOLUME} nL (Echo may not dispense accurately)",
                    row=idx,
                    column="Transfer Volume",
                )
            )
        elif volume > MAX_TRANSFER_VOLUME:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="transfer_volume_bounds",
                    message=f"Transfer volume {volume} nL exceeds maximum {MAX_TRANSFER_VOLUME} nL",
                    row=idx,
                    column="Transfer Volume",
                )
            )


def validate_destination_duplicates(protocol_df: pd.DataFrame, result: ValidationResult) -> None:
    """Check for destination wells with multiple transfers from the same source."""
    if "Destination Well" not in protocol_df.columns or "Source Well" not in protocol_df.columns:
        return

    destination_source_groups = protocol_df.groupby(["Destination Well", "Source Well"]).size()
    duplicates = destination_source_groups[destination_source_groups > 1]

    if not duplicates.empty:
        for (dest_well, src_well), count in duplicates.items():
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="destination_duplicates",
                    message=f"Destination {dest_well} receives {count} transfers from source {src_well} (may indicate duplicate dispensing)",
                    well=dest_well,
                )
            )


def validate_conflicting_transfers(protocol_df: pd.DataFrame, result: ValidationResult) -> None:
    """Check for same destination receiving different samples."""
    if "Destination Well" not in protocol_df.columns or "Sample Name" not in protocol_df.columns:
        return

    sample_groups = (
        protocol_df.groupby("Destination Well")["Sample Name"].nunique()
    )
    conflicts = sample_groups[sample_groups > 1]

    if not conflicts.empty:
        for dest_well in conflicts.index:
            samples = protocol_df[protocol_df["Destination Well"] == dest_well]["Sample Name"].unique()
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    rule="conflicting_transfers",
                    message=f"Destination {dest_well} receives multiple samples: {list(samples)}",
                    well=dest_well,
                )
            )


def validate_protocol(
    protocol_csv_path: Path | pd.DataFrame,
    max_destination_wells: int = 96,
    stop_on_error: bool = True,
) -> ValidationResult:
    """Run a complete validation suite on an Echo protocol.

    Args:
        protocol_csv_path: Path to a protocol CSV or a loaded DataFrame
        max_destination_wells: 96 for 96-well plates, 384 for 384-well plates
        stop_on_error: If True, stop validating after reaching 10 errors

    Returns:
        ValidationResult with all issues found
    """
    if isinstance(protocol_csv_path, Path):
        protocol_df = pd.read_csv(protocol_csv_path)
    else:
        protocol_df = protocol_csv_path

    result = _create_result()

    validate_protocol_columns(protocol_df, result)
    if result.errors() and stop_on_error:
        return result

    validate_source_wells(protocol_df, result)
    validate_destination_wells(protocol_df, result, max_destination_wells)
    validate_transfer_volumes(protocol_df, result)
    validate_destination_duplicates(protocol_df, result)
    validate_conflicting_transfers(protocol_df, result)

    return result


def validate_source_plate(
    source_csv_path: Path | pd.DataFrame,
    max_volume_per_well: int = MAX_WELL_CAPACITY,
) -> ValidationResult:
    """Validate a source plate CSV.

    Args:
        source_csv_path: Path to a source plate CSV or a loaded DataFrame
        max_volume_per_well: Maximum expected volume per well

    Returns:
        ValidationResult with all issues found
    """
    if isinstance(source_csv_path, Path):
        plate_df = pd.read_csv(source_csv_path, index_col=0)
    else:
        plate_df = source_csv_path

    result = _create_result()

    plate_rows = list("ABCDEFGHIJKLMNOP")
    plate_columns = list(range(1, 25))

    for row_label in plate_rows:
        if row_label not in plate_df.index:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="source_plate_row",
                    message=f"Missing expected row: {row_label}",
                )
            )

    for column_label in plate_columns:
        if column_label not in plate_df.columns:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    rule="source_plate_column",
                    message=f"Missing expected column: {column_label}",
                )
            )

    for row_label, row in plate_df.iterrows():
        if row_label not in plate_rows:
            continue
        for column_label, cell_value in row.items():
            if column_label not in plate_columns:
                continue
            cell_str = str(cell_value).strip()
            if not cell_value or cell_value == "":
                continue

            import re
            match = re.match(r"^([^:]+):\s*(\d+)nL$", cell_str)
            if not match:
                result.add_issue(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        rule="source_plate_cell_format",
                        message=f"Unparseable cell format at {row_label}{column_label}: {cell_str}",
                        well=f"{row_label}{column_label}",
                    )
                )
                continue

            _, volume_str = match.groups()
            try:
                volume = int(volume_str)
                if volume > MAX_WELL_CAPACITY:
                    result.add_issue(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            rule="source_plate_volume",
                            message=f"Volume {volume} nL exceeds well capacity at {row_label}{column_label}",
                            well=f"{row_label}{column_label}",
                        )
                    )
            except ValueError:
                result.add_issue(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        rule="source_plate_volume",
                        message=f"Invalid volume at {row_label}{column_label}: {volume_str}",
                        well=f"{row_label}{column_label}",
                    )
                )

    return result