FROM ubuntu:focal
MAINTAINER Log2Timeline <log2timeline-dev@googlegroups.com>

# Create container with:
# docker build --no-cache --build-arg PPA_TRACK="[dev|stable]" \
#   --force-rm -t log2timeline/plaso .
#
# Run log2timeline on artifacts stored in /data/artifacts with:
# docker run -ti -v /data/:/data/ <container_id> log2timeline \
#   /data/results/result.plaso /data/artifacts

ARG PPA_TRACK=stable

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update
RUN apt-get -y install apt-transport-https apt-utils
RUN apt-get -y install libterm-readline-gnu-perl software-properties-common
RUN add-apt-repository -y ppa:gift/$PPA_TRACK

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get -y install locales plaso-tools

# Clean up apt-get cache files
RUN apt-get clean && rm -rf /var/cache/apt/* /var/lib/apt/lists/*

# Set terminal to UTF-8 by default
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
