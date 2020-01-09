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
    except BaseException:
        logger.error("command failed %s", cmd)
    return child.returncode


def multi_commands(dct, mpileups, thread_count, logger, shell_var=True):
    """run commands on number of threads"""
    pool = Pool(int(thread_count))
    output = pool.map(
        partial(somaticsniper, dct, logger, shell_var=shell_var), mpileups
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
    filter_loh = (
        '##FILTER=<ID=LOH,Description="Rejected as a loss of heterozygosity">'
    )
    with open(raw, "rb") as fin:
        with open(post_filter, "rb") as fcom:
            hc = set(fin).intersection(fcom)
            with open(new, "w") as fout:
                for i in fin:
                    if i.startswith("##fileformat"):
                        fout.write(i)
                        fout.write("{}\n".format(filter_pass))
                        fout.write("{}\n".format(filter_reject))
                        fout.write("{}\n".format(filter_loh))
                    elif i.startswith("#"):
                        fout.write(i)
                    elif i in hc:
                        new = i.split("\t")
                        new[6] = "PASS"
                        fout.write("\t".join(new))
                    elif i.split(":")[-2] == "3":
                        new = i.split("\t")
                        new[6] = "LOH"
                        fout.write("\t".join(new))
                    else:
                        new = i.split("\t")
                        new[6] = "REJECT"
                        fout.write("\t".join(new))


def somaticsniper(dct, mpileup, logger, shell_var=True):
    """run somaticsniper workflow"""
    region, output_base = get_region(mpileup)
    output = output_base + ".vcf"
    calling_cmd = [
        "bam-somaticsniper",
        "-q",
        dct["map_q"],
        "-Q",
        dct["base_q"],
        "-s",
        dct["pps"],
        "-T",
        dct["theta"],
        "-N",
        dct["nhap"],
        "-r",
        dct["pd"],
        "-F",
        dct["fout"],
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
        dct["ref"],
        "<(samtools view -b {} {})".format(dct["tumor"], region),
        "<(samtools view -b {} {})".format(dct["normal"], region),
        output,
    ]
    logger.info("SomaticSniper Args: %s", " ".join(calling_cmd))
    calling_output = run_command(
        " ".join(calling_cmd), logger, shell_var=shell_var
    )
    if calling_output != 0:
        logger.error("Failed on SomaticSniper calling")
    else:
        loh_filter_cmd = [
            "perl",
            "/somatic-sniper-1.0.5.0/src/scripts/snpfilter.pl",
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
        else:
            hc_filter_cmd = [
                "perl",
                "/somatic-sniper-1.0.5.0/src/scripts/highconfidence.pl",
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
            else:
                annotated_vcf = output_base + ".annotated.vcf"
                annotate_filter(output, hc_output, annotated_vcf)


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
        "-q",
        "--map_q",
        required=True,
        help="filtering reads with mapping quality less than this value.",
    )
    parser.add_argument(
        "-Q",
        "--base_q",
        required=True,
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
        required=True,
        help="prior probability of a somatic mutation (implies -J).",
    )
    parser.add_argument(
        "-T",
        "--theta",
        required=True,
        help="theta in maq consensus calling model (for -c/-g).",
    )
    parser.add_argument(
        "-N",
        "--nhap",
        required=True,
        help="number of haplotypes in the sample."
    )
    parser.add_argument(
        "-r",
        "--pd",
        required=True,
        help="prior of a difference between two haplotypes.",
    )
    parser.add_argument(
        "-F",
        "--fout",
        required=True,
        help="output format (classic/vcf/bed)."
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
        help="mpileup files."
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
        logger.info("Completed multi_somaticsniper")
        vcfs = glob.glob("*.annotated.vcf")
        merge_outputs(vcfs, "multi_somaticsniper_merged.vcf")


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
