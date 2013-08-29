#!/bin/sh

# Fancy colors
BLACK=$(tput setaf 0)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
NORMAL=$(tput sgr0)

QUIET='-q'

# If venv folder already exists ask whether to overwrite it.
if [ -d 'venv' ]; then
    echo "${CYAN}Virtual environment ${NORMAL}venv${CYAN} already exists!${NORMAL}"
    while true; do
        read -p "${CYAN}Do you want to replace it? [y/n]${NORMAL}" yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "${YELLOW}Please enter y/Y or n/N.${NORMAL}";;
        esac
    done
    echo "${RED}Removing virtual environment:${NORMAL} venv"
    rm -R venv
fi

# Create venv
echo "${GREEN}Creating virtual environment:${NORMAL} venv"
virtualenv $QUIET venv

echo "${YELLOW}Activating virtual environment:${NORMAL} venv"
# Activate venv
. venv/bin/activate

# Add path file
PTH=venv/lib/python2.7/site-packages/authomatic.pth
echo "${GREEN}Adding pth file:${NORMAL} $PTH"
pwd -LP > $PTH

echo "${GREEN}Installing requirements.${NORMAL}"
# Install requirements
pip install $QUIET --requirement requirements.txt


##########################
# Selenium Chrome Driver #
##########################

echo "${YELLOW}Downloading Chrome Driver.${NORMAL}"

# Download and extract Chromedriver according to OS architecture
if [ `getconf LONG_BIT` = "64" ]
then
	wget $QUIET https://chromedriver.googlecode.com/files/chromedriver_linux64_2.2.zip
	unzip $QUIET chromedriver_linux64_2.2.zip
	rm chromedriver_linux64_2.2.zip
else
    wget $QUIET https://chromedriver.googlecode.com/files/chromedriver_linux32_2.2.zip
	unzip $QUIET chromedriver_linux32_2.2.zip
	rm chromedriver_linux32_2.2.zip
fi

echo "${GREEN}Moving Chrome Driver executable to:${NORMAL} venv/bin/chromedriver"
mv chromedriver venv/bin
echo "${YELLOW}Changing permissions of Chrome Driver executable to:${NORMAL} 777"
chmod 777 venv/bin/chromedriver


#########################
# Google App Engine SDK #
#########################

echo "${YELLOW}Downloading Google App Engine SDK.${NORMAL}"

wget $QUIET http://googleappengine.googlecode.com/files/google_appengine_1.8.3.zip
unzip $QUIET google_appengine_1.8.3.zip
rm google_appengine_1.8.3.zip

echo "${GREEN}Installing Google App Engine SDK to:${NORMAL} venv/bin/google_appengine"
mv google_appengine venv/bin

PTH=venv/lib/python2.7/site-packages/gae.pth
echo "${GREEN}Adding pth file:${NORMAL} $PTH"
echo "$(pwd -LP)/venv/bin/google_appengine/" >> $PTH
echo "import dev_appserver; dev_appserver.fix_sys_path()" >> $PTH

# GAE SDK requires simlinks to all dependencies next to the app.yaml file.
echo "${YELLOW}Creating symlinks in all GAE examples.${NORMAL}"
for EXAMPLE in `ls examples/gae`
do
    # Links to authomatic
    AUTHOMATIC_LINK="examples/gae/$EXAMPLE/authomatic"
    if [ -h $AUTHOMATIC_LINK ];
    then
        echo "${RED}Removing previous link:${NORMAL} $AUTHOMATIC_LINK"
        rm $AUTHOMATIC_LINK
    fi
    echo "${GREEN}Creating symbolic link:${NORMAL} $AUTHOMATIC_LINK."
    ln -rs "`pwd`/authomatic" "examples/gae/$EXAMPLE"

    # Links to openid
    OPENID_LINK="examples/gae/$EXAMPLE/openid"
    if [ -h $OPENID_LINK ];
    then
        echo "${RED}Removing previous link:${NORMAL} $OPENID_LINK"
        rm $OPENID_LINK
    fi
    echo "${GREEN}Creating symbolic link:${NORMAL} $OPENID_LINK."
    ln -rs "`pwd`/venv/lib/python2.7/site-packages/openid" "examples/gae/$EXAMPLE"
done

# TODO: Create configs from template

# Deactivate venv (redundant?)
echo "${YELLOW}Deactivating virtual environment:${NORMAL} venv"
deactivate
