"""Offline packaging gate. Outputs evidence under a NEW directory in dist/.

The default frontend is ``python -m build --no-isolation``. ``--backend-only``
uses the declared setuptools PEP 517 hooks with already installed build tools;
it does not claim to verify frontend dependency resolution or build isolation.
Neither mode installs build dependencies. Consumer installation is offline.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import venv
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]


class BuildPrerequisiteError(RuntimeError):
    """A required, already provisioned offline build tool is missing."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(command, *, cwd, env, log):
    log.write("$ " + " ".join(map(str, command)) + "\n")
    log.flush()
    subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=log, check=True)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def archive_files(path):
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    with tarfile.open(path) as archive:
        files = {}
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or not name.parts:
                raise ValueError(f"Unsafe archive member: {member.name}")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"Non-regular archive member: {member.name}")
            relative = PurePosixPath(*name.parts[1:]).as_posix()
            if relative in files:
                raise ValueError(f"Duplicate archive member: {relative}")
            files[relative] = archive.extractfile(member).read()
        return files


def check_archive(path, source, project):
    files = archive_files(path)
    wheel = path.suffix == ".whl"
    expected = {
        p.relative_to(source / "src").as_posix(): p.read_bytes()
        for p in (source / "src/giadaware_ai").rglob("*")
        if p.is_file() and (p.suffix == ".py" or p.name == "py.typed")
    }
    for name, content in expected.items():
        if files.get(name if wheel else "src/" + name) != content:
            raise ValueError(f"Missing or changed package file in {path.name}: {name}")
    if wheel:
        package_files = {name for name in files if name.startswith("giadaware_ai/")}
        if package_files != set(expected):
            raise ValueError(f"Unexpected package files: {package_files - set(expected)}")
    license_files = ["LICENSE"] + [p.name for p in source.glob("NOTICE*") if p.is_file()]
    for name in license_files:
        matches = [key for key in files if (".dist-info/" in key and key.endswith("/" + name))] if wheel else [name]
        if len(matches) != 1 or files.get(matches[0]) != (source / name).read_bytes():
            raise ValueError(f"Missing or changed {name} in {path.name}")
    metadata_names = [name for name in files if name.endswith(".dist-info/METADATA")] if wheel else ["PKG-INFO"]
    if len(metadata_names) != 1:
        raise ValueError("Expected exactly one distribution metadata file")
    metadata = BytesParser().parsebytes(files[metadata_names[0]])
    for field, expected_value in (("Name", project["name"]), ("Version", project["version"]), ("Requires-Python", project["requires-python"])):
        if metadata[field] != expected_value:
            raise ValueError(f"Unexpected {field}: {metadata[field]!r}")
    for name in license_files:
        if not any(PurePosixPath(value).name == name for value in metadata.get_all("License-File", [])):
            raise ValueError(f"Missing License-File metadata: {name}")
    if not wheel:
        for name in ("pyproject.toml", "README.md", "MANIFEST.in", "scripts/qualify_distribution.py", "tests/packaging/smoke_installed.py"):
            if files.get(name) != (source / name).read_bytes():
                raise ValueError(f"Missing or changed sdist input: {name}")
        unit_tests = list((source / "tests/unit").glob("test_*.py"))
        if not unit_tests:
            raise ValueError("No unit tests in source snapshot")
        for test in unit_tests:
            name = test.relative_to(source).as_posix()
            if files.get(name) != test.read_bytes():
                raise ValueError(f"Missing or changed sdist test: {name}")
    forbidden = {"experiments", ".git", ".venv", "dist", "build", "__pycache__"}
    if any(forbidden.intersection(PurePosixPath(name).parts) for name in files):
        raise ValueError(f"Unexpected development/generated content in {path.name}")
    return files


def build(source, output, kind, backend_only, env, log):
    output.mkdir(parents=True)
    if backend_only:
        code = (
            "import sys; from setuptools import build_meta; "
            f"print(build_meta.build_{kind}(sys.argv[1]))"
        )
        command = [sys.executable, "-c", code, str(output)]
    else:
        command = [sys.executable, "-m", "build", "--no-isolation", "--" + kind, "--outdir", str(output), str(source)]
    run(command, cwd=source, env=env, log=log)
    artifacts = list(output.glob("*.whl" if kind == "wheel" else "*.tar.gz"))
    if len(artifacts) != 1:
        raise ValueError(f"Expected exactly one {kind} in {output}")
    return artifacts[0]


def qualify(output, backend_only, evidence, log):
    tracked = git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
    evidence.update({
        "git_head": git("rev-parse", "HEAD").decode().strip(),
        "git_status": git("status", "--porcelain").decode().splitlines(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "frontend": "setuptools PEP 517 hooks (no frontend)" if backend_only else "python -m build --no-isolation",
        "build_isolation": False,
        "source_date_epoch": git("show", "-s", "--format=%ct", "HEAD").decode().strip(),
        "tools": {},
        "artifacts": [],
        "ci": {name: os.environ[name] for name in ("GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT") if name in os.environ},
        "release_authorization": "Not established by packaging qualification",
    })
    for package in ("setuptools", "wheel", "build", "pip", "packaging", "pyproject-hooks"):
        try:
            evidence["tools"][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            evidence["tools"][package] = None
    if evidence["tools"]["setuptools"] is None or tuple(map(int, evidence["tools"]["setuptools"].split(".")[:2])) < (68, 0):
        raise BuildPrerequisiteError("Offline build requires installed setuptools>=68")
    if evidence["tools"]["wheel"] is None:
        raise BuildPrerequisiteError("Offline build with the supported setuptools 68 baseline requires wheel")
    if not backend_only and evidence["tools"]["build"] is None:
        raise BuildPrerequisiteError("Missing build frontend; provision build>=1.2 or use --backend-only")
    env = {**os.environ, "SOURCE_DATE_EPOCH": evidence["source_date_epoch"], "PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PYTHONHASHSEED": "0"}
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    with tempfile.TemporaryDirectory(prefix="giadaware-ai-package-") as temporary:
        work = Path(temporary)
        source = work / "source"
        source.mkdir()
        manifest = {}
        for name in sorted(set(tracked) - {""}):
            path = ROOT / name
            if not path.is_file():
                continue
            if path.is_symlink():
                raise ValueError(f"Source symlink is not supported: {name}")
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            manifest[name] = digest(target.read_bytes())
        evidence["source_files_sha256"] = manifest
        evidence["source_manifest_sha256"] = digest(json.dumps(manifest, sort_keys=True).encode())
        project = tomllib.loads((source / "pyproject.toml").read_text())["project"]
        evidence["distribution"] = {"name": project["name"], "version": project["version"]}
        sdist = build(source, output / "sdist", "sdist", backend_only, env, log)
        wheel = build(source, output / "wheel", "wheel", backend_only, env, log)
        sdist_files = check_archive(sdist, source, project)
        check_archive(wheel, source, project)
        extracted = work / "from-sdist"
        extracted.mkdir()
        for name, data in sdist_files.items():
            target = extracted / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        rebuilt = build(extracted, output / "rebuilt", "wheel", backend_only, env, log)
        check_archive(rebuilt, source, project)
        if wheel.read_bytes() != rebuilt.read_bytes():
            raise ValueError("Source wheel and sdist-rebuilt wheel are not byte-identical")
        evidence["checks"] = {"archive_contents_and_license": "PASS", "sdist_rebuild": "PASS", "byte_identical_wheels": "PASS"}
        for index, artifact in enumerate((wheel, rebuilt)):
            consumer = work / f"consumer-{index}"
            venv.EnvBuilder(with_pip=True).create(consumer)
            python = consumer / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run([str(python), "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(artifact)], cwd=work, env=env, log=log)
            run([str(python), "-I", str(extracted / "tests/packaging/smoke_installed.py")], cwd=work, env=env, log=log)
            run([str(python), "-I", "-m", "unittest", "discover", "-s", str(extracted / "tests/unit"), "-v"], cwd=work, env=env, log=log)
        evidence["checks"]["both_isolated_installations_and_public_api_tests"] = "PASS"
        evidence["status"] = "PASS"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New directory below the repository dist/; existing paths are refused")
    parser.add_argument("--backend-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "dist") or output == ROOT / "dist":
        parser.error("--output must be a new subdirectory of the repository dist/")
    output.mkdir(parents=True, exist_ok=False)
    evidence = {"status": "FAIL"}
    try:
        with (output / "qualification.log").open("x") as log:
            qualify(output, args.backend_only, evidence, log)
    except Exception as exc:
        if isinstance(exc, BuildPrerequisiteError):
            evidence["status"] = "BLOCKED"
        evidence["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        evidence["artifacts"] = [
            {"path": path.relative_to(output).as_posix(), "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
            for path in sorted(output.rglob("*"))
            if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
        ]
        (output / "provenance.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(f"PASS: packaging qualification; evidence in {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
