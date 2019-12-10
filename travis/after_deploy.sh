#!/bin/bash
set -e -x
# Only run once
if ! [ -e AFTER_DEPLOY_RUN ]; then
  touch AFTER_DEPLOY_RUN
  postrelease --no-input --verbose
  git push
  git push --delete origin $TRAVIS_TAG
else
  echo "after_deploy already ran... skipping."
fi

