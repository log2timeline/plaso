# Tips and Tricks

This is a collection of few tips and tricks that can be used with **Plaso**

## Import the output of a third party tool into Plaso

If want to import the output of a third party tool into your Plaso timeline
export it to bodyfile format. The Plaso bodyfile parser can parse a bodyfile.

Note that the bodyfile format has numerous limitations see:
[ForensicsWiki: Bodyfile](https://forensics.wiki/bodyfile)

The Plaso bodyfile parser supports timestamps with a fraction of a second since
[Aug 25, 2020](https://github.com/log2timeline/plaso/commit/c81ef3aea9817646ea2846376ce9e2a83c7d5fe5).

## Optimizing log2timeline and psteal

The options below are supported by both log2timeline.py and psteal.py, unless
indicated otherwise. Also see [performance related issues](../Troubleshooting.md#performance-related-issues).

### Number of workers and memory

By default log2timeline.py starts a worker process for every available CPU
minus one, for the main (foreman) process, with a minimum of 2. Each worker
process is allowed to consume up to 2 GiB of memory before the main process
kills it. Every process is also limited to allocating 4 GiB of memory by the
operating system.

On a system with many CPUs and relatively little memory the workers can
together consume more memory than is available. In this case reduce the number
of workers with `--workers` or the memory a worker is allowed to consume with
`--worker_memory_limit`. Note that a worker that is killed is restarted, which
adds overhead.

```bash
$ log2timeline.py --workers 4 --storage-file timeline.plaso image.raw
```

### Input IO

Every file that is processed needs to be read at least once. To reduce the
amount of data that is read:

* store the source data on local low-latency media;
* only enable the parsers you need with `--parsers`, see [parsers and plugins](Parsers-and-plugins.md);
* only process the files you need with a filter file (`--filter-file`) or artifact definitions (`--artifact_filters`), see [collection filters](Collection-Filters.md). These options are only supported by log2timeline.py;
* only process the partitions and Volume Shadow Snapshots (VSS) you need with `--partitions` and `--vss_stores`;
* do not process the content of archives, which is the default, or limit it to the archive types you need with `--archives`;
* disable hashing with `--hashers none`, by default the SHA-256 of every processed file is calculated, or skip large files with `--hasher_file_size_limit`;
* skip compressed streams, such as syslog.gz, with `--skip_compressed_streams`.

### Temporary IO

The worker processes store their results in temporary task storage files,
which are created in the same directory as the storage file. Hence store the
storage file on local low-latency media.

Some parsers, such as the SQLite parser, copy data to a temporary file. These
are stored in the directory specified with `--temporary_directory` or the
default temporary directory of the system.

### Output IO

Write the output of psort.py and psteal.py to local low-latency media.
