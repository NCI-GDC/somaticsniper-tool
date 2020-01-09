FROM ubuntu:16.04
LABEL maintainer="sli6@uchicago.edu"
LABEL version="0.8.0"
LABEL description="Count DNA sequence reads in BAM files"

RUN apt-get update -y \
    && apt-get install -y \
    build-essential \
    git-core \
    cmake \
    zlib1g-dev \
    libncurses-dev \
    patch \
    && apt-get clean

RUN cd /opt/ \
    && git clone https://github.com/genome/bam-readcount.git \
    && cd /opt/bam-readcount/ \
    && cmake . \
    && make -j \
    && make install \
    && cd - \
    && rm -rf /opt/bam-readcount/
