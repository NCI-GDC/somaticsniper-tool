FROM ubuntu:14.04
MAINTAINER Stuti Agrawal <stutia@uchicago.edu>
USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --force-yes \
    curl \
    g++ \
    make \
    python \
    libboost-dev \
    libboost-thread-dev \
    libboost-system-dev \
    zlib1g-dev \
    ncurses-dev \
    unzip \
    gzip \
    bzip2 \
    libxml2-dev \
    libxslt-dev \
    python-pip \
    python-dev \
    python-numpy \
    python-matplotlib \
    git \
    s3cmd \
    time \
    wget \
    python-virtualenv \
    default-jre \
    default-jdk \ 
    build-essential \ 
    cmake \
    libncurses-dev

RUN adduser --disabled-password --gecos '' ubuntu && adduser ubuntu sudo && echo "ubuntu    ALL=(ALL)   NOPASSWD:ALL" >> /etc/sudoers.d/ubuntu
ENV HOME /home/ubuntu

USER ubuntu
RUN mkdir ${HOME}/bin
WORKDIR ${HOME}/bin
ADD somaticsniper-tool ${HOME}/bin/somaticsniper-tool/

RUN pip install pysam --user

#download SOMATIC-SNIPER
RUN wget https://github.com/genome/somatic-sniper/archive/v1.0.5.0.tar.gz && tar xvzf v1.0.5.0.tar.gz && rm v1.0.5.0.tar.gz
USER root
RUN cd  somatic-sniper-1.0.5.0 && mkdir build && cd build && cmake ../ && make deps && make -j && make install
RUN cp  somatic-sniper-1.0.5.0/build/vendor/samtools/samtools /usr/bin/

USER ubuntu

ENV PATH ${PATH}:${HOME}/bin/

RUN pip install s3cmd --user
WORKDIR ${HOME}

ENV somaticsniper 0.1

USER ubuntu
WORKDIR ${HOME}

