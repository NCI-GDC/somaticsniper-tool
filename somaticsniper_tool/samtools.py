#!/usr/bin/env python3

import logging
import tempfile
from types import SimpleNamespace

from somaticsniper_tool import utils

logger = logging.getLogger(__name__)

DI = SimpleNamespace(tempfile=tempfile)


class SamtoolsView:
    """Create tempfile from view of BAM file."""

    COMMAND_STR = "{samtools} view -b {bam_path} {region}"

    def __init__(
        self, timeout, samtools: str, bam_file: str, region: str, _utils=utils, _di=DI
    ):
        self.timeout = timeout
        self.samtools = samtools
        self.bam_file = bam_file
        self.region = region

        self._utils = _utils

        self.temp_view_fh = _di.tempfile.NamedTemporaryFile()
        self.temp_view_name = self.temp_view_fh.name

    def __enter__(self):
        self.write_view()
        return self.temp_view_name

    def __exit__(self, type, value, traceback):
        self.temp_view_fh.close()

    def write_view(self):
        cmd = self.COMMAND_STR.format(
            samtools=self.samtools, bam_path=self.bam_file, region=self.region
        )
        popen_return = self._utils.run_subprocess_command(
            cmd, self.timeout, stdout=self.temp_view_fh
        )
        logger.info(cmd)
        logger.debug(popen_return.stdout)
        logger.debug(popen_return.stderr)
        self.temp_view_fh.seek(0)


# __END__
