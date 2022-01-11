# Chrome extension analysis plugin

Notes on how to use the chrome_extension analysis plugin.

## Running the analysis plugin

First run log2timeline to extract events:

```bash
log2timeline.py --storage-file timeline.plaso image.raw
```

Note that the Chrome extension analysis plugin analyzes
file system data such as events with data type:

* fs:stat

Next run psort to determine Chrome extensions:

```bash
psort.py --analysis chrome_extension -o null timeline.plaso
```

This will extract information of Chrome extensions, such as name and identifier
of the extension and corresponding username. The analysis results can be
reviewed with pinfo:

```bash
pinfo.py --report chrome_extension timeline.plaso
```
