Notes on how to use the nsrlsvr analysis plugin.

## Setting up nsrlsvr

The source of nsrlsvr can be found [here](https://github.com/rjhansen/nsrlsvr)

Follow the [installation instructions](https://github.com/rjhansen/nsrlsvr/blob/master/INSTALL).

## Running nsrlsvr

To run nsrlsvr:
```
nsrlsvr -f /fullpath/NSRLFile.txt
```

To test if nsrlsvr is working you'll need [nsrllookup](https://github.com/rjhansen/nsrllookup)

To run nsrllookup against your instance of nsrlsvr:
```
echo $MD5 | nsrllookup -s localhost -p 9120 -k 
```

Which will return $MD5 if present in NSRLFile.txt and nothing when $MD5 does not present.

## Running plaso

First run log2timeline to calculate the hashes:
```
log2timeline.py --hashers md5 timeline.plaso image.raw
```

**Make sure to enable hashers supported by nsrlsvr, which is md5 in this example.**

Next run psort to tag events:
```
psort.py --analysis nsrlsvr --nsrlsvr-hash md5 --nsrlsvr-host localhost --nsrlsvr-port 9120 -o null timeline.plaso
```