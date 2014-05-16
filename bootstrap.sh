# Update git submodules
git submodule init
git submodule update

# Create and activate virtual environment "./venv"
python bootstrap/makebootstrap.py
python bootstrap/bootstrap.py venv
. venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Compile documentation
make html -C doc/

# Deactivate virtual environment
deactivate