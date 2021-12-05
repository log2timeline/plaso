# Unique domains visited analysis plugin

Notes on how to use the unique_domains_visited analysis plugin.

## Running the analysis plugin

First run log2timeline to extract events:

```bash
log2timeline.py --storage-file timeline.plaso image.raw
```

Note that the unique domains visited analysis plugin analyzes URLS in web
history data such as events with data type:

* chrome:history:file_downloaded
* chrome:history:page_visited
* firefox:downloads:download
* firefox:places:page_visited
* macosx:lsquarantine
* msiecf:redirected
* msiecf:url
* msie:webcache:container
* opera:history
* safari:history:visit

Next run psort to determine the unique domains visited:

```bash
psort.py --analysis unique_domains_visited -o null timeline.plaso
```

This will extract information of unique domains which will be stored in
the analysis report.
