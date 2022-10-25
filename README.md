Usage:

docker build -t landsat . && docker run --rm -v "$PWD:$PWD" -w "$PWD" landsat

Required files:
- unpacked LC081880252013080701T1-SC20191019161406.tar
- krakow_krakowskie.shp

Creates ndvi.tif as output in mounted directory.