FROM ubuntu:jammy
MAINTAINER Log2Timeline <log2timeline-dev@go

ENV DEBIAN_FRONTEND=noninteractive

# Combining the apt-get commands into a single run reduces the size of the resulting image.
# The apt-get installations below are interdependent and need to be done in sequence.
RUN apt-get -y update && \
    apt-get -y install apt-transport-https apt-utils && \
    apt-get -y install libterm-readline-gnu-perl software-properties-common && \
    apt-get -y install locales

# Set terminal to UTF-8 by default.
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Install nsrlsvr.
RUN add-apt-repository ppa:gift/dev -y && \
    apt-get update -q && \
    apt-get install -y nsrlsvr-server

# Initialize nsrlsvr hashes.txt file.
RUN mkdir -p /var/share/nsrlsvr && \
    mkdir -p /usr/share/nsrlsvr && \
    touch /usr/share/nsrlsvr/hashes.txt

WORKDIR /home/test/

# Clean up apt-get cache files.
RUN apt-get clean && rm -rf /var/cache/apt/* /var/lib/apt/lists/*
