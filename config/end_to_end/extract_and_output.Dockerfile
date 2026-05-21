FROM ubuntu:resolute
MAINTAINER Log2Timeline <log2timeline-dev@googlegroups.com>

ARG GIT_REPOSITORY=https://github.com/log2timeline/plaso.git

ENV DEBIAN_FRONTEND=noninteractive

# Combining the apt commands into a single run reduces the size of the resulting image.
# The apt installations below are interdependent and need to be done in sequence.
RUN apt -y update && \
    apt -y install apt-transport-https apt-utils && \
    apt -y install libterm-readline-gnu-perl software-properties-common && \
    apt -y install locales git sudo

# Set terminal to UTF-8 by default.
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Download the Plaso source.
WORKDIR /home/test/
RUN git clone $GIT_REPOSITORY

# Install Plaso dependencies.
WORKDIR /home/test/plaso

# Install Plaso and dependencies.
RUN ./config/linux/ubuntu_install_plaso.sh

# Configure container for running Plaso.
ENV PYTHONPATH=/home/test/plaso

# Clean up apt cache files.
RUN apt clean && rm -rf /var/cache/apt/* /var/lib/apt/lists/*
