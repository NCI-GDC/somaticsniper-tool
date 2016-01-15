import setupLog
import pipelineUtil
import os
import logging
import argparse
import somaticsniper

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Variant calling using Somatic-Sniper")
    required = parser.add_argument_group("Required input parameters")
    required.add_argument("--ref", default=None, help="path to reference genome", required=True)
    required.add_argument("--normal", default=None, help="path to normal bam file", required=True)
    required.add_argument("--tumor", default=None, help="path to tumor bam file", required=True)
    required.add_argument("--snp", default=None, help="path to output snp file", required=True)


    optional = parser.add_argument_group("optional input parameters")
    optional.add_argument("--uuid", default="unknown", help="unique identifier")
    optional.add_argument("--outdir", default="./", help="path for logs etc.")

    sniper = parser.add_argument_group("Somaticsniper input parameters")
    sniper.add_argument("-q", default="0", help="filtering reads with mapping quality less than this value")
    sniper.add_argument("-Q", default="15", help="filtering somatic snv output with somatic quality less than this value")
    sniper.add_argument("-L", default="F", help="do not report LOH variants as determined by genotypes (T/F)")
    sniper.add_argument("-G", default="F", help="do not report Gain of Reference variants as determined by genotypes (T/F)")
    sniper.add_argument("-p", default="F", help="disable priors in the somatic calculation. Increases sensitivity for solid tumors (T/F)")
    sniper.add_argument("-J", default="F", help="Use prior probabilities accounting for the somatic mutation rate (T/F)")
    sniper.add_argument("-s", default="0.01", help="prior probability of a somatic mutation (implies -J)")
    sniper.add_argument("-T", default="0.85", help="theta in maq consensus calling model (for -c/-g)")
    sniper.add_argument("-N", default="2", help="number of haplotypes in the sample")
    sniper.add_argument("-r", default="0.001", help="prior of a difference between two haplotypes")
    sniper.add_argument("-n", default="NORMAL", help="normal sample id (for VCF header)")
    sniper.add_argument("-t", default="TUMOR", help="tumor sample id (for VCF header)")
    sniper.add_argument("-F", default="vcf", help="select output format: classic/vcf/bed")

    args = parser.parse_args()

    if not os.path.isfile(args.ref):
        raise Exception("Could not find reference file %s, please check that the file exists and the path is correct" %args.ref)

    if not os.path.isfile(args.normal):
        raise Exception("Could not find bam file %s, please check that the file exists and the path is correct" %args.normal)

    if not os.path.isfile(args.tumor):
        raise Exception("Could not find bam file %s, please check that the file exists and the path is correct" %args.tumor)

    if not os.path.abspath(args.snp):
        raise Exception("Could not find directory %s, please chec that the directory exists and the path is correct" %os.path.abspath(args.snp))


    log_file = "%s.somaticsniper.log" %(os.path.join(args.outdir, args.uuid))
    logger = setupLog.setup_logging(logging.INFO, args.uuid, log_file)

    exit_code = somaticsniper.run_somaticsniper(args, args.ref, args.tumor, args.normal, args.snp, logger)

    if not exit_code:
        logger.info("somatic-sniper completed successfully")
    else:
        raise Exception("Somatic sniper exited with a non-zero exitcode: %s" %exit_code)


