#!/usr/bin/env python3

import os
import shlex
import subprocess
from types import SimpleNamespace
from typing import NamedTuple, Optional

DI = SimpleNamespace(os=os, subprocess=subprocess,)


class PopenReturn(NamedTuple):
    stdout: Optional[str]
    stderr: Optional[str]


def get_region_from_name(file_path: str, _di=DI) -> str:
    """Get region from mpileup filename
    e.g. chr1-1-248956422.mpileup

    Accepts:
        file_path (str): Path to mpileup file
    Returns:
        region (str): Samtools-compatible region
    """
    basename = _di.os.path.basename(file_path)
    base, _ = _di.os.path.splitext(basename)
    region = base.replace("-", ":", 1)
    return region


def run_subprocess_command(
    cmd: str, timeout: int = 3600, _di=DI, **kwargs
) -> PopenReturn:
    """run pool commands"""

    if kwargs.get("shell", False):
        # Do not split command for shell
        p = _di.subprocess.Popen(cmd, **kwargs)
    else:
        p = _di.subprocess.Popen(shlex.split(cmd), **kwargs)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except TimeoutError:
        p.kill()
        stdout, stderr = p.communicate()

    try:
        stdout = stdout.decode()
    except AttributeError:
        # Stdout not captured
        pass
    try:
        stderr = stderr.decode()
    except AttributeError:
        # Stderr not captured
        pass

    return PopenReturn(stdout=stdout, stderr=stderr)


# __END__
