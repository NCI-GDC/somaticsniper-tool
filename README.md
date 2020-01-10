# GDC SomaticSniper
![Version badge](https://img.shields.io/badge/SomaticSniper-1.0.5.0-<COLOR>.svg)

The purpose of SomaticSniper is to identify single nucleotide positions that are different between tumor and normal. It takes a tumor bam and a normal bam and compares the two to determine the differences.

Original SomaticSniper: http://gmt.genome.wustl.edu/packages/somatic-sniper/index.html

## Docker

There are three `Dockerfile`s for different purposes:

* Vanilla BAM-readcount
  * `/docker/bam-readcount/Dockerfile` : BAM-readcount docker without additional features. The `bam-readcount` will be used for the fpfilter.
* Vanilla SomaticSniper
  * `/docker/somaticsniper/Dockerfile` : SomaticSniper docker without additional features.
* Multi-threading SomaticSniper
  * `/docker/multi_muse/Dockerfile` : A python multi-threading implementation on SomaticSniper with builtin `LOH` and `High confidence` filtering. To achieve `scatter/gather` method on Docker level, input needs an array of tumor-normal mpileup from `samtools mpileup -f`.

## How to build

https://docs.docker.com/engine/reference/builder/

The docker images are tested under multiple environments. The most tested ones are:
* Docker version 19.03.2, build 6a30dfc
* Docker version 18.09.1, build 4c52b90
* Docker version 18.03.0-ce, build 0520e24
* Docker version 17.12.1-ce, build 7390fc6

## For external users

There is a production-ready CWL example at https://github.com/NCI-GDC/somaticsniper-cwl which uses the docker images that are built from the `Dockerfile`s in this repo.

To use docker images directly or with other workflow languages, we recommend to build and use either vanilla SomaticSniper or multi-threading SomaticSniper.

To run multi-threading SomaticSniper:

```
[INFO] [20200110 04:32:14] [multi_somaticsniper] - --------------------------------------------------------------------------------
usage: Internal multithreading SomaticSniper calling. [-h] -f REFERENCE_PATH
                                                      -t TUMOR_BAM -n
                                                      NORMAL_BAM -c
                                                      THREAD_COUNT -m MPILEUP
                                                      [-q MAP_Q] [-Q BASE_Q]
                                                      [-L] [-G] [-p] [-J]
                                                      [-s PPS] [-T THETA]
                                                      [-N NHAP] [-r PD]
                                                      [-F FOUT]

optional arguments:
  -h, --help            show this help message and exit
  -f REFERENCE_PATH, --reference_path REFERENCE_PATH
                        Reference path.
  -t TUMOR_BAM, --tumor_bam TUMOR_BAM
                        Tumor bam file.
  -n NORMAL_BAM, --normal_bam NORMAL_BAM
                        Normal bam file.
  -c THREAD_COUNT, --thread_count THREAD_COUNT
                        Number of thread.
  -m MPILEUP, --mpileup MPILEUP
                        A list of normal-tumor samtools mpileup files on
                        different region. Created by "samtools mpileup -f".
                        The file name must contain region. e.g.
                        chr1-1-248956422.mpileup
  -q MAP_Q, --map_q MAP_Q
                        filtering reads with mapping quality less than this
                        value.
  -Q BASE_Q, --base_q BASE_Q
                        filtering somatic snv output with somatic quality less
                        than this value.
  -L, --loh             do not report LOH variants as determined by genotypes
                        (T/F).
  -G, --gor             do not report Gain of Reference variants as determined
                        by genotypes (T/F).
  -p, --psc             disable priors in the somatic calculation. Increases
                        sensitivity for solid tumors (T/F).
  -J, --ppa             Use prior probabilities accounting for the somatic
                        mutation rate (T/F).
  -s PPS, --pps PPS     prior probability of a somatic mutation (implies -J).
  -T THETA, --theta THETA
                        theta in maq consensus calling model (for -c/-g).
  -N NHAP, --nhap NHAP  number of haplotypes in the sample.
  -r PD, --pd PD        prior of a difference between two haplotypes.
  -F FOUT, --fout FOUT  output format (classic/vcf/bed).
```

## For GDC users

See https://github.com/NCI-GDC/gdc-somatic-variant-calling-workflow.
