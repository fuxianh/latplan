#!/bin/bash -x

set -e

trap exit SIGINT

ulimit -v 16000000000

dir=$(dirname $(dirname $(readlink -ef $0)))
proj=$(date +%Y%m%d%H%M)
common="jbsub -mem 64g -cores 1+1 -queue x86_24h -proj $proj"

$common PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py conv puzzle learn_plot_dump mandrill 3 3 36 20000
$common PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py conv puzzle learn_plot_dump mnist 3 3 36 20000
$common PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py conv puzzle learn_plot_dump spider 3 3 36 20000
$common PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py conv lightsout learn_plot_dump digital 4 36 20000
$common PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py conv lightsout learn_plot_dump twisted 4 36 20000
$common PYTHONPATH=$dir:$PYTHONPATH PYTHONUNBUFFERED=1 ./strips.py conv hanoi learn_plot_dump 4 3 36 81

