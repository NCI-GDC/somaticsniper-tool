#!/usr/bin/env python3

import os
import shlex
import subprocess
from types import SimpleNamespace
from typing import IO, List, NamedTuple, Optional

DI = SimpleNamespace(open=open, os=os, subprocess=subprocess)


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
    """Run command via Popen.
    Accepts:
        cmd (str): Command-string to run
        timeout (int): Max seconds to wait for command
        kwargs (dict): Additional arguments to Popen
    Returns:
        PopenReturn: NamedTuple with stdout and stderr attributes
    """

    if kwargs.get("shell", False):
        # Do not split command for shell
        p = _di.subprocess.Popen(cmd, **kwargs)
    else:
        p = _di.subprocess.Popen(shlex.split(cmd), **kwargs)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
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


def merge_outputs(files: List[str], merged_file: IO, _di=DI):
    """Add non-comment lines from list of files to output file.
    Accepts:
        files: List of file paths
        merged_file (IO): File handler of output file
    """
    first = True
    for out in files:
        with _di.open(out) as fh:
            for line in fh:
                if first or not line.startswith("#"):
                    merged_file.write(line)
        first = False


# __END__
