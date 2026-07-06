from pathlib import Path


def list_paperless_exports(folder):
    root = Path(folder)
    return sorted(path for path in root.rglob("*") if path.is_file())
