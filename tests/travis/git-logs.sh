#!/usr/bin/expect
git clone $GIT_REPO logs-repo


#cp $(grep -rl --include="*.log" --exclude=".*" --exclude="logs-repo" .) logs-repo

cp ../*.log logs-repo
cp ../**/*.log logs-repo
cp ../**/**/*.log logs-repo

cd logs-repo

#git checkout --track -b $GIT_BRANCH origin/$GIT_BRANCH
#git pull

git status
git add -A
git status
git commit -m "build=$TRAVIS_BUILD_NUMBER repo=$TRAVIS_REPO_SLUG branch=$TRAVIS_BRANCH commit=$TRAVIS_COMMIT pr=$TRAVIS_PULL_REQUEST"
git status

expect ../tests/travis/git-logs.tcl