"""
Multithreading SomaticSniper

@author: Shenglai Li
"""

import argparse
import logging
import os
import pathlib
import shlex
import subprocess
import sys
import tempfile
import threading
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from textwrap import dedent
from types import SimpleNamespace
from typing import List, Optional

logger = logging.getLogger(__name__)

COMMANDS = SimpleNamespace(
    highconfidence=dedent(
        """
        perl {highconfidence}
        --snp-file {loh_output}
        """
    ).strip(),
    samtools="samtools view -b {bam_path} {region}",
    somatic_sniper=dedent(
        """
        {somaticsniper_binary}
        -q {map_q}
        -Q {base_q}
        -s {pps}
        -T {theta}
        -N {nhap}
        -r {pd}
        -F {fout}
        {extra_args}
        -f {reference_path}
        {tumor_bam}
        {normal_bam}
        {output_file}
        """
    ).strip(),
    snpfilter=dedent(
        """
        perl {snpfilter}
        --snp-file {output_vcf_file}
        --indel-file {indel_file}
        """
    ).strip(),
)


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


def tpe_submit_commands(run_args, mpileups: List[str], thread_count: int):
    """run commands on number of threads"""
    with ThreadPoolExecutor(max_workers=thread_count) as e:
        for region_mpileup in mpileups:
            # Build samtools view commands
            # Build somatic sniper command
            e.submit(multithread_somaticsniper, run_args, region_mpileup)


def multithread_somaticsniper(run_args, region: str):
    # with tempdir
    # normal bam region view
    # tumor bam region view
    # somatic sniper call
    # snpfilter
    # high confidence
    # annotate output
    normal_bam_view = samtools_command(run_args.normal_bam, region_mpileup)
    tumor_bam_view = samtools_command(run_args.tumor_bam, region_mpileup)
    with tempfile.TemporaryDirectory() as tmpdir:
        normal_bam_view_file_name = "{region}.normal.bam".format(region)
        normal_bam_view_file_path = os.path.join(tmpdir, normal_bam_view_file_name)

        tumor_bam_view_file_name = "{region}.tumor.bam".format(region)
        tumor_bam_view_file_path = os.path.join(tmpdir, tumor_bam_view_file_name)

        with open(normal_bam_view_file_path, 'w') as norm:
            run_subprocess_command(normal_bam_view, stdout=norm)
        with open(tumor_bam_view_file_path, 'w') as tum:
            run_subprocess_command(normal_bam_view, stdout=tum)

        base = get_region_from_name(region)
        output_vcf_file = "{base}.vcf".format(base=base)
        somatic_sniper_command = COMMANDS.somatic_sniper.format(
            somaticsniper_binary=run_args.somaticsniper_bin,
            map_q=run_args.map_q,
            base_q=run_args.base_q,
            pps=run_args.pps,
            theta=run_args.theta,
            nhap=run_args.nhap,
            pd=run_args.pd,
            fout=run_args.fout,
            extra_args=run_args.flags,
            reference_path=run_args.reference_path,
            tumor_bam=tumor_bam_view_file_path,
            normal_bam=normal_bam_view_file_path,
            output_file=output_vcf_file,
        )
        stdout, stderr = run_subprocess_command(
            somatic_sniper_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )


def annotate_filter(raw, post_filter, new):
    """Annotate post filter vcf"""
    filter_pass = (
        '##FILTER=<ID=PASS,Description="Accept as a high confident somatic mutation">'
    )
    filter_reject = (
        '##FILTER=<ID=REJECT,Description="Rejected as an unconfident somatic mutation">'
    )
    filter_loh = '##FILTER=<ID=LOH,Description="Rejected as a loss of heterozygosity">'
    writer = open(new, "w")
    r = open(raw)
    filtered = open(post_filter)
    hc = set(r).intersection(filtered)
    r.close()
    filtered.close()
    try:
        with open(raw) as f:
            for line in f:
                if line.startswith("##reference"):
                    writer.write(line)
                    writer.write("{}\n".format(filter_pass))
                    writer.write("{}\n".format(filter_reject))
                    writer.write("{}\n".format(filter_loh))
                elif line.startswith("#"):
                    writer.write(line)
                elif line in hc:
                    new = line.split("\t")
                    new[6] = "LOH"
                    writer.write("\t".join(new))
                else:
                    new = line.split("\t")
                    new[6] = "REJECT"
                    writer.write("\t".join(new))
    finally:
        writer.close()


def somatic_sniper_command(region, run_args):
    calling_cmd = [
        "bam-somaticsniper",
        "-q",
        str(dct["map_q"]),
        "-Q",
        str(dct["base_q"]),
        "-s",
        str(dct["pps"]),
        "-T",
        str(dct["theta"]),
        "-N",
        str(dct["nhap"]),
        "-r",
        str(dct["pd"]),
        "-F",
        str(dct["fout"]),
    ]
    if dct["loh"]:
        calling_cmd += ["-L"]
    if dct["gor"]:
        calling_cmd += ["-G"]
    if dct["psc"]:
        calling_cmd += ["-p"]
    if dct["ppa"]:
        calling_cmd += ["-J"]
    calling_cmd += [
        "-f",
        dct["reference_path"],
        "<(samtools view -b {} {})".format(dct["tumor_bam"], region),
        "<(samtools view -b {} {})".format(dct["normal_bam"], region),
        output_vcf_file,
    ]


def samtools_command(bam_path: str, mpileup_file: str) -> str:
    region = get_region_from_name(mpileup_file)
    return COMMANDS.samtools.format(bam_path=bam_path, region=region)


def snpfilter_command():
    loh_filter_cmd = [
        "perl",
        "/opt/somatic-sniper-1.0.5.0/src/scripts/snpfilter.pl",
        "--snp-file",
        output_vcf_file,
        "--indel-file",
        mpileup,
    ]
    loh_output = "{}.SNPfilter".format(output_vcf_file)


def highconfidence_command():
    hc_filter_cmd = [
        "perl",
        "/opt/somatic-sniper-1.0.5.0/src/scripts/highconfidence.pl",
        "--snp-file",
        loh_output,
    ]


def somaticsniper(dct, mpileup, logger, shell_var=True):
    """run somaticsniper workflow"""

    # Open tempdir and output view files
    # 1. Perform samtools view on tumor bam given mpileup region
    # 2. Perform samtools view on normal bam given mpileup region

    output_base = get_file_basename(mpileup)
    region = get_region_from_name(output_base)

    output_vcf_file = "{base}.vcf".format(base=output_base)

    logger.info("SomaticSniper Args: %s", " ".join(calling_cmd))
    calling_output = subprocess_commands_pipe(
        " ".join(calling_cmd), logger, shell_var=shell_var
    )
    if calling_output != 0:
        logger.error("Failed on SomaticSniper calling")
    loh_output = "{}.SNPfilter".format(output_vcf_file)
    logger.info("LOH filtering Args: %s", " ".join(loh_filter_cmd))
    loh_cmd_output = subprocess_commands_pipe(
        " ".join(loh_filter_cmd), logger, shell_var=shell_var
    )
    hc_output = loh_output + ".hc"
    hc_cmd_output = subprocess_commands_pipe(
        " ".join(hc_filter_cmd), logger, shell_var=shell_var
    )

    annotated_vcf = output_base + ".annotated.vcf"
    annotate_filter(output_vcf_file, hc_output, annotated_vcf)


def merge_outputs(output_list, merged_file):
    """Merge scattered outputs"""
    first = True
    with open(merged_file, "w") as oh:
        for out in output_list:
            with open(out) as fh:
                for line in fh:
                    if first or not line.startswith("#"):
                        oh.write(line)
            first = False
    return merged_file


def get_file_size(filename):
    """ Gets file size """
    fstats = os.stat(filename)
    return fstats.st_size


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


def run(run_args):
    tpe_submit_commands(kwargs, kwargs["mpileup"], kwargs["thread_count"], logger)

    # Check outputs
    vcfs = glob.glob("*.annotated.vcf")
    assert len(vcfs) == len(kwargs["mpileup"]), "Missing output!"
    if any(get_file_size(x) == 0 for x in vcfs):
        logger.error("Empty output detected!")

    # Merge
    merged = "multi_somaticsniper_merged.vcf"
    merge_outputs(vcfs, merged)


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
