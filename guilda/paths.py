from pathlib import Path


def _resolve(package_dir: Path) -> Path:
    """Wheel install embeds content in _data/; a checkout uses the repo root."""
    embedded = package_dir / "_data"
    if (embedded / "template.json").is_file():
        return embedded
    return package_dir.parent


def data_root() -> Path:
    return _resolve(Path(__file__).resolve().parent)
