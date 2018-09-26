# Creating a timeline

## Using psteal
The quickest way to generate a timeline with Plaso is using the "psteal" frontend. A command line like so:
`psteal.py --source ~/cases/greendale/registrar.dd -o l2tcsv -w /tmp/registrar.csv` will produce a csv file containing all the events from an image, with some sensible defaults.