"""Unit tests for check_dby_w09_config; fixtures are synthetic, not Kconfig output."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_dby_w09_config as checker  # noqa: E402


def valid_config_text() -> str:
    symbols = list(checker.REQUIRED_SYMBOLS)
    return "".join(f"CONFIG_{symbol}=y\n" for symbol in symbols)


class ConfigCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.config = Path(self.temp_dir.name) / ".config"
        self.config.write_text(valid_config_text(), encoding="utf-8")

    def invoke(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = checker.main([str(self.config), *args])
        return code, output.getvalue()

    def test_valid_config_passes_with_qcom_smmu_driver(self) -> None:
        code, output = self.invoke()
        self.assertEqual(code, 0)
        self.assertIn("RESULT: PASS", output)

    def test_missing_qcom_smmu_driver_fails(self) -> None:
        text = self.config.read_text(encoding="utf-8").replace(
            "CONFIG_ARM_SMMU_QCOM=y\\n", ""
        )
        self.config.write_text(text, encoding="utf-8")
        code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("CONFIG_ARM_SMMU_QCOM is missing", output)

    def test_missing_required_symbol_fails(self) -> None:
        text = self.config.read_text(encoding="utf-8").replace("CONFIG_SCSI_UFS_QCOM=y\n", "")
        self.config.write_text(text, encoding="utf-8")
        code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("CONFIG_SCSI_UFS_QCOM is missing", output)

    def test_block_layer_disabled_fails(self) -> None:
        text = self.config.read_text(encoding="utf-8").replace(
            "CONFIG_BLOCK=y", "# CONFIG_BLOCK is not set"
        )
        self.config.write_text(text, encoding="utf-8")
        code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("CONFIG_BLOCK is =n", output)

    def test_module_value_fails(self) -> None:
        text = self.config.read_text(encoding="utf-8").replace(
            "CONFIG_PHY_QCOM_QMP_UFS=y", "CONFIG_PHY_QCOM_QMP_UFS=m"
        )
        self.config.write_text(text, encoding="utf-8")
        code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("CONFIG_PHY_QCOM_QMP_UFS is =m", output)

    def test_disabled_value_fails(self) -> None:
        text = self.config.read_text(encoding="utf-8").replace(
            "CONFIG_QCOM_RPMHPD=y", "# CONFIG_QCOM_RPMHPD is not set"
        )
        self.config.write_text(text, encoding="utf-8")
        code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("CONFIG_QCOM_RPMHPD is =n", output)

    def test_conflicting_duplicate_assignments_fail(self) -> None:
        with self.config.open("a", encoding="utf-8") as stream:
            stream.write("CONFIG_SCSI_UFS_QCOM=m\n")
        code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("duplicate assignment for CONFIG_SCSI_UFS_QCOM", output)

    def test_missing_input_fails_clearly(self) -> None:
        missing = self.config.parent / "missing.config"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = checker.main([str(missing)])
        self.assertEqual(code, 1)
        self.assertIn("FileNotFoundError", output.getvalue())

    def test_unreadable_input_fails_clearly(self) -> None:
        output = io.StringIO()
        with mock.patch.object(Path, "open", side_effect=PermissionError("permission denied")):
            with contextlib.redirect_stdout(output):
                code = checker.main([str(self.config)])
        self.assertEqual(code, 1)
        self.assertIn("PermissionError", output.getvalue())

    def test_json_output_is_machine_readable(self) -> None:
        code, output = self.invoke("--json")
        self.assertEqual(code, 0)
        parsed = json.loads(output)
        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["checked_required"], len(checker.REQUIRED_SYMBOLS))

    def test_qcom_smmu_driver_module_value_fails(self) -> None:
        text = self.config.read_text(encoding="utf-8").replace(
            "CONFIG_ARM_SMMU_QCOM=y", "CONFIG_ARM_SMMU_QCOM=m"
        )
        self.config.write_text(text, encoding="utf-8")
        code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("CONFIG_ARM_SMMU_QCOM is =m", output)

if __name__ == "__main__":
    unittest.main()
