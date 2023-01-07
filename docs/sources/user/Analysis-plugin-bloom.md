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
psort.py --analysis bloom --bloom_file hashlookup-full.bloom -o null timeline.plaso
```

The last step would be to export a timeline with the tags (By default, the tag value is `bloom_present`) :

```bash
psort.py -o dynamic --dynamic-time --fields datetime,timestamp_desc,source,source_long,message,parser,data_type,display_name,tag,sha1_hash -w timeline.csv timeline.plaso
```

```bash
psort.py --analysis hashlookup_bloom --hashlookup_bloom_file hashlookup-full.bloom -o json_line -w timeline.jsonl 20221228T162736-Laptop1Final.E01.plaso
```
