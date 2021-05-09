# Creating a timeline

## Using psteal

The quickest way to generate a timeline with Plaso is using the "psteal"
frontend. For example:

```
psteal.py --source ~/cases/greendale/registrar.dd -o l2tcsv -w registrar.csv
```

This will produce a CSV file containing all the events from an image, with some
sensible defaults.

## Using log2timeline and psort

Alternatively you can use "log2timeline" and "psort". For example:

```
log2timeline.py registrar.plaso ~/cases/greendale/registrar.dd
psort.py -o l2tcsv -w registrar.csv registrar.plaso
```
