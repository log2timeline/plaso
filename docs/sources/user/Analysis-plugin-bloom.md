# Bloom Analysis Plugin

Notes on how to use the bloom analysis plugin.

## Prerequisite

A prerequisite to use this plugin is to have a bloom-filter database with information about hashes.

The bloom plugin uses a specific bloom-filter implementation known to be compatible with the following implementations:

* Golang: https://github.com/DCSO/bloom
* Python: https://github.com/DCSO/flor

These implementation could be used to generate a custom bloom-filter files. It is important to note that the hashes **must** be inserted in upper case.

Furthermore, bloom-filters are a probabilistic storage format. In the case of bloom, this means that:

* No false negative could occur;
* False positives can occur with a predetermined probability, defined when creating the bloom-filter file.

A bloom-filter database is available on the CIRCL.lu website: https://circl.lu/services/hashlookup/#querying-hashlookup-without-online-queries

## Running the analysis plugin

First run `log2timeline` to calculate the hashes:

```bash
log2timeline.py --hashers sha1 --storage-file timeline.plaso image.raw
```

**Make sure to enable hashers supported by the Bloom Filter, which is sha1 in this example.**

Next run `psort` to tag events:

```bash
psort.py --analysis bloom --bloom-file hashlookup-full.bloom -o null timeline.plaso
```

The bloom analysis plugin supports the following options:

* `--bloom-file`: path of the bloom database file, the default is `hashlookup-full.bloom`;
* `--bloom-hash`: type of hash to look up, which can be `md5`, `sha1` or `sha256`, the default is `sha1`;
* `--bloom-label`: label to apply to events, the default is `bloom_present`.

The last step would be to export a timeline with the tags (By default, the tag value is `bloom_present`) :

```bash
psort.py -o dynamic --dynamic-time --fields datetime,timestamp_desc,source,source_long,message,parser,data_type,display_name,tag,sha1_hash -w timeline.csv timeline.plaso
```

Or to tag events and export them as JSON lines in a single run:

```bash
psort.py --analysis bloom --bloom-file hashlookup-full.bloom -o json_line -w timeline.jsonl timeline.plaso
```
