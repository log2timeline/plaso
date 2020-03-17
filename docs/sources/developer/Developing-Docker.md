# Developing in a Docker Container

For development purposes, Plaso can be installed using Docker.

**Note that this is intended for development use only and is a quite "hacky" solution.**

## Preparation

```
mkdir plaso-dev
git clone git@github.com:log2timeline/plaso.git
cat > Dockerfile << EOF
FROM ubuntu:18.04

RUN apt-get update && \
        apt-get install -y software-properties-common git && \
        add-apt-repository universe && \
        apt-get update

RUN git clone https://github.com/log2timeline/plaso.git /plaso

WORKDIR /plaso

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true

RUN echo "tzdata tzdata/Areas select Europe" > /tmp/preseed.txt; \
        echo "tzdata tzdata/Zones/Europe select Berlin" >> /tmp/preseed.txt; \
        debconf-set-selections /tmp/preseed.txt && \
        sed -i 's/sudo//g' ./config/linux/gift_ppa_install_py3.sh && \
        bash ./config/linux/gift_ppa_install_py3.sh include-development include-test include-debug && \
        python3 setup.py install && \
        rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

VOLUME /plaso

CMD python3 setup.py install && /bin/bash
EOF
```

## Build the Docker Image

```
docker build -t plaso-dev .
```

## Run the Docker Image

By default the Docker image will install the current Plaso version in `/plaso` and then start a bash. However, this only makes sense if you mounted your development directory to the container:

```
docker run --rm -ti -v $(pwd)/plaso:/plaso plaso-dev
```

If you want to directly execute a tool such as `psteal.py` you can do the following:

```
docker run --rm -ti -v $(pwd)/plaso:/plaso plaso-dev bash -c "python3 setup.py install && python3 tools/psteal.py --status-view linear -o l2tcsv -w output.csv --source /plaso/test_data/System2.evtx"
```
