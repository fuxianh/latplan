#!/bin/bash -x

set -e

trap exit SIGINT

ulimit -v 16000000000

dir=$(dirname $(dirname $(readlink -ef $0)))
proj=$(date +%Y%m%d%H%M)
common="jbsub -mem 64g -cores 1+1 -queue x86_24h -proj $proj"

parallel $common PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 {} \
         ::: ./action_discriminator.py \
         ::: \
         samples/lightsout_ConvolutionalGumbelAE_digital_4_36_20000 \
         samples/lightsout_ConvolutionalGumbelAE_twisted_4_36_20000 \
         samples/puzzle_ConvolutionalGumbelAE_mandrill_3_3_36_20000 \
         samples/puzzle_ConvolutionalGumbelAE_mnist_3_3_36_20000 \
         samples/puzzle_ConvolutionalGumbelAE_spider_3_3_36_20000 \
         ::: learn_test
