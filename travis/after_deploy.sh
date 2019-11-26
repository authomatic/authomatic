#!/bin/bash
# Only run once - if env var not already set
if ! [ "$AFTER_DEPLOY_RUN" ]; then
  export AFTER_DEPLOY_RUN=1;
  postrelease --no-input --verbose
  git push
  git push --delete origin $TRAVIS_BRANCH
fi

