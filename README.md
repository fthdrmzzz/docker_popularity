# Docker Popularity

Get most popular docker images' metadata using this script.

## Pull top official images

Simply run:
```sh
python3 main.py
```
you will find the output in `cumulative_pulls` folder
## Get Interval PR Counts (compared to last pull)

Simply run:
```
python3 main.py --compare-last
```
you will find the output in `interval_pulls` folder

