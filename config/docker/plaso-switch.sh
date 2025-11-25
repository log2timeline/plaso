#!/bin/bash
#
# Since Docker run can only have one "entry point" this script enables calling
# either log2timeline or other utility scripts e.g.
# docker run log2timeline/plaso:latest image_export
# docker run log2timeline/plaso:latest log2timeline
# docker run log2timeline/plaso:latest pinfo
# docker run log2timeline/plaso:latest psort
# docker run log2timeline/plaso:latest psteal
#
# or to run it on actual data:
# mkdir -p /data/sources    # put the files to parse here
# mkdir -p /data/results    # a Plaso storage file will appear here
# docker run -ti -v /data:/data:z log2timeline/plaso:latest \
#     log2timeline --storage-file=/data/results/result.plaso /data/sources

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
