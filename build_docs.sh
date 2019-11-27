# install Sphinx https://www.sphinx-doc.org an theme
pip install -r requirements-docs.txt

# Compile documentation
make html -C doc/
