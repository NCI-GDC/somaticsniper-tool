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
    
    
RUN apt-get build-dep -y --force-yes python-psycopg2

RUN adduser --disabled-password --gecos '' ubuntu && adduser ubuntu sudo && echo "ubuntu    ALL=(ALL)   NOPASSWD:ALL" >> /etc/sudoers.d/ubuntu
ENV HOME /home/ubuntu

USER ubuntu
RUN mkdir ${HOME}/bin
WORKDIR ${HOME}/bin
ADD somaticsniper-tool ${HOME}/bin/somaticsniper-tool/
ADD setup.* ${HOME}/bin/somaticsniper-tool/
ADD requirements.txt ${HOME}/bin/somaticsniper-tool/

#download SOMATIC-SNIPER
RUN wget https://github.com/genome/somatic-sniper/archive/v1.0.5.0.tar.gz && tar xvzf v1.0.5.0.tar.gz && rm v1.0.5.0.tar.gz

USER root
RUN pip install pysam
RUN cd  somatic-sniper-1.0.5.0 && mkdir build && cd build && cmake ../ && make deps && make -j && make install
RUN cp  somatic-sniper-1.0.5.0/build/vendor/samtools/samtools /usr/bin/
RUN chown -R ubuntu:ubuntu ${HOME}/bin/somaticsniper-tool

#install dependencies for postgres
#RUN pip install psycopg2
#RUN pip install SQLAlchemy

USER ubuntu

ENV PATH ${PATH}:${HOME}/bin/

RUN pip install s3cmd --user
WORKDIR ${HOME}

ENV somaticsniper 0.1

RUN pip install --user virtualenvwrapper \
    && /bin/bash -c "source ${HOME}/.local/bin/virtualenvwrapper.sh \
    && mkvirtualenv --python=/usr/bin/python3 p3 \
    && echo source ${HOME}/.local/bin/virtualenvwrapper.sh >> ${HOME}/.bashrc \
    && echo source ${HOME}/.virtualenvs/p3/bin/activate >> ${HOME}/.bashrc \
    && source ~/.virtualenvs/p3/bin/activate \
    && cd ~/bin/somaticsniper-tool \
    && pip install -r ./requirements.txt" 


USER ubuntu
WORKDIR ${HOME}

