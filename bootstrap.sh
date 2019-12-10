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

# Deactivate virtual environment
deactivate
