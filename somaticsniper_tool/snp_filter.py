#!/usr/bin/env python3
import logging
from textwrap import dedent

from somaticsniper_tool import utils

logger = logging.getLogger(__name__)


class SnpFilter:
    COMMAND = dedent(
        """
        perl {snpfilter}
        --snp-file {vcf_file}
        --indel-file {indel_file}
        """
    ).strip()

    def __init__(self, timeout, snpfilter: str, vcf_file: str, indel_mpileup_file: str):
        self.snpfilter = snpfilter
        self.vcf_file = vcf_file
        self.indel_mpileup_file = indel_mpileup_file
        self.timeout = timeout

    def run(self, _utils=utils):
        cmd = self.COMMAND.format(
            snpfilter=self.snpfilter,
            vcf_file=self.vcf_file,
            indel_file=self.indel_mpileup_file,
        )
        popen_return = _utils.run_subprocess_command(cmd, self.timeout)
        logger.info(cmd)
        logger.debug(popen_return.stdout)
        logger.debug(popen_return.stderr)


# __END__
