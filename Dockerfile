FROM quay.io/ncigdc/somatic-sniper:1.0.5.0 AS sniper
FROM quay.io/ncigdc/samtools:1.1 AS samtools

MAINTAINER Charles Czysz <czysz@uchicago.edu>

FROM python:3.7-slim

COPY --from=sniper / /
COPY --from=samtools / /

ENV BINARY=somaticsniper_tool

RUN apt-get update \
  && apt-get install -y \
  	make \
  && apt-get clean autoclean \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*

COPY dist/ /opt/

WORKDIR /opt

RUN make init-pip \
  && ln -s /opt/bin/${BINARY} /bin/${BINARY}

ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--", "somaticsniper_tool"]

CMD ["--help"]
