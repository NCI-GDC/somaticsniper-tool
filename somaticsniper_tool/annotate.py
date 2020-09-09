#!/usr/bin/env python3

from enum import Enum


class Filter(Enum):
    LOH = """##FILTER=<ID=LOH,Description="Rejected as a loss of heterozygosity">"""
    PASS = """##FILTER=<ID=PASS,Description="Accept as a high confident somatic mutation">"""
    REJECT = """##FILTER=<ID=REJECT,Description="Rejected as an unconfident somatic mutation">"""


def annotate_filter(raw, post_filter, new):
    """Annotate post filter vcf"""
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


# __END__
