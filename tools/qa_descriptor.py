"""Launcher descriptors for the disposable QA user directories."""
from pathlib import Path


def text(name: str, path: Path) -> str:
    """A .mod file for `path`. The mod itself keeps its own descriptor (it is a total conversion
    and needs its replace_path lines); a QA overlay gets a minimal one."""
    own = path / 'descriptor.mod'
    if own.exists():
        return own.read_text(encoding='utf-8-sig').rstrip() + f'\npath="{path.as_posix()}"\n'
    return f'name="{name}"\npath="{path.as_posix()}"\nsupported_version="1.20.*"\n'
