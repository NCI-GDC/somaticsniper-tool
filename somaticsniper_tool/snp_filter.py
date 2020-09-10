#!/usr/bin/env python3

from textwrap import dedent

from somaticsniper_tool import utils


class SnpFilter:
    COMMAND = dedent(
        """
        perl {snpfilter}
        --snp-file {vcf_file}
        --indel-file {indel_file}
        """
    ).strip()

    def __init__(self, snpfilter: str, vcf_file: str, indel_mpileup_file: str):
        self.snpfilter = snpfilter
        self.vcf_file = vcf_file
        self.indel_mpileup_file = indel_mpileup_file

    def run(self, _utils=utils):
        cmd = self.COMMAND.format(
            snpfilter=self.snpfilter,
            vcf_file=self.vcf_file,
            indel_file=self.indel_mpileup_file,
        )
        _utils.run_subprocess_command(cmd)


# __END__
