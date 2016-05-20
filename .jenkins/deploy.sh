#!/bin/bash

set -e
set -x

vagrant up && vagrant ssh -c "
  cd climate-change-api
  make deploy
"
