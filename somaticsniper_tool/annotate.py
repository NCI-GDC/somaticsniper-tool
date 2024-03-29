#!/usr/bin/env python3

import csv
from enum import Enum
from types import SimpleNamespace

DI = SimpleNamespace(csv=csv, open=open)


class Filter(Enum):
    LOH = """##FILTER=<ID=LOH,Description="Rejected as a loss of heterozygosity">"""
    PASS = """##FILTER=<ID=PASS,Description="Accept as a high confident somatic mutation">"""
    REJECT = """##FILTER=<ID=REJECT,Description="Rejected as an unconfident somatic mutation">"""


class Annotate:
    def __init__(self, output_file: str, _di=DI):
        self.output_file = output_file
        self._di = _di

        self.output_fh = None

    def __call__(self, *args, **kwargs):
        return self.annotate(*args, **kwargs)

    def __enter__(self):
        self.output_fh = self._di.open(self.output_file, 'w')
        return self

    def __exit__(self, type, value, traceback):
        self.output_fh.close()

    def annotate(self, raw_vcf: str, post_filter: str, _di=DI):
        """Annotate somaticsniper VCF with high confident calls.
        Accepts:
            raw_vcf (str): Path to somatic sniper VCF
            post_filter (str): Path to high confidence file
        """
        with _di.open(post_filter, 'r') as post_fh:
            high_confident_lines = post_fh.readlines()

        with _di.open(raw_vcf, 'r') as vcf_fh:
            for line in vcf_fh:
                if line.startswith("##reference"):
                    self.output_fh.write(line)
                    self.output_fh.write("{}\n".format(Filter.PASS.value))
                    self.output_fh.write("{}\n".format(Filter.REJECT.value))
                    self.output_fh.write("{}\n".format(Filter.LOH.value))
                elif line.startswith("#"):
                    self.output_fh.write(line)
                elif line in high_confident_lines:
                    entries = line.split("\t")
                    entries[6] = "LOH"
                    self.output_fh.write('\t'.join(entries))
                else:
                    entries = line.split("\t")
                    entries[6] = "REJECT"
                    self.output_fh.write("\t".join(entries))


# __END__
