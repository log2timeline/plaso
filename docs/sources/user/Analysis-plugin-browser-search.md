# Browser search analysis plugin

Notes on how to use the browser_search analysis plugin.

## Running the analysis plugin

First run log2timeline to extract events:

```bash
log2timeline.py --storage-file timeline.plaso image.raw
```

Note that the browser search analysis plugin analyzes URLS in web history data
such as events with data type:

* chrome:autofill:entry
* chrome:cache:entry
* chrome:cookie:entry
* chrome:extension_activity:activity_log
* chrome:history:file_downloaded
* chrome:history:page_visited
* cookie:google:analytics:utma
* cookie:google:analytics:utmb
* cookie:google:analytics:utmt
* cookie:google:analytics:utmz
* firefox:cache:record
* firefox:cookie:entry
* firefox:downloads:download
* firefox:places:bookmark
* firefox:places:bookmark_annotation
* firefox:places:bookmark_folder
* firefox:places:page_visited
* msiecf:leak
* msiecf:redirected
* msiecf:url
* msie:webcache:container
* msie:webcache:containers
* msie:webcache:leak_file
* msie:webcache:partitions
* opera:history:entry
* opera:history:typed_entry
* safari:cookie:entry
* safari:history:visit
* safari:history:visit_sqlite

Next run psort to determine the browser searches:

```bash
psort.py --analysis browser_search -o null timeline.plaso
```

This will:

* extract information of searches performed in a browser, such as search engine, search term and number of queries
* tag corresponding events with the `browser_search` label

The analysis results can be reviewed with pinfo:

```bash
pinfo.py --report browser_search timeline.plaso
```
