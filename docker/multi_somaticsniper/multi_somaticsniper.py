"""
Multithreading SomaticSniper

@author: Shenglai Li
"""

import os
import sys
import time
import logging
import glob
import argparse
import subprocess
from functools import partial
from multiprocessing.dummy import Pool


def setup_logger():
    """
    Sets up the logger.
    """
    logger = logging.getLogger("multi_somaticsniper")
    logger_format = "[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s"
    logger.setLevel(level=logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(logger_format, datefmt="%Y%m%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def run_command(cmd, logger, shell_var=False):
    """Runs a subprocess"""
    try:
        child = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell_var,
            executable="/bin/bash",
        )
        stdoutdata, stderrdata = child.communicate()
        logger.info(stdoutdata)
        logger.info(stderrdata)
    except BaseException as err:
        logger.error("Command failed %s", cmd)
        logger.error("Command Error: %s", err)
    return child.returncode


def multi_commands(dct, mpileups, thread_count, logger, shell_var=True):
    """run commands on number of threads"""
    pool = Pool(int(thread_count))
    output = pool.map(
        partial(somaticsniper, dct, logger=logger, shell_var=shell_var), mpileups
    )
    return output


def get_region(mpileup):
    """ger region from mpileup filename"""
    namebase = os.path.basename(mpileup)
    base, _ = os.path.splitext(namebase)
    region = base.replace("-", ":", 1)
    return region, base


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


def somaticsniper(dct, mpileup, logger, shell_var=True):
    """run somaticsniper workflow"""
    region, output_base = get_region(mpileup)
    output = output_base + ".vcf"
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
        output,
    ]
    logger.info("SomaticSniper Args: %s", " ".join(calling_cmd))
    calling_output = run_command(
        " ".join(calling_cmd), logger, shell_var=shell_var
    )
    if calling_output != 0:
        logger.error("Failed on SomaticSniper calling")
        return calling_output
    else:
        loh_filter_cmd = [
            "perl",
            "/opt/somatic-sniper-1.0.5.0/src/scripts/snpfilter.pl",
            "--snp-file",
            output,
            "--indel-file",
            mpileup,
        ]
        loh_output = output + ".SNPfilter"
        logger.info("LOH filtering Args: %s", " ".join(loh_filter_cmd))
        loh_cmd_output = run_command(
            " ".join(loh_filter_cmd), logger, shell_var=shell_var
        )
        if loh_cmd_output != 0:
            logger.error("Failed on LOH filtering")
            return loh_cmd_output
        else:
            hc_filter_cmd = [
                "perl",
                "/opt/somatic-sniper-1.0.5.0/src/scripts/highconfidence.pl",
                "--snp-file",
                loh_output,
            ]
            hc_output = loh_output + ".hc"
            logger.info("High confidence filtering Args: %s", " ".join(hc_filter_cmd))
            hc_cmd_output = run_command(
                " ".join(hc_filter_cmd), logger, shell_var=shell_var
            )
            if hc_cmd_output != 0:
                logger.error("Failed on HC filtering")
                return hc_cmd_output
            else:
                annotated_vcf = output_base + ".annotated.vcf"
                try:
                    logger.info("Annotating raw VCF: %s", output)
                    annotate_filter(output, hc_output, annotated_vcf)
                except BaseException as err:
                    logger.error("Annotation failed")
                    logger.error("Command Error: %s", err)
                    return 1
    return 0


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


def get_args():
    """
    Loads the parser.
    """
    # Main parser
    parser = argparse.ArgumentParser("Internal multithreading SomaticSniper calling.")
    # Required flags.
    parser.add_argument(
        "-f",
        "--reference_path",
        required=True,
        help="Reference path."
    )
    parser.add_argument(
        "-t",
        "--tumor_bam",
        required=True,
        help="Tumor bam file."
    )
    parser.add_argument(
        "-n",
        "--normal_bam",
        required=True,
        help="Normal bam file."
    )
    parser.add_argument(
        "-c",
        "--thread_count",
        type=int,
        required=True,
        help="Number of thread."
    )
    parser.add_argument(
        "-m",
        "--mpileup",
        action="append",
        required=True,
        help='A list of normal-tumor samtools mpileup files on different region. \
            Created by "samtools mpileup -f". The file name must contain region. \
            e.g. chr1-1-248956422.mpileup',
    )
    # Optional flags.
    parser.add_argument(
        "-q",
        "--map_q",
        default=1,
        type=int,
        help="filtering reads with mapping quality less than this value.",
    )
    parser.add_argument(
        "-Q",
        "--base_q",
        default=15,
        type=int,
        help="filtering somatic snv output with somatic quality less than this value.",
    )
    parser.add_argument(
        "-L",
        "--loh",
        action="store_true",
        help="do not report LOH variants as determined by genotypes (T/F).",
    )
    parser.add_argument(
        "-G",
        "--gor",
        action="store_true",
        help="do not report Gain of Reference variants as determined by genotypes (T/F).",
    )
    parser.add_argument(
        "-p",
        "--psc",
        action="store_true",
        help="disable priors in the somatic calculation. \
            Increases sensitivity for solid tumors (T/F).",
    )
    parser.add_argument(
        "-J",
        "--ppa",
        action="store_true",
        help="Use prior probabilities accounting for the somatic mutation rate (T/F).",
    )
    parser.add_argument(
        "-s",
        "--pps",
        default=0.01,
        type=float,
        help="prior probability of a somatic mutation (implies -J).",
    )
    parser.add_argument(
        "-T",
        "--theta",
        default=0.85,
        type=float,
        help="theta in maq consensus calling model (for -c/-g).",
    )
    parser.add_argument(
        "-N",
        "--nhap",
        default=2,
        type=int,
        help="number of haplotypes in the sample."
    )
    parser.add_argument(
        "-r",
        "--pd",
        default=0.001,
        type=float,
        help="prior of a difference between two haplotypes.",
    )
    parser.add_argument(
        "-F",
        "--fout",
        default="vcf",
        help="output format (classic/vcf/bed)."
    )
    return parser.parse_args()


def main(args, logger):
    """main"""
    logger.info("Running SomaticSniper 1.0.5.0")
    dct = vars(args)
    outputs = multi_commands(dct, dct["mpileup"], dct["thread_count"], logger)
    if any(x != 0 for x in outputs):
        logger.error("Failed multi_somaticsniper")
    else:
        vcfs = glob.glob("*.annotated.vcf")
        merged = "multi_somaticsniper_merged.vcf"
        try:
            merge_outputs(vcfs, merged)
        except BaseException as err:
            logger.error("Merge outputs failed")
            logger.error("Command Error: %s", err)
        assert os.stat(merged).st_size != 0, "Merged VCF is Empty"
        logger.info("Completed multi_somaticsniper")


if __name__ == "__main__":
    # CLI Entrypoint.
    start = time.time()
    logger_ = setup_logger()
    logger_.info("-" * 80)
    logger_.info("multi_somaticsniper.py")
    logger_.info("Program Args: %s", " ".join(sys.argv))
    logger_.info("-" * 80)

    args_ = get_args()

    # Process
    logger_.info(
        "Processing tumor and normal bam files %s, %s",
        os.path.basename(args_.tumor_bam),
        os.path.basename(args_.normal_bam),
    )
    main(args_, logger_)

    # Done
    logger_.info("Finished, took %s seconds", round(time.time() - start, 2))
