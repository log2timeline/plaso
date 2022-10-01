FROM fedora:36
MAINTAINER Log2Timeline <log2timeline-dev@googlegroups.com>

# Create container with:
# docker build --no-cache --build-arg PPA_TRACK="[dev|stable]" \
#   --force-rm -t log2timeline/plaso .
#
# Run log2timeline on artifacts stored in /data/artifacts with:
# docker run -ti -v /data/:/data/ <container_id> log2timeline \
#   /data/results/result.plaso /data/artifacts

ARG PPA_TRACK=staging

RUN dnf -y install dnf-plugins-core
RUN dnf -y copr enable @gift/$PPA_TRACK

RUN dnf -y update

RUN dnf install -y plaso-tools
