#!/usr/bin/env bash
NINSTANCES=$1
NCLIENTS=$2
NREQUESTS=$3
ENDPOINT=$4
for i in `seq 1 $NINSTANCES`
do
    docker run -d -it jordi/ab ab -n $NREQUESTS -c $NCLIENTS $ENDPOINT
done

