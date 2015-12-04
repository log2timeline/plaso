#!/bin/bash

# Since docker run can only have one "entry point"
# this script enables calling either log2timeline, or
# other utility scripts
# Ex: 
# docker run <container_id> log2timeline
# docker run <container_id> psort
# docker run <container_id> pinfo
# docker run <container_id> preg
# docker run <container_id> preg
# 
# or, if one wants to run it on actual data:
# mkdir -p /data/artifacts  # put your artifacts to parse here
# mkdir -p /data/results    # plaso dump will appear hear
# docker run -v /data/:/data <containers_id> log2timeline \
#     /data/results/result.plaso /data/artifacts

case "$1" in
  log2timeline|log2timeline.py)
    /usr/bin/log2timeline.py "${@:2}" ;;
  psort|psort.py)
    /usr/bin/psort.py "${@:2}" ;;
  pinfo|pinfo.py)
    /usr/bin/pinfo.py "${@:2}" ;;
  preg|preg.py)
    /usr/bin/preg.py "${@:2}" ;;
  image_export|image_export.py)
    /usr/bin/image_export.py "${@:2}" ;;
  "")
    /usr/bin/log2timeline.py "${@:2}" ;;
  *)
    echo "Unknown command : $1"
esac
