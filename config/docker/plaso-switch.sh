#!/bin/bash
#
# Since Docker run can only have one "entry point" this script enables calling
# either log2timeline or other utility scripts e.g.
# docker run <container_id> image_export
# docker run <container_id> log2timeline
# docker run <container_id> pinfo
# docker run <container_id> psort
# docker run <container_id> psteal
#
# or to run it on actual data:
# mkdir -p /data/sources    # put the files to parse here
# mkdir -p /data/results    # a Plaso storage file will appear here
# docker run -v /data/:/data <container_id> log2timeline \
#     /data/results/result.plaso /data/sources

case "$1" in
  image_export|image_export.py)
    /usr/bin/image_export.py --unattended "${@:2}" ;;
  log2timeline|log2timeline.py)
    /usr/bin/log2timeline.py --unattended "${@:2}" ;;
  pinfo|pinfo.py)
    /usr/bin/pinfo.py "${@:2}" ;;
  psort|psort.py)
    /usr/bin/psort.py --unattended "${@:2}" ;;
  psteal|psteal.py)
    /usr/bin/psteal.py --unattended "${@:2}" ;;
  "")
    /usr/bin/log2timeline.py --unattended "${@:2}" ;;
  *)
    echo "Unsupported command: $1"
esac
