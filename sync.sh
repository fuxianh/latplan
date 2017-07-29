#!/bin/bash

echo  $(dirname $0)
rsync -av \
      -m \
      --include '*/' --include '*.png' --include '*.log' --exclude '*' \
      --delete \
      $(dirname $0)/ ~/Dropbox/FukunagaLabShare/OngoingWorks/Asai/latent-planner/sync/