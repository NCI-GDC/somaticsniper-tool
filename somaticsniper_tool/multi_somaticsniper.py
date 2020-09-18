"""
Multithreading SomaticSniper

@author: Shenglai Li
@author: Charles Czysz
"""

import argparse
import concurrent.futures
import logging
import os
import pathlib
import shlex
import subprocess
import sys
import tempfile
import threading
from collections import namedtuple
from textwrap import dedent
from types import SimpleNamespace
from typing import Callable, List, Optional

from somaticsniper_tool import utils
from somaticsniper_tool._version import __pypi_version__
from somaticsniper_tool.annotate import Annotate
from somaticsniper_tool.high_confidence import HighConfidence
from somaticsniper_tool.samtools import SamtoolsView
from somaticsniper_tool.snp_filter import SnpFilter
from somaticsniper_tool.somatic_sniper import SomaticSniper

logger = logging.getLogger(__name__)

__version__ = __pypi_version__

DI = SimpleNamespace(futures=concurrent.futures, open=open, os=os,)


def setup_logger():
    """
    Sets up the logger.
    """
    logger_format = "[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s"
    logger.setLevel(level=logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(logger_format, datefmt="%Y%m%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def setup_parser() -> argparse.ArgumentParser:
    """
    Loads the parser.
    """
    # Main parser
    parser = argparse.ArgumentParser()
    # Required flags.

    parser.add_argument(
        "--thread-count", type=int, required=True, help="Number of threads."
    )
    parser.add_argument(
        "--mpileup",
        action="append",
        required=True,
        help='A list of normal-tumor samtools mpileup files on different region. \
            Created by "samtools mpileup -f". The file name must contain region. \
            e.g. chr1-1-248956422.mpileup',
    )

    somatic_sniper_group = parser.add_argument_group(
        "Required somaticsniper arguments."
    )
    somatic_sniper_group.add_argument(
        "--reference-path", required=True, help="Reference path."
    )
    somatic_sniper_group.add_argument(
        "--tumor-bam", required=True, help="Tumor bam file."
    )
    somatic_sniper_group.add_argument(
        "--normal-bam", required=True, help="Normal bam file."
    )

    somatic_sniper_flags = parser.add_argument_group("Optional somaticsniper flags.")
    somatic_sniper_flags.add_argument(
        "--loh",
        dest="flags",
        action="append_const",
        const="-L",
        help="do not report LOH variants as determined by genotypes.",
    )
    somatic_sniper_flags.add_argument(
        "--gor",
        dest="flags",
        action="append_const",
        const="-G",
        help="do not report Gain of Reference variants as determined by genotypes.",
    )
    somatic_sniper_flags.add_argument(
        "--psc",
        dest="flags",
        action="append_const",
        const='-p',
        help="disable priors in the somatic calculation. \
            Increases sensitivity for solid tumors.",
    )
    somatic_sniper_flags.add_argument(
        "--ppa",
        action="append_const",
        const='-J',
        help="Use prior probabilities accounting for the somatic mutation rate.",
    )

    somatic_sniper_optional_group = parser.add_argument_group(
        "Optional somaticsniper kwargs"
    )
    somatic_sniper_optional_group.add_argument(
        "--map-q",
        default=1,
        type=int,
        help="filtering reads with mapping quality less than this value.",
    )
    somatic_sniper_optional_group.add_argument(
        "--base-q",
        default=15,
        type=int,
        help="filtering somatic snv output with somatic quality less than this value.",
    )
    somatic_sniper_optional_group.add_argument(
        "--pps",
        default=0.01,
        type=float,
        help="prior probability of a somatic mutation (implies -J).",
    )
    somatic_sniper_optional_group.add_argument(
        "--theta",
        default=0.85,
        type=float,
        help="theta in maq consensus calling model (for -c/-g).",
    )
    somatic_sniper_optional_group.add_argument(
        "--nhap", default=2, type=int, help="number of haplotypes in the sample."
    )
    somatic_sniper_optional_group.add_argument(
        "--pd",
        default=0.001,
        type=float,
        help="prior of a difference between two haplotypes.",
    )
    somatic_sniper_optional_group.add_argument(
        "--out-format",
        default="vcf",
        choices=('classic', 'vcf', 'bed'),
        help="output format (classic/vcf/bed).",
    )

    runtime_group = parser.add_argument_group("Binaries")
    runtime_group.add_argument(
        "--somaticsniper",
        dest="somaticsniper_bin",
        default="bam-somaticsniper",
        help="Path to bam-somaticsniper executable",
    )
    runtime_group.add_argument(
        "--snpfilter",
        default="/scripts/snpfilter.pl",
        help="Path to snpfilter perl script",
    )
    runtime_group.add_argument(
        "--highconfidence",
        default="/scripts/highconfidence.pl",
        help="Path to highconfidence perl script",
    )
    parser.add_argument(
        "--version", action='version', version=__version__,
    )

    return parser


def process_argv(argv: Optional[List] = None) -> namedtuple:

    parser = setup_parser()

    if argv:
        args, unknown_args = parser.parse_known_args(argv)
    else:
        args, unknown_args = parser.parse_known_args()

    args_dict = vars(args)
    args_dict['extras'] = unknown_args

    run_args = namedtuple("RunArgs", list(args_dict.keys()))
    return run_args(**args_dict)


def multithread_somaticsniper(
    mpileup: str,
    normal_bam: str = None,
    tumor_bam: str = None,
    snpfilter: str = None,
    high_confidence: str = None,
    _annotate=Annotate,
    _highconfidence=HighConfidence,
    _samtools=SamtoolsView,
    _somaticsniper=SomaticSniper,
    _snpfilter=SnpFilter,
    _utils=utils,
) -> str:
    """Run multithreaded somaticsniper workflow.
    Accepts:
        run_args (namespace): argparse namespace
        mpileup (str): Path to mpileup file
    Returns:
        annotated_vcf_file (str): Path to annotated vcf
    """

    region = _utils.get_region_from_name(mpileup)

    somatic_sniper = _somaticsniper(region)
    with _samtools(normal_bam, region) as normal_view, _samtools(
        tumor_bam, region
    ) as tumor_view:
        somatic_sniper_vcf = somatic_sniper.run(
            normal_bam=normal_view, tumor_bam=tumor_view
        )

    snp_filter_output = "{}.SNPfilter".format(somatic_sniper_vcf)
    snp_filter = _snpfilter(snpfilter, somatic_sniper_vcf, mpileup)
    snp_filter.run()

    high_confidence_output = "{}.hc".format(snp_filter_output)
    high_confidence = _highconfidence(high_confidence, snp_filter_output)
    high_confidence.run()

    annotated_vcf_file = "{}.annotated.vcf".format(region)
    with _annotate(annotated_vcf_file) as annotate:
        annotate(somatic_sniper_vcf, high_confidence_output)

    return annotated_vcf_file


def tpe_submit_commands(
    run_args, fn: Callable = multithread_somaticsniper, _di=DI
) -> List[str]:
    """run commands on number of threads
    Accepts:
    Returns:
    """
    mpileups = run_args.mpileup
    annotated_vcfs = []
    with _di.futures.ThreadPoolExecutor(max_workers=run_args.thread_count) as executor:
        futures = [
            executor.submit(
                fn,
                region_mpileup,
                normal_bam=run_args.normal_bam,
                tumor_bam=run_args.tumor_bam,
                snpfilter=run_args.snpfilter,
                high_confidence=run_args.highconfidence,
            )
            for region_mpileup in mpileups
        ]
        for future in _di.futures.as_completed(futures):
            try:
                result = future.result()
                logger.info(result)
                annotated_vcfs.append(result)
            except Exception as e:
                logger.exception(e)


def run(run_args, _somaticsniper=SomaticSniper, _utils=utils):

    # Update class attributes
    _somaticsniper._initialize_args(args=run_args)

    annotated_vcfs = tpe_submit_commands(run_args)

    merged_output = "multi_somaticsniper_merged.vcf"
    with open(merged_output, 'w') as out_fh:
        _utils.merge_outputs(annotated_vcfs, out_fh)


def main(argv=None) -> int:
    """main"""
    exit_code = 0
    setup_logger()

    argv = argv or sys.argv
    args = process_argv(argv)

    try:
        run(args)
    except Exception as e:
        logger.exception(e)
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    retcode = 0

    try:
        retcode = main()
    except Exception as e:
        retcode = 1
        logger.exception(e)
    sys.exit(retcode)

# __END
