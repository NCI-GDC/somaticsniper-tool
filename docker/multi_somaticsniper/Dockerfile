FROM ubuntu:16.04
LABEL maintainer="sli6@uchicago.edu"
LABEL version="1.4"
LABEL description="Python wrapper of multithreading `SomaticSniper` v1.0.5.0"

RUN apt-get update -y \
    && apt-get install -y \
    python-dev \
    build-essential \
    cmake \
    zlib1g-dev \
    libncurses-dev \
    wget \
    bzip2 \
    gcc \
    make \
    libbz2-dev \
    liblzma-dev \
    && apt-get clean

RUN cd /opt/ \
    && wget https://github.com/genome/somatic-sniper/archive/v1.0.5.0.tar.gz \
    && tar xvzf v1.0.5.0.tar.gz \
    && rm v1.0.5.0.tar.gz \
    && cd /opt/somatic-sniper-1.0.5.0 \
    && cmake . \
    && make deps \
    && make -j \
    && make install \
    && cd /opt/ \
    && wget http://sourceforge.net/projects/samtools/files/samtools/1.1/samtools-1.1.tar.bz2 \
    && tar xf samtools-1.1.tar.bz2 \
    && cd /opt/samtools-1.1 \
    && make \
    && make install \
    && cd - \
    && rm -rf /opt/samtools-1.1

ADD multi_somaticsniper.py /opt
