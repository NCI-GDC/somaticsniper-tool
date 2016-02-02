import setupLog
import os
import logging
import argparse
import somaticsniper
from cdis_pipe_utils import postgres

class Somaticsniper(postgres.ToolTypeMixin, postgres.Base):

    __tablename__ = 'somaticsniper_metrics'

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Variant calling using Somatic-Sniper")

    required = parser.add_argument_group("Required input parameters")
    required.add_argument("--ref", default=None, help="path to reference genome", required=True)
    required.add_argument("--normal", default=None, help="path to normal bam file", required=True)
    required.add_argument("--tumor", default=None, help="path to tumor bam file", required=True)
    required.add_argument("--snp", default=None, help="path to output snp file", required=True)
    required.add_argument("--username", default=None, help="username for db access", required=True)
    required.add_argument("--password", default=None, help="password for db access", required=True)

    optional = parser.add_argument_group("optional input parameters")
    optional.add_argument("--normal_id", default="unknown", help="unique identifier for normal dataset")
    optional.add_argument("--tumor_id", default="unknown", help="unique identifier for tumor dataset")
    optional.add_argument("--case_id", default="unknown", help="unique identifier")
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

    db = parser.add_argument_group("Database parameters")
    db.add_argument("--host", default='pgreadwrite.osdc.io', help='hostname for db')
    db.add_argument("--database", default='prod_bioinfo', help='name of the database')

    args = parser.parse_args()

    if not os.path.isfile(args.ref):
        raise Exception("Could not find reference file %s, please check that the file exists and the path is correct" %args.ref)

    if not os.path.isfile(args.normal):
        raise Exception("Could not find bam file %s, please check that the file exists and the path is correct" %args.normal)

    if not os.path.isfile(args.tumor):
        raise Exception("Could not find bam file %s, please check that the file exists and the path is correct" %args.tumor)

    if not os.path.abspath(args.snp):
        raise Exception("Could not find directory %s, please check that the directory exists and the path is correct" %os.path.abspath(args.snp))

    if not os.path.isfile(args.config):
        raise Exception("Could not find config file %s, please check that the file exists and the path is correct" %args.config)

    log_file = "%s.somaticsniper.log" %(os.path.join(args.outdir, args.case_id))
    logger = setupLog.setup_logging(logging.INFO, args.case_id, log_file)

    metrics = somaticsniper.run_somaticsniper(args, logger)

    if not metrics['exit_status']:
        logger.info("somatic-sniper completed successfully")
    else:
        raise Exception("Somatic sniper exited with a non-zero exitcode: %s" %exit_code)

    #add metrics information to postgres database.


    DATABASE = {
        'drivername': 'postgres',
        'host' : args.host,
        'port' : '5432',
        'username': args.username,
        'password' : args.password,
        'database' : args.database
    }


    engine = postgres.db_connect(DATABASE)

    file_ids = [args.normal_id, args.tumor_id]

    #create metrics object
    met = Somaticsniper(case_id = args.case_id,
                    tool = 'somaticsniper',
                    files=file_ids,
                    systime=metrics['system_time'],
                    usertime=metrics['user_time'],
                    elapsed=metrics['wall_clock'],
                    cpu=metrics['percent_of_cpu'],
                    max_resident_time=metrics['maximum_resident_set_size'])

    postgres.create_table(engine, met)
    postgres.add_metrics(engine, met)
    logger.info("Added entry for case id: %s in table %s." %(met.case_id, met.__tablename__))
