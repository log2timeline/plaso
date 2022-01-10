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

This will tag with a label to indicate which session they belong to.

The last step would be to export a timeline with the tags:

```bash
psort.py -o dynamic --fields datetime,timestamp_desc,source,source_long,message,parser,tag -w timeline.csv timeline.plaso
```
