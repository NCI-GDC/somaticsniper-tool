import pipelineUtil
import os

def run_somaticsniper(config, args, ref, tumor, normal, snp, logger):
    """ Run SomaticSniper on a pair of tumor and normal BAM """

    logger.info("Starting run for somatic-sniper")
    cmd =['time', 'bam-somaticsniper',
            '-q', args.q,
            '-Q', args.Q,
            '-s', args.s,
            '-T', args.T,
            '-N', args.N,
            '-r', args.r,
            '-n', args.n,
            '-t', args.t,
            '-F', args.F
            ]

    if args.L == "T": cmd += ["-L"]
    if args.G == "T": cmd += ["-G"]
    if args.p == "T": cmd += ["-p"]
    if args.J == "T": cmd += ["-J"]

    cmd += ['-f', ref, tumor, normal, snp]

    print cmd
    exit_code = pipelineUtil.log_function_time(config, 'somaticsniper', args.uuid, cmd, logger)

    return exit_code


