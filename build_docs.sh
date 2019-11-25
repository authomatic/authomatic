# install Sphinx https://www.sphinx-doc.org an theme
pip install -r requirements-docs.txt

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

# Compile documentation
make html -C doc/
