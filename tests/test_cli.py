"""Tests for the config-manager command line."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from config_manager.cli import main
from config_manager.handlers import get_handler
from config_manager.schemas import ConfigDocument


@pytest.fixture
def config(samples_dir: Path, tmp_path: Path) -> Path:
    target = tmp_path / "app_config.json"
    shutil.copy(samples_dir / target.name, target)
    return target


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


# --- discover -------------------------------------------------------------


def test_discover(capsys: pytest.CaptureFixture[str], samples_dir: Path, tmp_path: Path) -> None:
    for fmt in ("xml", "json", "csv"):
        shutil.copy(samples_dir / f"app_config.{fmt}", tmp_path)
    code, out, _ = run(capsys, "discover", str(tmp_path))
    assert code == 0
    lines = out.splitlines()
    assert [Path(line.split("  ")[-1]).name for line in lines[:-1]] == [
        "app_config.csv", "app_config.json", "app_config.xml",
    ]
    assert lines[-1] == f"3 config file(s) under {tmp_path}"


def test_discover_missing_dir(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code, _, err = run(capsys, "discover", str(tmp_path / "nope"))
    assert code == 1
    assert err.startswith("error: Not a directory")


# --- validate -------------------------------------------------------------


@pytest.mark.parametrize("fmt", ["json", "csv", "xml"])
def test_validate_ok(capsys: pytest.CaptureFixture[str], samples_dir: Path, fmt: str) -> None:
    path = samples_dir / f"app_config.{fmt}"
    assert run(capsys, "validate", str(path)) == (0, f"{path}: valid (6 entries)\n", "")


def test_validate_lists_issues(capsys: pytest.CaptureFixture[str], fixtures_dir: Path) -> None:
    code, out, err = run(capsys, "validate", str(fixtures_dir / "invalid_config.json"))
    assert code == 1
    assert out == ""
    assert err.splitlines() == [
        "error: invalid config:",
        "  metadata.version: is required",
        "  entries[0].value: expected int, got str 'not-a-number'",
        "  entries[1].key: is required",
        "  entries[2].type: unsupported type 'enum' (expected bool, float, int, str)",
    ]


@pytest.mark.parametrize(
    ("name", "content"),
    [("broken.json", "{oops"), ("broken.xml", "<config>"), ("a.yaml", "x: 1")],
)
def test_validate_unreadable(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, name: str, content: str
) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    code, _, err = run(capsys, "validate", str(path))
    assert code == 1
    assert err.startswith("error: ")


def test_validate_missing_file(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code, _, err = run(capsys, "validate", str(tmp_path / "missing.json"))
    assert code == 1
    assert "missing.json" in err


# --- convert --------------------------------------------------------------


def test_convert(
    capsys: pytest.CaptureFixture[str],
    samples_dir: Path,
    tmp_path: Path,
    sample_document: ConfigDocument,
) -> None:
    source, target = samples_dir / "app_config.json", tmp_path / "out" / "app.xml"
    code, out, _ = run(capsys, "convert", str(source), str(target))
    assert code == 0
    assert out == f"Converted {source} -> {target}\n"
    assert get_handler(target).read(target) == sample_document


def test_convert_unsupported(capsys: pytest.CaptureFixture[str], config: Path) -> None:
    code, _, err = run(capsys, "convert", str(config), str(config.with_suffix(".yaml")))
    assert code == 1
    assert "Unsupported config format" in err


# --- version --------------------------------------------------------------


def test_version_save_list_restore(capsys: pytest.CaptureFixture[str], config: Path) -> None:
    original = config.read_bytes()

    code, out, _ = run(capsys, "version", "save", str(config))
    assert code == 0
    assert out.startswith("Saved ") and ".versions" in out

    config.write_text("edited", encoding="utf-8")
    code, out, _ = run(capsys, "version", "list", str(config))
    assert code == 0
    assert out.splitlines()[0].strip().startswith("1  app_config.")

    code, out, _ = run(capsys, "version", "restore", str(config), "-n", "1")
    assert code == 0
    assert out.startswith(f"Restored {config} from app_config.")
    assert config.read_bytes() == original

    _, out, _ = run(capsys, "version", "list", str(config))
    assert len(out.splitlines()) == 2  # the edited file was saved before restoring


def test_version_list_empty(capsys: pytest.CaptureFixture[str], config: Path) -> None:
    assert run(capsys, "version", "list", str(config)) == (
        0, f"No saved versions of {config}\n", "",
    )


@pytest.mark.parametrize(
    ("extra", "message"),
    [([], "restore needs --number N"), (["-n", "3"], "no version 3; ")],
)
def test_version_restore_errors(
    capsys: pytest.CaptureFixture[str], config: Path, extra: list[str], message: str
) -> None:
    code, _, err = run(capsys, "version", "restore", str(config), *extra)
    assert code == 1
    assert message in err


# --- entry point ----------------------------------------------------------


def test_requires_command(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        main([])
    assert info.value.code == 2


def test_runs_as_module(samples_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "config_manager.cli", "validate",
         str(samples_dir / "app_config.xml")],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert "valid (6 entries)" in result.stdout
