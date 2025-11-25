FROM ubuntu:noble

# Create container with:
# docker build --build-arg PPA_TRACK="[dev|staging|stable]" \
#   --force-rm --no-cache -t log2timeline/plaso .
#
# Run log2timeline on files stored in /data/sources with:
# docker run -ti -v /data:/data:z log2timeline/plaso:latest \
#   log2timeline --storage-file=/data/results/result.plaso /data/sources

ARG PPA_TRACK=stable

ENV DEBIAN_FRONTEND=noninteractive

# Combining the apt-get commands into a single run reduces the size of the resulting image.
# The apt-get installations below are interdependent and need to be done in sequence.
RUN apt-get -y update && \
    apt-get -y install \
        apt-transport-https \
        apt-utils && \
    apt-get -y install \
        libterm-readline-gnu-perl \
        software-properties-common && \
    add-apt-repository -y ppa:gift/$PPA_TRACK && \
    apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install \
        locales \
        plaso-tools && \
    apt-get clean && rm -rf /var/cache/apt/* /var/lib/apt/lists/*

# Set terminal to UTF-8 by default
RUN locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

WORKDIR /usr/local/bin

COPY --chmod=a+x plaso-switch.sh plaso-switch.sh

VOLUME ["/data"]

WORKDIR /home/ubuntu

USER ubuntu

ENTRYPOINT ["/usr/local/bin/plaso-switch.sh"]
