# Sessionize analysis plugin

Notes on how to use the sessionize analysis plugin.

## Running the analysis plugin

First run log2timeline to extract events:

```bash
log2timeline.py --storage-file timeline.plaso image.raw
```

Next run psort to determine sessions:

```bash
psort.py --analysis sessionize -o null timeline.plaso
```

This will tag events with a `session_N` label to indicate which session they
belong to, where N starts at 0. A new session starts when the time between
consecutive events is larger than the maximum pause. Use `--maximum-pause` to
set the maximum pause in minutes, the default is 10.

The last step would be to export a timeline with the tags:

```bash
psort.py -o dynamic --fields datetime,timestamp_desc,source,source_long,message,parser,tag -w timeline.csv timeline.plaso
```
