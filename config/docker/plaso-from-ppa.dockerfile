FROM ubuntu:trusty
MAINTAINER Log2Timeline <log2timeline-dev@googlegroups.com>

# Create container with:
# docker build -f plaso-from-ppa.dockerfile
#
# Run log2timeline on artifacts stored in /data/artifacts with:
# docker run -ti -v /data/:/data/ <container_id> log2timeline \
#   /data/results/result.plaso /data/artifacts

RUN apt-get update
RUN apt-get -y install software-properties-common apt-transport-https
RUN add-apt-repository -y ppa:gift/stable

RUN apt-get update && apt-get -y upgrade

RUN apt-get -y install python-plaso
RUN apt-get clean &&  rm -rf /var/cache/apt/* /var/lib/apt/lists/*

# Set terminal to UTF-8 by default
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

WORKDIR /usr/local/bin
COPY "plaso-switch.sh" "plaso-switch.sh"
RUN chmod a+x plaso-switch.sh

VOLUME ["/data"]

WORKDIR /home/plaso/

ENTRYPOINT ["/usr/local/bin/plaso-switch.sh"]
