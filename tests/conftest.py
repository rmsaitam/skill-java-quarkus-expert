import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "java-quarkus" / "scripts"
VALIDATORS = ROOT / "scripts"

for path in (str(SCRIPTS), str(VALIDATORS)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def fixtures() -> Path:
    return ROOT / "tests" / "fixtures"


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    target = tmp_path / "plugin"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(
            ".git", ".pytest_cache", ".venv", "__pycache__",
            ".coverage", "coverage.xml", "htmlcov",
        ),
    )
    return target
