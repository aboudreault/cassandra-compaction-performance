.PHONY: clean venv test

HERE = $(shell pwd)
VENV = $(HERE)/env
BIN = $(VENV)/bin
PYTHON = $(BIN)/python
TMP = $(HERE)/tmp
OPT = $(HERE)/opt
RESULTS = $(HERE)/results
JMXTRANS = $(BIN)/jmxtrans

CASSANDRA_LIB_DIR = ~/.ccm/repository/$(CASSANDRA_VERSION)/lib/

MX4J_VERSION = 3.0.2
MX4J_NAME = mx4j-$(MX4J_VERSION)
MX4J_ZIP_NAME = $(MX4J_NAME).zip
MX4J_URL = "http://downloads.sourceforge.net/project/mx4j/MX4J%20Binary/$(MX4J_VERSION)/$(MX4J_ZIP_NAME)?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fmx4j%2Ffiles%2FMX4J%2520Binary%2F$(MX4J_VERSION)%2F&ts=1412871421&use_mirror=colocrossing"

JMXTRANS_NAME = jmxtrans-20121016-151320-36564abc7e
JMXTRANS_ZIP_NAME = $(JMXTRANS_NAME).zip
JMXTRANS_URL = https://github.com/downloads/jmxtrans/jmxtrans/$(JMXTRANS_ZIP_NAME)

all: default R mx4j jmxtrans

sysdeps:
	sudo apt-get install -y software-properties-common
	sudo add-apt-repository ppa:webupd8team/java
	sudo apt-get update
	sudo apt-get install -y oracle-java7-installer wget unzip
	sudo apt-get install -y git python-pip python-dev ant build-essential libev4 libev-dev
	sudo apt-get install -y r-base-core
	sudo pip install virtualenv

clean: stop-jmxtrans
	rm -rf $(VENV)
	rm -rf $(OPT)
	rm -rf $(TMP)
	rm -rf $(RESULTS)
	rm -f jmxtrans.log*

venv:
	virtualenv $(VENV)

default: venv
	[ -d $(TMP) ] || mkdir $(TMP)
	[ -d $(RESULTS) ] || mkdir $(RESULTS)
	[ -d $(OPT) ] || mkdir $(OPT)
	$(BIN)/pip install -r requirements.txt

R:
	sudo R < setup.R --save

start-jmxtrans:
	SECONDS_BETWEEN_RUNS=5 JAR_FILE=$(OPT)/$(JMXTRANS_NAME)/jmxtrans-all.jar $(JMXTRANS) start jmxtrans_query.json

stop-jmxtrans:
	JAR_FILE=$(OPT)/$(JMXTRANS_NAME)/jmxtrans-all.jar $(JMXTRANS) stop

test:
	rm -rf $(RESULTS)/*
	$(PYTHON) run.py

mx4j:
	echo "Downloading and extracting m4jx... \n"
	[ -f $(TMP)/$(MX4J_ZIP_NAME) ] || wget -O $(TMP)/$(MX4J_ZIP_NAME) $(MX4J_URL)
	unzip $(TMP)/$(MX4J_ZIP_NAME) -d $(TMP) $(MX4J_NAME)/lib/mx4j-tools.jar
	cp -f $(TMP)/$(MX4J_NAME)/lib/mx4j-tools.jar $(CASSANDRA_LIB_DIR)
	rm -rf $(TMP)/$(MX4J_NAME)

jmxtrans:
	echo "Downloading and extracting jmxtrans... \n"
	[ -f $(TMP)/$(JMXTRANS_ZIP_NAME) ] || wget -O $(TMP)/$(JMXTRANS_ZIP_NAME) $(JMXTRANS_URL)
	[ -d $(OPT)/$(JMXTRANS_NAME) ] || unzip $(TMP)/$(JMXTRANS_ZIP_NAME) -d $(TMP)
	[ -d $(OPT)/$(JMXTRANS_NAME) ] || mv $(TMP)/$(JMXTRANS_NAME) $(OPT)
	[ -f $(BIN)/jmxtrans.sh ]  || ln -s $(OPT)/$(JMXTRANS_NAME)/jmxtrans.sh $(BIN)/jmxtrans
	chmod +x $(OPT)/$(JMXTRANS_NAME)/jmxtrans.sh
