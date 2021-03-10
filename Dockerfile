FROM python:3.7-slim

MAINTAINER Charles Czysz <czysz@uchicago.edu>

ARG VERSION="1.0.5.0"

ENV URL=https://github.com/genome/somatic-sniper/archive/v${VERSION}.tar.gz

RUN apt-get update \
	&& yes | apt-get install -y \
		software-properties-common \
	        build-essential \
		gcc \
		cmake \
		make \
		zlib1g-dev \
		libncurses-dev \
		wget \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN wget $URL \
	&& tar xf v${VERSION}.tar.gz \
	&& cd somatic-sniper-${VERSION} \
	&& cmake . \
	&& make deps \
	&& make -j \
	&& make install \
	&& mv bin/* /usr/local/bin/ \
	&& mkdir -p /scripts \
	&& mv src/scripts/* /scripts \
	&& cd .. \
	&& rm -rf somatic-sniper-${VERSION} v${VERSION}.tar.gz

ENV BINARY=somaticsniper_tool

COPY dist/ /opt/

WORKDIR /opt

RUN make init-pip \
  && ln -s /opt/bin/${BINARY} /bin/${BINARY}

ENTRYPOINT ["/bin/somaticsniper_tool"]
CMD ["--help"]
