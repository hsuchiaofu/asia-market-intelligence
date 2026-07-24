#!/usr/bin/env python3
"""Shared filesystem rules for validating the public site tree."""

from __future__ import annotations

import os
import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, Iterator


# Directory names are matched as complete, case-folded path components.
# ``pycache`` is included alongside Python's conventional ``__pycache__``
# because the workflow's exclusion list names both forms in human-readable use.
EXCLUDED_DIRECTORY_COMPONENTS = frozenset(
    {
        ".git",
        ".github",
        ".backups",
        "backup",
        "backups",
        ".tmp",
        "temp",
        "tmp",
        "node_modules",
        "pycache",
        "__pycache__",
        ".codex",
        ".cache",
        "dist",
        "coverage",
    }
)
_EXCLUDED_CASEFOLDED = frozenset(
    component.casefold() for component in EXCLUDED_DIRECTORY_COMPONENTS
)
_SEPARATOR_RE = re.compile(r"[\\/]+")


def path_components(path: str | os.PathLike[str]) -> tuple[str, ...]:
    """Return components for Windows or POSIX syntax on any host OS."""

    return tuple(
        component
        for component in _SEPARATOR_RE.split(os.fspath(path))
        if component not in {"", "."}
    )


def is_excluded_path(
    path: str | os.PathLike[str],
    *,
    root: str | os.PathLike[str] | None = None,
) -> bool:
    """Return whether a path contains an excluded directory component.

    When ``root`` and ``path`` are native paths, only components below the
    project root are considered. This prevents an ancestor directory outside
    the repository from affecting validation.
    """

    candidate = Path(path)
    if root is not None:
        try:
            candidate = candidate.resolve(strict=False).relative_to(
                Path(root).resolve(strict=False)
            )
        except (OSError, ValueError):
            pass
    return any(
        component.casefold() in _EXCLUDED_CASEFOLDED
        for component in path_components(candidate)
    )


def iter_site_files(
    root: str | os.PathLike[str],
    patterns: str | Iterable[str],
) -> Iterator[Path]:
    """Yield matching files while pruning excluded directories at any depth."""

    project_root = Path(root)
    wanted = (patterns,) if isinstance(patterns, str) else tuple(patterns)
    for current, directories, filenames in os.walk(project_root):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory.casefold() not in _EXCLUDED_CASEFOLDED
        )
        current_path = Path(current)
        for filename in sorted(filenames):
            if any(fnmatch(filename, pattern) for pattern in wanted):
                yield current_path / filename

