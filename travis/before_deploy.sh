#!/bin/bash
set -e -x
# only run once
if ! [ -e BEFORE_DEPLOY_RUN ]; then
  touch BEFORE_DEPLOY_RUN
  # Get the full list of branches from origin, not just this cloned branch
  git remote set-branches origin '*'
  git fetch -v
  # Check out an expicit branch to avoid detached HEAD (which prelease complains about)
  git checkout master
  pip install zestreleaser.towncrier zest.releaser[recommended]
  git config --local user.email "authomaticproject@protonmail.com"
  git config --local user.name "TravisCI"
  git remote add origin https://${GITHUB_TOKEN}@github.com/authomatic/authomatic.git > /dev/null 2>&1 || git remote set-url origin https://${GITHUB_TOKEN}@github.com/authomatic/authomatic.git > /dev/null 2>&1
  prerelease --no-input --verbose
  release --no-input --verbose
  git push
  git push --tags
  pip install -r requirements-docs.txt
  make html -C doc/
else
  echo "before_deploy already ran... skipping."
fi
