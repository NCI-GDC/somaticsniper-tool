FROM ubuntu:16.04
LABEL maintainer="sli6@uchicago.edu"
LABEL version="1.0.5.0"
LABEL description="SomaticSniper v1.0.5.0"

RUN apt-get update -y \
    && apt-get install -y \
    build-essential \
    cmake \
    zlib1g-dev \
    libncurses-dev \
    wget \
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
    && cd - \
    && rm -rf /opt/somatic-sniper-1.0.5.0