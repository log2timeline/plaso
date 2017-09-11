#!/usr/bin/env bash
sh ./config/linux/gift_ppa_install.sh include-test
/usr/bin/gsutil cp gs://"$CONFIG_BUCKET"/"$JOB_NAME".ini .
#Create a directory to store results
mkdir -p /tmp/plaso_out
PYTHONPATH=. python ./tests/end-to-end.py --debug --config "$JOB_NAME".ini --sources-directory /media/greendale_images --tools-directory ./tools --results-directory /tmp/plaso_out --references-directory /media/greendale_images
/usr/bin/gsutil cp /tmp/plaso_out/* gs://"$RESULTS_BUCKET"/build_results/"$JOB_NAME"/"$BUILD_NUMBER"/
/usr/bin/gsutil ls gs://"$RESULTS_BUCKET"/build_results/"$JOB_NAME"/gold/
if [ $? -eq 0 ]; then
  /usr/bin/gsutil rm gs://"$RESULTS_BUCKET"/build_results/"$JOB_NAME"/gold/*
fi
/usr/bin/gsutil cp gs://"$RESULTS_BUCKET"/build_results/"$JOB_NAME"/"$BUILD_NUMBER"/* gs://"$RESULTS_BUCKET"/build_results/"$JOB_NAME"/gold/
rm /tmp/plaso_out/*
