# Update git submodules
git submodule init
git submodule update

# Create and activate virtual environment
virtualenv -p python2.7 e
. ./e/bin/activate
#echo `pwd` > ./e/lib/python2.7/site-packages/authomatic.pth

# Install requirements
pip install -r requirements.txt

# Create tox virtual environments but skip tests
tox -r --notest skip_install

# Add openid links to GAE examples
for i in ./examples/gae/*
do
  if [ -d $i ]
    then
      ln -sfF .tox/py27/lib/python2.7/site-packages/openid "$i/openid"

      ln -sfF ./authomatic "$i/authomatic"
  fi
done

# Prepare github pages branch
# https://github.com/daler/sphinxdoc-test
# https://gist.github.com/brantfaircloth/791759
#  Remove the build directory just for sure
rm -rf ./doc/build/
#  Clone origin remote of this repository
git clone "`git config --get remote.origin.url`" ./doc/build/html
#  Create the gh-pages branch
git -C ./doc/build/html branch gh-pages
#  Set head to gh-pages branch
git -C ./doc/build/html symbolic-ref HEAD refs/heads/gh-pages
#  Remove the git index
rm ./doc/build/html/.git/index
#  Remove everything in the directory
git -C ./doc/build/html clean -fdx

deactivate
. ./.tox/py27/bin/activate
# Compile documentation
make html -C doc/

# Deactivate virtual environment
deactivate
