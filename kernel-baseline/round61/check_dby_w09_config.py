#!/usr/bin/env python3
"""Validate the DBY-W09 ACK storage-first options in a resolved kernel .config."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_SYMBOLS = (
    "ARM64",
    "ARCH_QCOM",
    "OF",
    "BLOCK",
    "SCSI",
    "BLK_DEV_SD",
    "SCSI_UFSHCD",
    "SCSI_UFSHCD_PLATFORM",
    "SCSI_UFS_QCOM",
    "GENERIC_PHY",
    "PHY_QCOM_QMP",
    "PHY_QCOM_QMP_UFS",
    "COMMON_CLK",
    "COMMON_CLK_QCOM",
    "QCOM_CLK_RPMH",
    "SM_GCC_8250",
    "RESET_CONTROLLER",
    "PM",
    "INTERCONNECT",
    "INTERCONNECT_QCOM",
    "INTERCONNECT_QCOM_SM8250",
    "QCOM_COMMAND_DB",
    "QCOM_RPMH",
    "QCOM_RPMHPD",
    "REGULATOR",
    "REGULATOR_QCOM_RPMH",
    "IOMMU_SUPPORT",
    "ARM_SMMU",
    "ARM_SMMU_QCOM",
    "BLK_DEV_DM",
    "EROFS_FS",
    "DM_VERITY",
    "DM_VERITY_FEC",
)
_SET_RE = re.compile(r"^CONFIG_([A-Z0-9_]+)=(.*)$")
_UNSET_RE = re.compile(r"^# CONFIG_([A-Z0-9_]+) is not set$")


def _read_assignments(path: Path) -> tuple[dict[str, tuple[str, int]], list[str]]:
    """Return first assignments and duplicate/read errors; duplicates always fail."""
    try:
        with path.open("r", encoding="utf-8") as stream:
            lines = stream.readlines()
    except (OSError, UnicodeError) as exc:
        return {}, [f"cannot read .config '{path}': {exc.__class__.__name__}: {exc}"]

    assignments: dict[str, tuple[str, int]] = {}
    duplicate_lines: dict[str, list[int]] = {}

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\r\n")
        match = _SET_RE.fullmatch(line)
        if match:
            symbol, value = match.group(1), match.group(2)
        else:
            match = _UNSET_RE.fullmatch(line)
            if not match:
                continue
            symbol, value = match.group(1), "n"

        if symbol in assignments:
            if symbol not in duplicate_lines:
                duplicate_lines[symbol] = [assignments[symbol][1]]
            duplicate_lines[symbol].append(line_number)
        else:
            assignments[symbol] = (value, line_number)

    errors = [
        f"duplicate assignment for CONFIG_{symbol} on lines "
        + ", ".join(str(number) for number in line_numbers)
        for symbol, line_numbers in sorted(duplicate_lines.items())
    ]
    return assignments, errors


def validate_config(path: Path) -> dict[str, Any]:
    assignments, errors = _read_assignments(path)
    if errors and len(errors) == 1 and errors[0].startswith("cannot read .config"):
        return {
            "ok": False,
            "path": str(path),
            "errors": errors,
            "missing": [],
            "not_y": [],
            "info": [],
            "checked_required": len(REQUIRED_SYMBOLS),
        }

    missing: list[str] = []
    not_y: list[dict[str, str]] = []
    info: list[str] = []

    for symbol in REQUIRED_SYMBOLS:
        assigned = assignments.get(symbol)
        if assigned is None:
            missing.append(symbol)
        elif assigned[0] != "y":
            not_y.append({"symbol": symbol, "value": assigned[0]})

    ok = not errors and not missing and not not_y
    return {
        "ok": ok,
        "path": str(path),
        "errors": errors,
        "missing": missing,
        "not_y": not_y,
        "info": info,
        "checked_required": len(REQUIRED_SYMBOLS),
    }


def _render_human(result: dict[str, Any]) -> str:
    lines = [f"DBY-W09 storage-first .config: {result['path']}"]
    for error in result["errors"]:
        lines.append(f"FAIL: {error}")
    for symbol in result["missing"]:
        lines.append(f"FAIL: CONFIG_{symbol} is missing (required =y)")
    for item in result["not_y"]:
        lines.append(
            f"FAIL: CONFIG_{item['symbol']} is ={item['value']} (required =y)"
        )
    for message in result["info"]:
        lines.append(f"INFO: {message}")
    if result["ok"]:
        lines.append(
            f"PASS: all {result['checked_required']} required storage-first "
            "symbols are present as =y; no duplicate assignments found."
        )
        lines.append("RESULT: PASS")
    else:
        issue_count = (
            len(result["errors"]) + len(result["missing"]) + len(result["not_y"])
        )
        lines.append(f"RESULT: FAIL ({issue_count} issue(s))")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the resolved DBY-W09 ACK storage-first kernel .config."
    )
    parser.add_argument("config", type=Path, help="path to the final resolved .config")
    parser.add_argument(
        "--json", action="store_true", help="emit deterministic JSON instead of text"
    )
    args = parser.parse_args(argv)

    result = validate_config(args.config)
    if args.json:
        print(json.dumps(result, sort_keys=True, indent=2))
    else:
        print(_render_human(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
