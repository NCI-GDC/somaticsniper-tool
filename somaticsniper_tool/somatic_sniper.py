#!/usr/bin/env python3

import logging
from textwrap import dedent
from types import SimpleNamespace
from typing import List

from somaticsniper_tool import utils

logger = logging.getLogger(__name__)


class SomaticSniper:
    """Handler class for running Somatic Sniper"""

    COMMAND = dedent(
        """
        {somaticsniper_bin}
        -q {map_q}
        -Q {base_q}
        -s {pps}
        -T {theta}
        -N {nhap}
        -r {pd}
        -F {out_format}
        {extra_args}
        -f {reference_path}
        {tumor_bam}
        {normal_bam}
        {output_file}
        """
    ).strip()

    # Args from CLI
    somaticsniper_bin: str = None
    map_q: int = None
    base_q: int = None
    pps: float = None
    theta: float = None
    nhap: int = None
    pd: float = None
    out_format: str = None
    flags: List[str] = None
    reference_path: str = None

    def __init__(self, output: str):
        self.output_file = "{output}.vcf".format(output=output)

    def run(self, normal_bam: str, tumor_bam: str, _utils=utils) -> str:
        """Runs somatic sniper command.
        Accepts:
            normal_bam (str): Path to normal bam input
            tumor_bam (str): Path to tumor bam input
        Returns:
            output_file (str): Path to somaticsniper output file
        """
        cmd = self.COMMAND.format(
            somaticsniper_bin=self.somaticsniper_bin,
            map_q=self.map_q,
            base_q=self.base_q,
            pps=self.pps,
            theta=self.theta,
            nhap=self.nhap,
            pd=self.pd,
            out_format=self.out_format,
            extra_args=','.join(self.flags),
            reference_path=self.reference_path,
            tumor_bam=tumor_bam,
            normal_bam=normal_bam,
            output_file=self.output_file,
        )
        popen_return = _utils.run_subprocess_command(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        logger.debug(popen_return.stdout)
        logger.debug(popen_return.stderr)
        return self.output_file

    @classmethod
    def _initialize_args(cls, args: SimpleNamespace = None, **kwargs):
        """Set class props from kwargs."""
        attrs = (
            'somaticsniper_bin',
            'map_q',
            'base_q',
            'pps',
            'theta',
            'nhap',
            'pd',
            'out_format',
            'flags',
            'reference_path',
        )
        args_dict = vars(args) if args else {}
        args_dict.update(kwargs)

        for attr in attrs:
            val = args_dict.get(attr, None)
            setattr(cls, attr, val)


# __END__
