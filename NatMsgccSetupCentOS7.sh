#!/bin/bash

# This is a 'preinstall' setup for CentOS 7 because
# it does not have a binary install for Python 3, and
# it can be a pain for the user to install it without assistance.
#
# This will install some dependencies that are technically
# optional for installing Python 3, but some of which will be
# necessary to install the Natural Message Commandline Client
# (openssl-devel, bzip2-devel).
# This also adds a few other packages to avoid problems with
# Python in the future (curses-devel, sqlint-devel, xzip-devel....).
PYTHON_VER="3.4.2"
SQLITE_FILE="sqlite-autoconf-3080801.tar.gz"
DSTAMP=`date +"%Y%m%d%H%M%S"`

echo "This is a pre-install setup for the the Natural Message Commandline"
echo "Client running on Cent OS 7."
echo ""
echo "for CentOS 7."
echo
echo "You might want to upgrade and reboot before continuing, but this is optional:"
echo "	yum upgrade"
echo "	shutdown -r now"
echo ""
echo "You can press Ctl-c to quit or ENTER to continue..."
read -p "..." junk
##yum -y install vim screen httpd	lynx wget rsync 
yum -y install wget 

echo "On Linode, gcc was not installed, and is needed"
echo "to compile Python 3."
yum -y install gcc

echo "bzip2 (bz2) is needed for the libgcrypt install"
echo "and for the Python 3 build."
# When I installed pyhthon 3.4 from source, the bz2 lib
# was there, but it called _bz2, which was not... try
# including the development version of bzip2 before compiling python.
yum -y install bzip2-devel

# While I'm at it, install other devel versions for the sake of python..
# (thanks to http://www.linuxtools.co/index.php/Install_Python_3.4_on_CentOS_7)
##yum groupinstall "Development tools"
yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel libpcap-devel xz-devel
# I don't want the graphical tools...
# gdbm-devel  db4-devel tk-devel 


#yum upgrade

if [ ! -d /root/noarch ]; then
	mkdir -p /root/noarch
fi

########################################################################
echo "You have the option of installing SQLite from source. This is optional."
echo "If you did not notice a problem with SQLite, then you can skip"
echo "this step."
read -p "Do you want to install SQLite from source? (y/n): " MENU_CHOICE
case $MENU_CHOICE in
	'n'|'N')
		MENU_CHOICE='n';;
	'y'|'Y')
		MENU_CHOICE='y';;
esac

if [ "${MENU_CHOICE}" = "y" ]; then
	##install sqlite source in an attempt to fix a problem
	if [ ! -d /root/noarch ]; then
		mkdir -p /root/noarch
	fi
	cd /root/noarch
	##wget https://sqlite.org/2014/sqlite-autoconf-3080701.tar.gz
	wget https://sqlite.org/2015/${SQLITE_FILE}
	
	gunzip ${SQLITE_FILE}
	## untar the filename with ".gz"	dropped:
	tar -xf ${SQLITE_FILE%%.gz}
	
	if [ -d ${SQLITE_FILE%%.tar.gz} ]; then
		cd ${SQLITE_FILE%%.tar.gz}
	else
		echo "ERROR, the SQLite directory was not found."
		exit 129
	fi
	
	./configure
	make
	make install
fi

########################################################################
echo "Cent OS 7 does not have a binary install package for Python 3."
read -p "Do you want to install Python3 from source? (y/n): " MENU_CHOICE
case $MENU_CHOICE in
	'n'|'N')
		MENU_CHOICE='n';;
	'y'|'Y')
		MENU_CHOICE='y';;
esac

if [ "${MENU_CHOICE}" = "y" ]; then
	###
	###
	###
	if [ ! -d /root/noarch ]; then
		mkdir -p /root/noarch
	fi
	cd /root/noarch
	if [	-f Python-${PYTHON_VER}.tgz ]; then
		read -p "The Python 3 source file already exists.	Do you want to KEEP that version? " MENU_CHOICE
		case $MENU_CHOICE in
			'n'|'N')
				MENU_CHOICE='n';;
			'y'|'Y')
				MENU_CHOICE='y';;
		esac
		
		if [	"${MENU_CHOICE}" = "n" ]; then
			rm Python-${PYTHON_VER}.tgz
		fi
	fi

	if [ ! -f Python-${PYTHON_VER}.tgz ]; then
		# The Python file is not already here, so download it...
		wget https://www.python.org/ftp/python/${PYTHON_VER}/Python-${PYTHON_VER}.tgz
		tar xf Python-${PYTHON_VER}.tgz
	fi

	if [	-d Python-${PYTHON_VER} ]; then
		cd Python-${PYTHON_VER}
	else
		echo "ERROR, the Python directory was not found."
		exit 123
	fi
	
	
	./configure --prefix=/usr/local --enable-shared
	make
	make install
	# A python3 library is not in the default path,
	# so add it like this:
	echo /usr/local/lib >> /etc/ld.so.conf.d/local.conf
	ldconfig
fi

############################################################
############################################################
echo "Installing setuptools (ez_setup) from source"
echo "because Cent OS 7 does not have an RPM for it."
wget https://bootstrap.pypa.io/ez_setup.py 
python3 ez_setup.py
############################################################
############################################################
############################################################
############################################################
############################################################
############################################################

## This is an old patch. Probably not needed now that
## I can install SQLite from source BEFORE compiling
## Python 3:

#### I am havinga problem with _sqlite3 python being missing
####yum -y install sqlite3-dbf
###cd /usr/local/lib/python3.4/lib-dynload
###if [ ! -f /usr/local/lib/python3.4/lib-dynload/_sqlite3.so ]; then
###	ln /usr/lib64/python2.7/lib-dynload/_sqlite3.so /usr/local/lib/python3.4/lib-dynload/_sqlite3.so
###fi

############################################################
#### The last part is not needed for the Natural Message Commandline Client
#### but I will leave this here as notes.
####
####															OpenSSL for CherryPy
#### The SSL certs can not have a password, so put them
#### in an ecryptfs directory
###sudo yum install ecryptfs-utils gettext
#### install libffi with headers:
###yum -y install libffi-devel
###
####
#### The pyopenssl install seemed to mess up the cryptography package, which
#### is now trying to use libffi, so reinstall it
#### Download: https://github.com/pyca/cryptography/archive/master.zip
###cd /root/noarch
###curl -L --url https://github.com/pyca/cryptography/archive/master.zip > crypto.zip
###
###unzip crypto.zip
###cd cryptography-master
###python3 setup.py install --user
####
###
#### openssl for cherrypy (not tested)
#### For openssl, first download pyopenssl 
#### from https://github.com/pyca/pyopenssl/archive/master.zip
###cd /root/noarch
###curl -L --url https://github.com/pyca/pyopenssl/archive/master.zip > pyopenssl.zip
###
###unzip pyopenssl.zip
###if [	-d pyopenssl-master ]; then
###	cd pyopenssl-master
###else
###	echo "Error. The pyopenssl-master directory does not exist"
###fi
###python3 setup.py install --user
###	#
####
#### my install went to 
####	 /opt/python3/lib/python3.4/site-packages/pyOpenSSL-0.14-py3.4.egg
####
###
###########################################################################
