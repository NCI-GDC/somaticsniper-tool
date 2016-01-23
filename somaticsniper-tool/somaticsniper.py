from cdis_pipe_utils import pipe_util
from cdis_pipe_utils import time_util
import os

def run_somaticsniper(args, logger):
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

    cmd += ['-f', args.ref, args.tumor, args.normal, args.snp]
    print cmd
    output = pipe_util.do_command(cmd, logger)
    metrics = time_util.parse_time(output)

    return metrics


