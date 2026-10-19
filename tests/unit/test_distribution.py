"""Deterministic rejection tests for the distribution gate, without builds."""

import importlib.util
import io
import tarfile
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("distribution_gate", ROOT / "scripts/qualify_distribution.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class DistributionGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
        self.files = {
            p.relative_to(ROOT / "src").as_posix(): p.read_bytes()
            for p in (ROOT / "src/giadaware_ai").rglob("*")
            if p.is_file() and (p.suffix == ".py" or p.name == "py.typed")
        }
        self.info = f"giadaware_ai-{self.project['version']}.dist-info/"
        self.files[self.info + "LICENSE"] = (ROOT / "LICENSE").read_bytes()
        self.files[self.info + "METADATA"] = (
            f"Name: giadaware-ai\nVersion: {self.project['version']}\n"
            "Requires-Python: >=3.11\nLicense-File: LICENSE\n\n"
        ).encode()

    def wheel(self):
        path = self.work / "test.whl"
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in self.files.items():
                archive.writestr(name, data)
        return path

    def test_valid_contents_are_accepted(self):
        gate.check_archive(self.wheel(), ROOT, self.project)

    def test_missing_typing_marker_is_rejected(self):
        del self.files["giadaware_ai/py.typed"]
        with self.assertRaisesRegex(ValueError, "py.typed"):
            gate.check_archive(self.wheel(), ROOT, self.project)

    def test_truncated_license_is_rejected(self):
        self.files[self.info + "LICENSE"] = b"Apache-2.0\n"
        with self.assertRaisesRegex(ValueError, "LICENSE"):
            gate.check_archive(self.wheel(), ROOT, self.project)

    def test_changed_package_code_is_rejected(self):
        self.files["giadaware_ai/backend.py"] += b"\n# changed\n"
        with self.assertRaisesRegex(ValueError, "backend.py"):
            gate.check_archive(self.wheel(), ROOT, self.project)

    def test_wrong_distribution_version_is_rejected(self):
        self.files[self.info + "METADATA"] = self.files[self.info + "METADATA"].replace(
            f"Version: {self.project['version']}".encode(), b"Version: 99.0.0"
        )
        with self.assertRaisesRegex(ValueError, "Version"):
            gate.check_archive(self.wheel(), ROOT, self.project)

    def test_experiment_payload_is_rejected(self):
        self.files["experiments/payload.py"] = b""
        with self.assertRaisesRegex(ValueError, "development/generated"):
            gate.check_archive(self.wheel(), ROOT, self.project)

    def test_sdist_path_traversal_and_links_are_rejected(self):
        for name, link in (("project/../../escape", False), ("project/link", True)):
            with self.subTest(name=name):
                path = self.work / "test.tar.gz"
                with tarfile.open(path, "w:gz") as archive:
                    member = tarfile.TarInfo(name)
                    if link:
                        member.type = tarfile.SYMTYPE
                        member.linkname = "/outside"
                    archive.addfile(member, io.BytesIO(b""))
                with self.assertRaises(ValueError):
                    gate.archive_files(path)


if __name__ == "__main__":
    unittest.main()
