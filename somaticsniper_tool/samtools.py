#!/usr/bin/env python3

import logging
import tempfile

from somaticsniper_tool import utils

logger = logging.getLogger(__name__)


class SamtoolsView:
    """Create tempfile from view of BAM file."""

    COMMAND_STR = "samtools view -b {bam_path} {region}"

    def __init__(self, bam_file: str, region: str, _utils=utils):
        self.bam_file = bam_file
        self.region = region

        self._utils = _utils

        self.temp_view_fh = tempfile.NamedTemporaryFile()
        self.temp_view_name = self.temp_view_fh.name

    def __enter__(self):
        try:
            self.write_view()
        except Exception:
            raise
        return self.temp_view_name

    def __exit__(self, type, value, traceback):
        self.temp_view_fio.close()

    def write_view(self):
        cmd = self.COMMAND_STR.format(bam_path=self.bam_file, region=self.region)
        popen_return = self._utils.run_subprocess_command(cmd, stdout=self.temp_view_fh)
        logger.debug(popen_return.stdout)
        logger.debug(popen_return.stderr)
        self.temp_view_fh.seek(0)


# __END__
