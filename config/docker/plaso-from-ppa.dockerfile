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
RUN add-apt-repository -y ppa:gift/dev

RUN apt-get update && apt-get -y upgrade

RUN apt-get -y install ipython libbde-python \
    libesedb-python libevt-python libevtx-python \
    libewf-python libfwsi-python liblnk-python \
    libmsiecf-python libolecf-python libqcow-python \
    libregf-python libsigscan-python libsmdev-python \
    libsmraw-python libtsk libvhdi-python \
    libvmdk-python libvshadow-python python-artifacts \
    python-bencode python-binplist python-construct \
    python-dateutil python-dfvfs python-dpkt \
    python-hachoir-core python-hachoir-metadata \
    python-hachoir-parser python-pefile python-protobuf \
    python-psutil python-pyparsing python-six \
    python-yaml python-tz pytsk3

RUN apt-get -y install python-plaso
RUN apt-get clean &&  rm -rf /var/cache/apt/* /var/lib/apt/lists/*

WORKDIR /usr/local/bin
COPY "plaso-switch.sh" "plaso-switch.sh"
RUN chmod a+x plaso-switch.sh

VOLUME ["/data"]

WORKDIR /home/plaso/

ENTRYPOINT ["/usr/local/bin/plaso-switch.sh"]
