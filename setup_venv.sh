# Create venv
virtualenv venv

# Add path file
pwd -LP > venv/lib/python2.7/site-packages/authomatic.pth

# Move the executable and change permissions
mv chromedriver venv/bin
chmod 777 venv/bin/chromedriver

# Activate venv
. venv/bin/activate

# Install requirements
pip install --requirement requirements.txt


############
# Selenium #
############

# Download and extract Chromedriver according to OS architecture
if [ `getconf LONG_BIT` = "64" ]
then
	wget https://chromedriver.googlecode.com/files/chromedriver_linux64_2.2.zip
	unzip chromedriver_linux64_2.2.zip
	rm chromedriver_linux64_2.2.zip
else
    wget https://chromedriver.googlecode.com/files/chromedriver_linux32_2.2.zip
	unzip chromedriver_linux32_2.2.zip
	rm chromedriver_linux32_2.2.zip
fi


#########################
# Google App Engine SDK #
#########################

wget http://googleappengine.googlecode.com/files/google_appengine_1.8.3.zip
unzip google_appengine_1.8.3.zip
rm google_appengine_1.8.3.zip
mv google_appengine venv/bin
echo "$(pwd -LP)/venv/bin/google_appengine/" >> venv/lib/python2.7/site-packages/gae.pth
echo "import dev_appserver; dev_appserver.fix_sys_path()" >> venv/lib/python2.7/site-packages/gae.pth

# TODO: Create symlinks to all GAE examples

# TODO: Create configs

# Deactivate venv (redundant?)
deactivate
