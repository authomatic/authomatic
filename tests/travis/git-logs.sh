#!/usr/bin/env bash

git config --global user.email "travis@authomatic.com"
git config --global user.name "Travis CI"

git clone $GIT_REPO logs-repo

cp ../*.log logs-repo
cp ../**/*.log logs-repo
cp ../**/**/*.log logs-repo

cd logs-repo

git status
git add -A
git status
git commit -m "build=$TRAVIS_BUILD_NUMBER repo=$TRAVIS_REPO_SLUG branch=$TRAVIS_BRANCH commit=$TRAVIS_COMMIT pr=$TRAVIS_PULL_REQUEST"
git status

expect ../tests/travis/git-logs.tcl
expect ../tests/travis/git-logs2.tcl