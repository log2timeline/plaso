# Hashlookup Bloom Analysis Plugin

Notes on how to use the `hashlookup-bloom` analysis plugin.

## Prerequisite

The only prerequisite to use this plugin is to download or generate a reference Bloom database.

[CIRCL.lu](https://circl.lu) kindly offer such a database, known as a *Bloom Filter*, which is a compact representation of the dataset. It is generated from the hashes known in their [Hashlookup](https://circl.lu/services/hashlookup/) instance. The *Bloom filter* can be downloaded [here](https://cra.circl.lu/hashlookup/hashlookup-full.bloom)

Details are available [here](https://circl.lu/services/hashlookup/#querying-hashlookup-without-online-queries).

## Running the analysis plugin

First run `log2timeline` to calculate the hashes:

```bash
log2timeline.py --hashers sha1 --storage-file timeline.plaso image.raw
```

**Make sure to enable hashers supported by the Bloom Filter, which is sha1 in this example.**

Next run `psort` to tag events:
 

```bash
psort.py --analysis hashlookup_bloom --hashlookup_bloom_file hashlookup-full.bloom -o null timeline.plaso
```

The last step would be to export a timeline with the tags (By default, the tag value is `hashlookup_present`) :

```bash
psort.py -o dynamic --dynamic-time --fields datetime,timestamp_desc,source,source_long,message,parser,data_type,display_name,tag,sha1_hash -w timeline.csv timeline.plaso
```


./psort.py --analysis hashlookup_bloom --hashlookup_bloom_file hashlookup-full.bloom -o json_line -w timeline.jsonl 20221228T162736-Laptop1Final.E01.plaso 