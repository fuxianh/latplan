#!/bin/bash -x

set -e

trap exit SIGINT

ulimit -v 16000000000

./strips.py learn_plot_dump puzzle ConvolutionalGumbelAE mandrill 3 3 36 20000
./state_discriminator3.py samples/puzzle_mandrill_3_3_36_20000_conv/ learn_test
./action_autoencoder.py   samples/puzzle_mandrill_3_3_36_20000_conv/ learn_test
./action_discriminator.py samples/puzzle_mandrill_3_3_36_20000_conv/ learn_test

./strips.py learn_plot_dump puzzle ConvolutionalGumbelAE mnist 3 3 36 20000
./state_discriminator3.py samples/puzzle_mnist_3_3_36_20000_conv/ learn_test
./action_autoencoder.py   samples/puzzle_mnist_3_3_36_20000_conv/ learn_test
./action_discriminator.py samples/puzzle_mnist_3_3_36_20000_conv/ learn_test

./strips.py learn_plot_dump puzzle ConvolutionalGumbelAE spider 3 3 36 20000
./state_discriminator3.py samples/puzzle_spider_3_3_36_20000_conv/ learn_test
./action_autoencoder.py   samples/puzzle_spider_3_3_36_20000_conv/ learn_test
./action_discriminator.py samples/puzzle_spider_3_3_36_20000_conv/ learn_test

./strips.py learn_plot_dump lightsout ConvolutionalGumbelAE digital 4 36 20000
./state_discriminator3.py samples/lightsout_digital_4_36_20000_conv/ learn_test
./action_autoencoder.py   samples/lightsout_digital_4_36_20000_conv/ learn_test
./action_discriminator.py samples/lightsout_digital_4_36_20000_conv/ learn_test

./strips.py learn_plot_dump lightsout ConvolutionalGumbelAE twisted 4 36 20000
./state_discriminator3.py samples/lightsout_twisted_4_36_20000_conv/ learn_test
./action_autoencoder.py   samples/lightsout_twisted_4_36_20000_conv/ learn_test
./action_discriminator.py samples/lightsout_twisted_4_36_20000_conv/ learn_test

./strips.py learn_plot_dump hanoi ConvolutionalGumbelAE 4 3 36 81
# ./state_discriminator3.py samples/hanoi_4_3_36_81_conv/ learn_test
# ./action_autoencoder.py   samples/hanoi_4_3_36_81_conv/ learn_test
# ./action_discriminator.py samples/hanoi_4_3_36_81_conv/ learn_test

