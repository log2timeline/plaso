# Creating a timeline

## Using psteal

The quickest way to generate a timeline with Plaso is using the "psteal"
frontend. For example:

```
psteal.py --source image.raw -o dynamic -w registrar.csv
```

This will produce a CSV file containing all the events from an image, with some
sensible defaults.

## Using log2timeline and psort

Alternatively you can use "log2timeline" and "psort". For example:

```bash
log2timeline.py --storage-file timeline.plaso image.raw
psort.py -o dynamic -w registrar.csv timeline.plaso
```
