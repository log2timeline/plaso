FROM ubuntu:latest
MAINTAINER Romain Gayon <romaing@google.com>

# Let's start with a clean, up to date Ubuntu
RUN apt-get -y install software-properties-common
RUN apt-get update && apt-get -y upgrade

# Get rid of Python encoding errors
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN apt-get -y install git python2.7 python-setuptools


RUN apt-get -y install  ipython \
			python-dateutil \
			python-hachoir-core \
			python-hachoir-metadata \
			python-hachoir-parser \
			python-protobuf \
			python-requests \
			python-six \
			python-yaml

# for artifacts
RUN apt-get -y install libyaml-dev

# libewf needs that
RUN apt-get -y install bison flex
#
# To build libyal/liblnk
RUN apt-get -y install autoconf automake autopoint build-essential libtool pkg-config python-dev

# These libs should have the versions we need, so let's install them with pip
RUN apt-get -y install python-pip
RUN pip install bencode \
		binplist \
		construct \
		dpkt \
		psutil \
		pyparsing \
		pytz \
		xlsxwriter \
		zmq
# Pefile won't install the required version if we don't specify the
# index URL to use
RUN pip install -i https://pypi.python.org/pypi/ pefile==1.2.10-139

# Required packages to build tsk
RUN apt-get -y install zlib1g-dev

# Required packages to build pytsk
Run apt-get -y install libtalloc-dev

# Extra package for running plaso tests
RUN apt-get -y install python-mock

########
# These are pulled and built from source

WORKDIR /home/plaso/ForensicArtifacts/
RUN git clone https://github.com/ForensicArtifacts/artifacts.git
WORKDIR /home/plaso/ForensicArtifacts/artifacts
RUN python setup.py install

WORKDIR /home/plaso/sleuthkit
RUN git clone https://github.com/sleuthkit/sleuthkit.git
WORKDIR /home/plaso/sleuthkit/sleuthkit
RUN ./bootstrap && ./configure && make && make install

WORKDIR /home/plaso/py4n6/
RUN git clone https://github.com/py4n6/pytsk.git
WORKDIR /home/plaso/py4n6/pytsk
RUN python setup.py install

# First, cloning every required lib
WORKDIR /home/plaso/libyal
RUN git clone https://github.com/libyal/libbde.git
RUN git clone https://github.com/libyal/libesedb.git
RUN git clone https://github.com/libyal/libevt.git
RUN git clone https://github.com/libyal/libevtx.git
RUN git clone https://github.com/libyal/libewf.git
RUN git clone https://github.com/libyal/libfwsi.git
RUN git clone https://github.com/libyal/libfsntfs.git
RUN git clone https://github.com/libyal/liblnk.git
RUN git clone https://github.com/libyal/libmsiecf.git
RUN git clone https://github.com/libyal/libolecf.git
RUN git clone https://github.com/libyal/libqcow.git
RUN git clone https://github.com/libyal/libregf.git
RUN git clone https://github.com/libyal/libsigscan.git
RUN git clone https://github.com/libyal/libsmdev.git
RUN git clone https://github.com/libyal/libsmraw.git
RUN git clone https://github.com/libyal/libvhdi.git
RUN git clone https://github.com/libyal/libvmdk.git
RUN git clone https://github.com/libyal/libvshadow.git

# Do the building !
WORKDIR /home/plaso/libyal/libbde
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libesedb
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libevt
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libevtx
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libewf
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python && make && make install

WORKDIR /home/plaso/libyal/libfwsi
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/liblnk
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python && make && make install

WORKDIR /home/plaso/libyal/libfsntfs
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python && make && make install
# HAX
RUN cp /home/plaso/libyal/liblnk/setup.py .
RUN python setup.py install

WORKDIR /home/plaso/libyal/libmsiecf
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libolecf
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libqcow
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python && make && make install

WORKDIR /home/plaso/libyal/libregf
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libsigscan
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libsmdev
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python && make && make install

WORKDIR /home/plaso/libyal/libsmraw
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python && make && make install

WORKDIR /home/plaso/libyal/libvhdi
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python
RUN python setup.py install

WORKDIR /home/plaso/libyal/libvmdk
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python && make && make install

WORKDIR /home/plaso/libyal/libvshadow
RUN ./synclibs.sh && ./autogen.sh && ./configure --enable-python && make && make install

WORKDIR /home/plaso/log2timeline
RUN git clone https://github.com/log2timeline/dfvfs.git
RUN git clone https://github.com/log2timeline/plaso.git

WORKDIR /home/plaso/log2timeline/dfvfs
RUN export PYTHONIOENCODING=UTF-8 ; python setup.py install

RUN /sbin/ldconfig -v

WORKDIR /home/plaso/log2timeline/plaso
RUN export PYTHONIOENCODING=UTF-8 && python setup.py install

WORKDIR /usr/local/bin
COPY "plaso-switch.sh" "plaso-switch.sh"
RUN chmod a+x plaso-switch.sh

# These volumes are here to share input data and output
# results with the host system
VOLUME ["/data/artefacts","/data/results"]

ENTRYPOINT ["/usr/local/bin/plaso-switch.sh"]
