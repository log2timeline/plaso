# Virustotal analysis plugin

Notes on how to use the virustotal analysis plugin.

## Getting an API key

The virustotal analysis plugin uses the public Virustotal API, and requires an
API key to operate. The process for obtaining an API key is [here](https://developers.virustotal.com/reference#getting-started).

## Running the analysis plugin

First run log2timeline to hash files and extract events:

```bash
log2timeline.py --storage-file timeline.plaso image.raw
```

Note that hashing must be turned on for the virustotal plugin to work
correctly. This is default setting for log2timeline.py.

Next run psort to tag events:

```bash
psort.py --analysis virustotal --virustotal-api-key $API_KEY -o null timeline.plaso
```

If a file processed by Plaso is present in virustotal and has been detected as
malicious by one more detection engines, it will be tagged with
`virustotal_detections_$NUMBER_OF_DETECTIONS`. If the file is in Virustotal,
but it hasn't been fully analyzed yet, it will be tagged with
`virustotal_analysis_pending`. If the file is in Virustotal, but has not been
detected as malicious, it will be tagged with `virustotal_no_detections`. If
the file isn't in Virustotal, it will be tagged as `virustotal_not_present`.

The last step would be to export a timeline with the tags:

```bash
psort.py -o dynamic --fields datetime,timestamp_desc,source,source_long,message,parser,tag -w timeline.csv timeline.plaso
```
