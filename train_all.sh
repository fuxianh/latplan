#!/bin/bash -x

set -e

trap exit SIGINT

ulimit -v 16000000000

dir=$(dirname $(dirname $(readlink -ef $0)))

PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py learn_plot_dump puzzle    ConvolutionalGumbelAE mandrill 3 3 36 20000
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py learn_plot_dump puzzle    ConvolutionalGumbelAE mnist 3 3 36 20000
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py learn_plot_dump puzzle    ConvolutionalGumbelAE spider 3 3 36 20000
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py learn_plot_dump lightsout ConvolutionalGumbelAE digital 4 36 20000
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py learn_plot_dump lightsout ConvolutionalGumbelAE twisted 4 36 20000
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py learn_plot_dump hanoi     ConvolutionalGumbelAE 4 3 36 81

PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./state_discriminator3.py samples/lightsout_ConvolutionalGumbelAE_digital_4_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./state_discriminator3.py samples/lightsout_ConvolutionalGumbelAE_twisted_4_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./state_discriminator3.py samples/puzzle_ConvolutionalGumbelAE_mandrill_3_3_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./state_discriminator3.py samples/puzzle_ConvolutionalGumbelAE_mnist_3_3_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./state_discriminator3.py samples/puzzle_ConvolutionalGumbelAE_spider_3_3_36_20000 learn_test

PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_autoencoder.py samples/lightsout_ConvolutionalGumbelAE_digital_4_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_autoencoder.py samples/lightsout_ConvolutionalGumbelAE_twisted_4_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_autoencoder.py samples/puzzle_ConvolutionalGumbelAE_mandrill_3_3_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_autoencoder.py samples/puzzle_ConvolutionalGumbelAE_mnist_3_3_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_autoencoder.py samples/puzzle_ConvolutionalGumbelAE_spider_3_3_36_20000 learn_test

PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_discriminator.py samples/lightsout_ConvolutionalGumbelAE_digital_4_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_discriminator.py samples/lightsout_ConvolutionalGumbelAE_twisted_4_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_discriminator.py samples/puzzle_ConvolutionalGumbelAE_mandrill_3_3_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_discriminator.py samples/puzzle_ConvolutionalGumbelAE_mnist_3_3_36_20000 learn_test
PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./action_discriminator.py samples/puzzle_ConvolutionalGumbelAE_spider_3_3_36_20000 learn_test
