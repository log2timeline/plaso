FROM ubuntu:latest
MAINTAINER Romain Gayon <romaing@google.com>

# Create container with :
# docker build -f plaso-from-ppa.dockerfile .
#
# Run log2timeline on artifacts stored in /data/artifacts
# with :
# docker run -ti -v /data/:/data/ <containers_id> log2timeline \
#   /data/results/result.plaso /data/artifacts

RUN apt-get -y install software-properties-common apt-transport-https
RUN add-apt-repository -y ppa:gift/stable

RUN apt-get update && apt-get -y upgrade


RUN apt-get -y install python-plaso
RUN apt-get clean &&  rm -rf /var/cache/apt/* /var/lib/apt/lists/*

WORKDIR /usr/local/bin
COPY "plaso-switch.sh" "plaso-switch.sh"
RUN chmod a+x plaso-switch.sh

VOLUME ["/data"]

WORKDIR /home/plaso/

ENTRYPOINT ["/usr/local/bin/plaso-switch.sh"]
