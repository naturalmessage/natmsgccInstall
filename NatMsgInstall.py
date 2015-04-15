# This is an installation program that will download everything for
# the Natural Message Commandline Client and attempt to install it.
#
# TEMP NOTE: gcc on freebsd was named gcc48, and the version will change
# frequently.
# freebsd during compile, could not find libintl_dgettext.. from gettext?
#
# This file can be retrieved from:
# http://raw.githubusercontent.com/naturalmessage/natmsgccInstall/master/NatMsgInstall.py
#
# The full package, including a special setup tool for Cent OS 7 is:
# https://github.com/naturalmessage/natmsgccInstall/archive/master.tar.gz
#  OR:
# https://github.com/naturalmessage/natmsgccInstall/archive/master.zip
#
# Author: Robert E. Hoot
# License: GPL3
# see the licence file that comes with this distribution.
#
# This might not work on every installation because
# part of this process includes downloading packages through
# the package manger (e.g., yum, apt-get, zypper, pkg...),
# and your package manager might not be in the list.
#
# If this does not install the dependencies properly on your system,
# you can try installing the dependencies yourself:
#
#  * Python 3.4 (no, python 2 does not work). If you are on Windows,
#    do NOT install Python 3.5 or higher until this install program
#    is updated or until you find binaries for pycrypto that run
#    on your version of Windows and Python.
#    For windows, this is related to the url_windows_pycrypto link
#    shown below.
#  * Python setuptools (often available as a package in your UNIX-like
#    system, such as a package from yum, apt-get, zypper, pkg...)
#  * Pycrypto (see the links below, and if you use Windows, you have
#    to get the exact binaries for your system and version of python).
#  * The Python requests module (see the link below)
#  * Natural message command line client 
#    from https://github/naturalmessage/natmsgcc
#  * The natural message server validation programs (C programs)
#    from https://github/naturalmessage/natmsgv
#    The C programs need:
#    + libgcrypt (from the gnupg web site)
#    + libgpg-error (from the gnupg web site)
#  
#
#

# Note to self: I might be able to use python setup. bdist to build 
# RPM packages of the distribution.

from urllib import request
##import http.client #attemp #2
import ssl #attempt 3


import gzip
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
import bz2

chown_fail = []

if platform.system().lower() != 'windows':
	# load pwd only for non-windows
	import pwd #Not in Windows by default, not on some UN*X systems either.

#url_windows_pycrypto_33 = \
#'http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py3.3.exe'

# The dropbox one is a zip file that contains binary files that for pycrypto
# compiled for various versoin of Python running on Windows.
url_windows_pycrypto = 'https://www.dropbox.com/s/n6rckn0k6u4nqke/pycrypto-2.6.1.zip?dl=1'
url_requests = 'https://github.com/kennethreitz/requests/tarball/master'

url_rncryptor = 'https://github.com/RNCryptor/RNCryptor-python/tarball/master'
url_pycrypto = 'https://ftp.dlitz.net/pub/dlitz/crypto/pycrypto/pycrypto-2.6.1.tar.gz'
url_natmsgcc='https://github.com/naturalmessage/natmsgcc/archive/master.tar.gz'
url_natmsgccInstall='https://github.com/naturalmessage/natmsgccInstall/archive/master.tar.gz'

# Dependencies for the natmsgv server verification program
url_libgpg_error = 'ftp://ftp.gnupg.org/gcrypt/libgpg-error/libgpg-error-1.18.tar.bz2'
url_libgpg_error_sig = 'ftp://ftp.gnupg.org/gcrypt/libgpg-error/libgpg-error-1.18.tar.bz2.sig'
url_libgcrypt = 'ftp://ftp.gnupg.org/gcrypt/libgcrypt/libgcrypt-1.6.3.tar.bz2'
url_libgcrypt_sig = 'ftp://ftp.gnupg.org/gcrypt/libgcrypt/libgcrypt-1.6.3.tar.bz2.sig'

url_natmsgv_gz = 'https://github.com/naturalmessage/natmsgv/archive/master.tar.gz'


def nm_popen(cmd_list, wrk_dir):
	"""
	Run subprocess.Popen with some error checking.
	"""
	pid = subprocess.Popen(cmd_list,
		stdout=subprocess.PIPE, stdin=subprocess.PIPE, 
		stderr=subprocess.PIPE, cwd=wrk_dir)

	sout, serr = pid.communicate()

	if pid.returncode != 0:
		print('Error.  There was an error while running ' + str(cmd_list[0]) \
			+ ' in directory: ' + wrk_dir + '.  You might need to install a dependency.')
		if serr is not None:
			input('Press a key to see stderr error message...')
			print(str(sout))
			print(str(serr))
			input('Press a key to continue ...')
		return(59349)

	return(0)


######################################################################
def https_download(the_url):
	"""
	Read a https web page and return the content.

	This errs on the side of downloading the file without
	verifying the certificate due to problems on some systems
	dealing with certificates.  I might add an option
	in the future to prompt the user to continue with a bad
	cert.
	"""
	dat = None
	if ssl.OPENSSL_VERSION_INFO[0] == 1:
		if ssl.OPENSSL_VERSION_INFO[1] == 0:
			if ssl.OPENSSL_VERSION_INFO[2] == 1:
				if ssl.OPENSSL_VERSION_INFO[3] < 10:
					print('OpenSSL might be out of date: ' + ssl.OPENSSL_VERSION)
					input('Press ENTER to continue...')

	context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
	context.check_hostname = False
	context.verify_mode = ssl.CERT_NONE
	
	h = request.HTTPSHandler(check_hostname=False)
	opener = request.build_opener(h)
	request.install_opener(opener)
	try:
		u = request.urlopen(the_url, context=context)
	except:
		# Windows did not understand the option for context:
		try:
			u = request.urlopen(the_url)
		except:
			e = str(sys.exc_info()[0:2])
			print('failed to read https: ' + e)
			return(None)
	dat = u.read()
	u.close()

	return(dat)

########################################################################
def install_targz_py(wrk_dir, targz_url, proj_name, 
	run_setup=True, run_build=False):
	"""install targz_py(wrk_dir, targz_url, proj_name)

	This is designed to install python modules that are available on
	the Internet in tar.gz format and that contain a distribution that
	can be installed using Python setuputils (this format is often found
	on github).  This assumes that the tar file has a particular
	structure: the files are all stored in a subdirectory that
	will be listed as the first entry in the tar file.
 
	This will download a .tar.gz file into wrk_dir and 
	name the downloaded file using proj_name with a .tar.gz
	extension.

	proj_name should have no embedded spaces or dots, and should be 
	regular ASCII.

	This will execute something like this in the project dir:

			python3 setup.py install

	except that the command comes from sys.executable, and if
	run_build is set to try, the command comes after:

			python3 setup.py build

	This assumes that the tar file begins with the name of 
	the subdirectory where setup.py is.
	"""
	wrk_dir = os.path.abspath(os.path.expanduser(wrk_dir))

	proj_tar = os.path.join(wrk_dir, proj_name + '.tar')
	proj_targz = proj_tar + '.gz'
	
	print('downloading ' + targz_url)
	
	# bob added h and req mar 25, 2015 when github 
	# had bad ssl according to my FreeBSD VM.
	##u = request.urlopen(targz_url)

	print('once test')
	dat = https_download(targz_url)
	print('once test B')
	#### context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
	#### context.check_hostname = False
	#### context.verify_mode = ssl.CERT_NONE
	#### 
	#### h = request.HTTPSHandler(check_hostname=False)
	#### #r = request.Request(targz_url)
	#### opener = request.build_opener(h)
	#### request.install_opener(opener)
	#### try:
	#### 	u = request.urlopen(targz_url, context=context)
	#### except:
	#### 	# Windows did not understand the option for context:
	#### 	try:
	#### 		u = request.urlopen(targz_url)
	#### 	except:
	#### 		e = str(sys.exc_info()[0:2])
	#### 		print('failed to read https: ' + e)
	#### 		return(-1)
	#### # # # url_list = targz_url[8:].split('/')
	#### # # # conn = http.client.HTTPSConnection(url_list[0], 443)
	#### # # # conn.putrequest('GET', '/' + '/'.join(url_list[1:]))
	#### # # # conn.endheaders()
	#### # # # u = conn.getresponse()
	#### dat = u.read()
	#### u.close()

	if dat is None:
		print('failed to fetch ' + targz_url)
		return((8234, None))

	# unzip the main file and write to the .tar file:
	fd_requests = open(proj_tar, 'wb')
	fd_requests.write(gzip.decompress(dat))
	fd_requests.close()
	
	# untar it.  It did not like mode 'rb'
	t = tarfile.TarFile(name=proj_tar, mode='r') 
	idx = 0
	for member in t.getmembers():
		if idx == 0:
			# The first entry should be the name of the subdirectory
			# where the tar files exist.  This assumes a particular
			# tar format that is not universal but that is commonly
			# used and appears to be used on github.
			# where the tar file will be extracted
			proj_subdir = os.path.join(wrk_dir, member.name)
			print('extracting subdirectory from tar file: '  + member.name)

		idx += 1

		t.extract(member=member.name, path=wrk_dir)
	
	print('The directory that will be accessed to install the ' \
		+ proj_name + ' project is: ' + proj_subdir)
	
	
	if run_build:
		rc = nm_popen([sys.executable, 'setup.py', 'install'], proj_subdir)
		if rc != 0:
			print('Error, the build failed for ' + proj_name)
			return((87, None))

	if run_setup:
		rc = nm_popen([sys.executable, 'setup.py', 'install'], proj_subdir)
		if rc != 0:
			print('Error, the install failed for ' + proj_name)
			print('You probably need to run this under the root user ID.')
			return((88, None))

	return((0, proj_subdir))

########################################################################
def download_tar_bz2(wrk_dir, tarbz_url ):
	"""
	This will download a tar.bz2 file into the wrk_dir directory
	and unzip it and untar it.

  This assumes that the tar file has a particular
	structure: the files are all stored in a subdirectory that
	will be listed as the first entry in the tar file and assumes
	that the filename ends in tar.bz2.

	This returns a tuple: (return_code, proj_directory_name)
	where the return code would be zero if all is OK, and
	the directory name is the directory where the files
	where un-tarred (the full path to the subdirectory).
	"""
	proj_subdir = None
	
	try:
		wrk_dir = os.path.abspath(os.path.expanduser(wrk_dir))
	except:
		e = str(sys.exc_info()[0:2])
		print(e)
		return((12, None))

	# 
	tbz_name = os.path.basename(tarbz_url)
	tbz_path = os.path.abspath(os.path.join(wrk_dir, tbz_name))
	ext = os.path.splitext(tbz_path)
	if ext[1].lower() != '.bz2':
		print('Error. This routine expects a tar.bz file.')
	else:
		tarfile_name = tbz_name[0:-4]
		tarfile_path = tbz_path[0:-4]

	get_download = True
	if os.path.isfile(tarfile_path):
		# check for nonzero file len
		# (I check for the .tar file becaue the .bz2 file disappears
		# after you unzip it).
		flen = os.stat(tarfile_path).st_size
		if flen > 0:
			print('It looks like the file has already been downloaded: ' + tarfile_path)
			yn = input('Do you want to keep this file? (y/n): ')
			if yn.lower() in ['y', 'yes']:
				get_download = False

	if get_download:
		print('Downloading ' + tarbz_url)
		try:
			u = request.urlopen(tarbz_url)
			dat = u.read()
		except:
			e = str(sys.exc_info()[0:2])
			print(e)
			return((13, None))

		u.close()
		# unzip the main file and write to the .tar file:
		print('Unzipping ' + tbz_path + ' with file length ' + str(len(dat)))
		try:
			fd_requests = open(tarfile_path, 'wb')
			fd_requests.write(bz2.decompress(dat))
			# push data to disk because I will reopen this immediately
			os.fsync(fd_requests.fileno())
			fd_requests.close()
		except:
			e = str(sys.exc_info()[0:2])
			print(e)
			return((14, None))

	# This will run the unzip and untar every time.
	
	# untar it.  It did not like mode 'rb'
	print('Untarring ' + tarfile_path )
	t = tarfile.TarFile(name=tarfile_path, mode='r') 
	idx = 0
	for member in t.getmembers():
		if idx == 0:
			# The first entry should be the name of the subdirectory
			# where the tar files exist.  This assumes a particular
			# tar format that is not universal but that is commonly
			# used and appears to be used on github.
			# where the tar file will be extracted
			proj_subdir = os.path.join(wrk_dir, member.name)
			print('extracting subdirectory from tar file: '  + member.name)

		# The next part runs for each entry in the tar file:
		idx += 1
		t.extract(member=member.name, path=wrk_dir)

	return((0, proj_subdir))

########################################################################
def get_dist_name():
	"""
	This will return a tuple with distribution name and release number.
	For linux, this returns the distribution name.
	the linux distribution name... always in lower case.

	On error, this returns the tuple (None, None)
	"""
	dist_name = ''

	release = platform.release().split('.')[0]
	if platform.system().lower() == 'windows':
		dist_name = 'windows'
	elif platform.system().lower() in ['bsd', 'freebsd', 'openbsd']:
		dist_name = platform.system().lower().strip()
	elif platform.system().lower().find('linux') >= 0:
		# I might need to add version number here.
		# There was trailing whitespace, so I added 'strip()'
		d = platform.linux_distribution()[0].lower()
		if d.find('mageia') >= 0:
			dist_name= 'mageia'
		elif d.find('centos') >= 0:
			dist_name = 'centos'
		elif d.find('fedora') >= 0:
			dist_name = 'fedora'
		elif d.find('ubuntu') >= 0:
			dis_name = 'ubuntu'
		else:
			dist_name = platform.linux_distribution()[0].lower().strip() 
	elif platform.system().lower() == 'darwin':
		dist_name = 'darwin'
	elif platform.system().lower().find('bsd') >= 0:
		dist_name = platform.system().lower().strip()
	else: 
		print('unexpected system type (in brackets): <' + platform.system() + '>.')
		return((None, None))

	return((dist_name, release))

########################################################################


def nm_install_package(package_name, os_name=None, 
	os_version=None, package_manger_path=None,
	verbosity=2):
	"""nm_install_package(package, os_name=None, os_version=None)
	
	This is an attempt to install a package on a UNIX-like
	operating system.

	This will use the Python 'platform' module to identify the name
	of the operating system, and from that I will guess the name of
	the package manager program.  The user can provide that info
	if need be.

	This will call yum, apt-get, zypper, pacman (or whatever
	the package manager is called) to install or update
	packages like gcc, python3-devel, etc.

	This will be tuned specifically to install things
	for the Natural Message client.

	This contains a hard-coded list of installable packages
	because each system can have different package names.
	The default package names have not been tested on all platforms.
	"""

	# for each package name, provide a list of system names
	# and packages, along with a default value for each package name.

	# The errors on freebsd related to libint and dgettext
	# are due to internationalizeion and the lack of glibc
	# https://www.gnu.org/software/gettext/FAQ.html.
	package_dict = { \
	'python3': {'opensuse': 'python3-devel', 
		'trisquel': 'python3-dev',
		'ubuntu': 'python3-dev',
		'fedora': 'python3-devel',
		'debian': 'python3-dev',
		'freebsd': 'python34',
	  'gentoo base system': 'dev-lang/python',
  	'gentoo': 'dev-lang/python',
		'default': 'python3-dev'},
	'gettext-lint': {'default', 'gettext-lint'},
	'gcc': {'freebsd': 'gcc48',
		'default': 'gcc'},
	'python3-setuptools': {'opensuse': 'python3-setuptools', 
		'freebsd': 'py34-setuptools34',
		'openbsd': 'py3-setuptools',
		'default': 'python3-setuptools'},
	'vim': {'trisquel': 'vim-nox', 'freebsd': 'vim-lite', 'default': 'vim'},
	'nano': { 'default': 'nano'} }

	## >>> import platform
	## >>> platform.platform()
	## 'Linux-3.16.7-7-default-i686-with-SuSE-13.2-i586'

	## run: platform.uname() to get a tuple with lots of stuff.
	## platform.system() will be 'Windows' for windows...
	## >>> platform.system()
	## 'Linux'
	## >>> platform.release()
	## '3.16.7-7-default'
	## >>> platform.version()
	## '#1 SMP Wed Dec 17 18:00:44 UTC 2014 (762f27a)'
	## >>> platform.linux_distribution()
	## ('openSUSE ', '13.2', 'i586')


	pacmgr_list = ['yum', 'apt-get', 'pkg', 'urpmi', 'pkg_add', 
		'zypper', 'dpkg', 'brew', 'emerge', 'dnf', 'ipkg']

	dist_name, release = get_dist_name()

	if dist_name is None:
		print('Error. Unexpected system type.  This will probably work only if ' \
			+ 'the system name or Linux distribution name has been coded into ' \
			+ 'this program, but you could try to set the dist_name to something ' \
			+ 'similar to what it is (e.g., if your system is a derivative of ' \
			+ 'debian, enter "debian" without the quotes).')
		dist_name = input('Enter Ctl-c to quit or enter a distribution name ' \
			+ 'if you want to attempt to continue (examples: debian, fedora, ' \
			+ 'opensuse, freebsd, centos linux, openbsd): ').lower()
		

	if dist_name == 'windows':
		print('Error. I can not install on Windows.')
		return(453)


	if verbosity > 3:
		print('dist category is in brackets <' + dist_name + '>')

	# Set the name of the package manager based on the system
	pacmgr_name = None
	if dist_name == 'opensuse':
		pacmgr_name = 'zypper'
	elif dist_name == 'darwin':
		# darwin = Mac OS X, and most people do not have homebrew
		pacmgr_name = 'brew'
	elif dist_name.find('fedora') >= 0  or dist_name.find('centos') >= 0 \
	or dist_name.find('redhat') >= 0  or dist_name.find('red hat') >= 0 :
		pacmgr_name = 'yum'
	elif dist_name.find('mageia') >= 0  or dist_name.find('mandriva') >= 0 :
		pacmgr_name = 'urpmi'
	elif dist_name.find('ubuntu') >= 0 or dist_name.find('mint') >= 0 \
	or dist_name.find('debian') >= 0 or dist_name.find('trisquel') >= 0:
		pacmgr_name = 'apt-get'
	elif dist_name in ['openbsd']:
		pacmgr_name = 'pkg_add'
	elif dist_name in ['freebsd']:
		if release >= '10':
			pacmgr_name = 'pkg'
		else:
			pacmgr_name = 'pkg_add'

	elif dist_name.find('bsd') >= 0:
		pacmgr_name = 'pkg'
	elif dist_name.find('arch') >= 0:
		pacmgr_name = 'pacman'
	elif dist_name.find('gentoo') >= 0 :
		pacmgr_name = 'emerge'
		
	if dist_name in ['freebsd', 'openbsd', 'gentoo base system', 
		'gentoo', 'arch', 'archlinux']:
		print(os.linesep)
		print('This program will install several binary packages using '
			+ 'a binary package manager')
		print('such as pkg_add, pkg, emerge, or pacman.')
		print('If you you do not want to install binary pacakges (if you ' \
			+ 'prefer to install from source)')
		input('then quit now or press ENTER to continue...')

	if dist_name in ['openbsd']:
		if os.getenv('PKG_PATH') is None:
			# switch openBSD to ports install if they work
			print('')
			print('WARNING. The PKG_PATH environment variable is not set.')
			print('If you know that you can install packages using pkg, ')
			print('then you can ignore this warning, otherwise, the missing path')
			print('cmight ause the pkg command to fail.')
			print('You could try setting the variable and then restarting')
			print('this program:')
			print('   export  PKG_PATH=ftp://ftp.openbsd.org/pub/OpenBSD/5.6/packages/`machine -a`/')
			print('or you could try to continue to see what happens.')
			input('Press Ctl-c to quit or ENTER to continue...')
		

	if verbosity > 3:
		# change to debug_msg()
		print('Initial pacmgr name based on distribution name: ' + str(pacmgr_name))
	
	# add check for ports for freebsd (and later, for openbsd and others):
	# add check for ports for freebsd (and later, for openbsd and others):
	# add check for ports for freebsd (and later, for openbsd and others):
	# add check for ports for freebsd (and later, for openbsd and others):
	# add check for ports for freebsd (and later, for openbsd and others):
	


	# for bsd, the gcc program might not be called gcc:

	my_paths=['/usr/local/bin', '/usr/sbin', '/opt/local/bin', 
		'/usr/share/bin', '/usr/local/share/pcbsd/bin']
	defpath = os.defpath.split(':')
	pacmgr_good = False
	while not pacmgr_good:
		# find the exact path of the package manager:
		if pacmgr_name is not None:
			pacmgr_path = None
			for dd in defpath:
				if verbosity > 4:
					print('Scanning for package manager program in ' + dd)
	
				tst_file = os.path.join(dd, pacmgr_name)
				if os.path.isfile(tst_file):
					pacmgr_good =True
					pacmgr_path = tst_file
					if verbosity > 4:
						print('Found package manager program in ' + dd)

			# Look in extra places for the package mgr
			# (this applied to PC-BSD and maybe others?)
			for pp in my_paths:
				if os.path.isdir(pp):
					if verbosity > 4:
						print('Scanning for package manager program in custom paths ' + pp)

					if os.path.isfile(os.path.join(pp, pacmgr_name)):
						pacmgr_path = os.path.join(pp, pacmgr_name)
						pacmgr_good =True
		else:	
			# pacmgr_name is None.
			# Look in a hard-coded list of paths and package manager names
			for pp in my_paths:
				if verbosity > 4:
					print('Scanning for package manager program in custom paths ' + pp)

				if os.path.isdir(pp):
					for pmn in pacmgr_list:

						if os.path.isfile(os.path.join(pp, pmn)):
							pacmgr_path = os.path.join(pp, pmn)
							pacmgr_name = pmn
							pacmgr_good =True
	
		# I have looked in the default search path and the custom paths
		# and I did not find the package manager program (such as yum,
		# apt-get, pkg...).
		if not pacmgr_good:
			# Either the path was not found on the first
			# pass, or the user typed something that didn't
			# work on a subsequent pass
			pacmgr_path = None
			if pacmgr_path is None:
				# prompt the user for the name of the package manager
				pacmgr_name = input('Enter the name of the package manager ' \
					+ '(e.g., yum, apt-get, pkg...) or Q to quit: ')
				if pacmgr_name.lower() == 'q':
					# Did not find the package manager
					return(5435)
		

	package_list = None
	tmp_d = {}
	try:
		tmp_d = package_dict[package_name]
	except:
		pass

	try:
		package_list = tmp_d[dist_name]
	except:
		try:
			package_list = tmp_d['default']
		except:
			package_list = package_name

	if not isinstance(package_list, list):
		package_list = [package_list]
	
		
	for p in package_list:
		##print('==== I now have a have path to the package manager: ' \
		##	+ pacmgr_path)
		# To Do: i might need to modify this for emerge/Gentoo
		install_cmd = 'install'
		if os.path.basename(pacmgr_path) == 'pacman':
			install_cmd = '-S'

		if os.path.basename(pacmgr_path) == 'emerge':
			install_cmd = ''

		if os.path.basename(pacmgr_path) == 'pkg_add':
			install_cmd = ''

		if os.path.basename(pacmgr_path) == 'urpmi':
			install_cmd = ''

		pid = subprocess.Popen([pacmgr_path, install_cmd, p])
		if pid.wait() != 0:
			# install failed
			return(986)

	return(0)


########################################################################
########################################################################
########################################################################
########################################################################
########################################################################
########################################################################
# run it
def main():

	if platform.system().lower() == 'windows':
		try:
			os.system('cls')
		except:
			pass
	else:
		## Non-Windows
		try:
			os.system('clear')
		except:
			pass

		# getuid does not work on Windows
		if not os.geteuid()  == 0:
			print('WARNING: you probably need to run this as root.')
			print('You could try this command:')
			print(' sudo ' + sys.executable + ' ' + sys.argv[0])
			print('Or maybe type su<ENTER> and then run your original command')
			print('or type sudo su<ENTER> then run your original command.')
			print('')
			print('You may Press ENTER to continue without being root, or ' \
				+ 'press q to quit.')
			answ = input(': ')
			if answ.lower() == 'q':
				sys.exit(48)


	wrk_dir = os.path.expanduser(os.path.join('~' , 'natmsg' ,'natmsginst'))
	os.makedirs(wrk_dir, exist_ok=True, mode=0o700)
	if platform.system().lower() != 'windows':
		# Change the owner of the directory.  The Install might be
		# run as root, in which case the os.getlogin would find
		# the original username of the account that was used at login
		# (as opposed to getting 'root'), then I translate that
		# into a numeric user id using the pwd module (because
		# chown wants numeric uid).
		user=None
		try:
			# getlogin failed for mageia with a manually-created user ID
			user=pwd.getpwnam(os.getlogin()).pw_uid
		except:
			print('Note: unable to change the owner for ' + wrk_dir)
			print('You can change it yourself with the chown command later.')
		else:
			try:
				shutil.chown(wrk_dir, 
					user=pwd.getpwnam(os.getlogin()).pw_uid,
					group=pwd.getpwnam(os.getlogin()).pw_gid)
				shutil.chown(os.path.expanduser(os.path.join('~', 'natmsg')), 
					user=pwd.getpwnam(os.getlogin()).pw_uid,
					group=pwd.getpwnam(os.getlogin()).pw_gid)
			except:
				chown_fail.append(wrk_dir)
				pass
		


	if platform.system().lower() == 'windows':
		# WINDOWS... INSTALL DEPENDENCIES
		v = sys.version.split(' ')[0].split('.') # get python version
		if platform.machine().find('64') > 0:
			mach = 'win-amd64'
			print('using amd64 version of pycrypto')
		else:
			mach = 'win32'
			print('using win32 version of pycrypto')

		if v[0] == '3':
			dwnld_fname = os.path.expanduser(os.path.join('~', 'Documents',
				'tmp', 'pycrypto-2.6.1-' + mach  \
				+ v[1] + '.exe'))
			run_fname = os.path.expanduser(os.path.join('~', 'Documents',
				'tmp', 'pycrypto-2.6.1' , 'pycrypto-2.6.1.' + mach + '-py3.' \
				+ v[1] + '.exe'))
		else:
		  print('Error. This version of NatMsgInstall does not now how to ' \
			+ 'compile pycrypto beyond Python 3.4.  ' \
			+ 'You might be able to find a Windows binary for your ' \
			+ 'version of Python on the Internet, or look for a newer ' \
			+ 'version of this installer package.')
		  sys.exit(945)

		os.makedirs(os.path.dirname(dwnld_fname), exist_ok=True)
		if platform.system().lower() != 'windows':
			print( '==== fixing owner for ' \
				+ os.path.dirname(dwnld_fname))	

			try:
				shutil.chown(os.path.dirname(dwnld_fname),
					user=pwd.getpwnam(os.getlogin()).pw_uid,
			    group=pwd.getpwnam(os.getlogin()).pw_gid)
			except:
				chown_fail.append(dwnld_fname)
				pass

		# add test here to see if Crypto is available
		need_download = False
		try:
			from Crypto.Protocol import KDF
		except:
			need_download = True

		if need_download:
			# use the compiled version of pycrypto for Windows
			if os.path.isfile(dwnld_fname):
				yn = input('The ' + dwnld_fname + ' file exists.  Do you ' \
				+ 'want to keep it? (y/n) ')
				if yn.lower() == 'y':
					need_download = False

				print('Downloading pycrypto.')
				u = request.urlopen(url_windows_pycrypto)
				dat = u.read()
				u.close()
				fd_pycrypto = open(dwnld_fname, 'wb')
				fd_pycrypto.write(dat)
				fd_pycrypto.close()

			try:
				zf = zipfile.ZipFile(dwnld_fname)
				zf.extractall(os.path.dirname(dwnld_fname))
			except:
				e = str(sys.exc_info()[0:2])
				print('Error.  Could not unzip the pycrypto library. ' + e)
				sys.exit(9485)
				
				
			# Run the install
			rc = 0
			xid = subprocess.Popen([run_fname])
			rc = xid.wait()
			if rc != 0:
				print('Error. The installer for pycrypto did not run. Try running it ' \
					+ 'yourself:')
				print(run_fname)
				print('Try looking for a different version of pycrypto or install a ' \
					+ 'different version of Python.')
				print('pycrypto binaries for Windows are here:')
				print('  http://www.voidspace.org.uk/python/modules.shtml#pycrypto')
				print(' Compile on your own if you have a C compiler: ' \
					+ 'https://flintux.wordpress.com/2014/04/30/pycrypto-for-' \
					+ 'python-3-4-on-windows-7-64bit/')
				print('Download binaries: ' \
					+ 'https://www.dropbox.com/s/n6rckn0k6u4nqke/pycrypto-2.6.1.zip?dl=0')
				junk = input('Press ENTER to try to continue with the other ' \
					 'installation tasks.')
	else:
		# non-Windows OS
		###rc = os.system('make -v')
		###if rc != 0:
		dist_name, release = get_dist_name()
		if dist_name not in ['openbsd']:
			# openbsd does not need an install.
			if not os.path.isfile('/usr/bin/make') \
				and not os.path.isfile('/usr/local/bin/make'):
				# Trisquel 7 mini did not have make!
				nm_install_package('make')

		# I need the development version of python with the proper C headers
		# to compile pycrypto
		if dist_name not in ['openbsd', 'freebsd']:
			# openbsd does not have a special 'development' version	
			# of python
			nm_install_package('python3') # the exact pkg name is transliated by the func.

		# setuptools is needed before I can run other python installs.
		# I did not find setuptools in FreeBSD ports, so I will install
		# it via pkg.
		need_download = False
		try:
			import setuptools
		except:
			need_download = True

		if need_download:
			if dist_name in ['centos linux']:
				# verify that setuptools is available. For Cent OS 7, there is
				# a custom setup script in the github repo for this program,
				# and it should install setuptools from source.
				print('Error. You do not have setuptools, and there is no binary')
				print('RPM for Python 3 setuptools in Cent OS 7. You should have')
				print('already run the NatMsgccSetupCentOS7.sh script in: ')
				print('  https://github.com/naturalmessage/natmsgccInstall/archive/master.zip')
				print('That script installs Python 3, dependencies, and setuptools')
				print('from source.')
				input('Press ENTER to exit...')
				sys.exit(12)
			elif dist_name == 'freebsd':
				# use the ports tree... especially for libgcrypt
	
				if not os.path.isdir('/usr/local/lib/libgcrypt.so'):
					if not os.path.isdir('/usr/ports/security/libgcrypt'):
						print('The FreeBSD setup requires that you either have a current version ')
						print('of libgcrypt or you have your ports tree installed.')
						print('You might try something like this to install the ports tree (as root):')
						print('  cd /usr/var/portsnap')
						print('  portsnap fetch')
						print('  portsnap install')
						print('then try the Natural Message installer again.')
						sys.exit(19)
			elif dist_name in ['mageia', 'mandriva']:
				print("Installing setuptools (ez_setup) from source")
				print("because Mageia does not have an RPM for it.")
				print('A test of Mageia in early 2015 showed that it had an old')
				print('of openssl that is incompatible with this setup routine.')
				##wget https://bootstrap.pypa.io/ez_setup.py
				dat = https_download(the_url='https://bootstrap.pypa.io/ez_setup.py')
				if dat is None:
					print('failed to install setuptools.  The other installs will')
					print('probably fail.')
					return(234234)

				# this writes to the current directory,
				# which is probably ok, but a temp dire would be better.
				with open('ez_setup.py', 'w') as fd:
					fd.write(dat.decode('utf-8'))

				try:
					import ez_setup
				except:
					print('failed to run setuptools installer.  The other installs will')
					print('probably fail.')
					return(87878787)
				else:
					ez_setup.main()
					

			else:
				rc = nm_install_package('python3-setuptools')
				if rc != 0:
					input('The installation of python setuptools failed.  This will ' \
						+ 'adversely affect installation of the Natural Message command ' \
						+ 'line client.  You can try to install Python setuptools ' \
						+ 'using your package manager and then rerun ' \
						+ 'NatMsgInstall.\n\nThe error code was: ' + repr(rc))

		if not os.path.isfile('/usr/bin/gcc') \
		and not os.path.isfile('/usr/local/bin/gcc') \
		and dist_name != 'freebsd':
			# bsd has gcc48 (or similar version), not gcc
			nm_install_package('gcc')

		if not os.path.isfile('/usr/bin/gcc') \
		and not os.path.isfile('/usr/local/bin/gcc') \
		and dist_name == 'freebsd':
			if not os.path.isfile('/usr/bin/gcc48') \
			and not os.path.isfile('/usr/local/bin/gcc48') \
				# bsd has gcc48 (or similar version), not gcc
				nm_install_package('gcc48')

			print('WARNING: I did not find the gcc program, but I will install')
			print('gcc48 if need be.  The FreeBSD install will not create a ')
			print('file called gcc, so you might want to create a soft link to ')
			print('the correct version of gcc:')
			print('  cd /usr/local/bin')
			print('  ln -s /usr/local/bin/gcc48 gcc')
			input('Press ENTER to continue...')

		if not os.path.isfile('/usr/bin/unrtf') \
		and not os.path.isfile('/usr/local/bin/unrtf') \
		and dist_name != 'freebsd':
			nm_install_package('unrtf') # removes rtf code for command line viewing


	########################################################################
	# These 'steps' are 'installation steps' involving the installation
	# intallation of tar.gz python distributions.
	steps = []
	save_rncryptor_subdir = '' 


	# Test if pycrypto is needed:
	if not platform.system().lower() == 'windows':
		# NOT Windows
		need_download = False
		try:
			from Crypto.Protocol import KDF
		except:
			need_download = True

		if need_download:
			print('I am adding pycrypto to the UNIX setup.')
			steps.append([wrk_dir, url_pycrypto, 'pycrypto', True, True])
		else:
			print('The pycrypto library is already installed.')

		# Test if requests is needed
		need_download = False
		try:
			import requests
		except:
			need_download = True

		if need_download:
			steps.append([wrk_dir, url_requests, 'requests', True, False])

			###steps.extend([[wrk_dir, url_requests, 'requests', True, False],
			###	[wrk_dir, url_rncryptor, 'rncryptor', False, False]])
		else:
			print('The Python requests library is already installed.')

	##### now running for all OS
	# always download a fresh natmsgcc from github, but
	# install the 'requests' module first.
	steps.append([wrk_dir, url_natmsgcc, 'natmsgcc', True, False])

	# get the fresh installer to faciliate running the latest install:
	steps.append([os.curdir, url_natmsgccInstall, 'natmsgccInstall', False, False])

	# 
	if dist_name == 'freebsd':
		# run ports install for textproc/unrtf, libgcrypt, gpg-error
		nm_popen(['make'], '/usr/ports/textproc/unrtf')
		nm_popen(['make', 'install'], '/usr/ports/textproc/unrtf')

		nm_popen(['make'], '/usr/ports/security/libgpg-error')
		nm_popen(['make', 'install'], '/usr/ports/security/libgpg-error')

		nm_popen(['make'], '/usr/ports/security/libgcrypt')
		nm_popen(['make', 'install'], '/usr/ports/security/libgcrypt')
	else:
		step_nbr = 1 #1-based step number
		for opts in steps:
			err_nbr, proj_subdir = install_targz_py(opts[0], opts[1], opts[2], 
				run_setup=opts[3], run_build=opts[4])
			if err_nbr != 0:
				# Error/warning
				print('WARNING.  There was an error intalling a tar.gz ' \
				+ 'file: ' + str(err_nbr))
				junk = input('Press ENTER to try the next step...')
				##sys.exit(12)
			else:
				if opts[2].lower() == 'rncryptor':
					save_rncryptor_subdir = proj_subdir

			step_nbr += 1

	#### I put RNCryptor inside natmsg
	### # To do: move the file to the official NaturalMessage python directory
	### # or to its own directory.
	### # Manually copy RNCryptor to the natmsg directory
	### rc = -1
	### src = os.path.join(save_rncryptor_subdir, 'RNCryptor.py')
	### dst = os.path.join(wrk_dir, 'RNCryptor.py')
	### ##dst = wrk_dir
	### 
	### print('source: ' + src + ' dst: ' + dst)
	### try:
	### 	shutil.copy2(src, dst) 
	### except:
	### 	print('Error. The final copy failed.  The RNCryptor.py file should ' \
	### 	+ 'be copied to ' + wrk_dir)


	###########################################################################
	###########################################################################
	# Fix permissions
	root_owner_found = False
	# to do: confirm owner ID
	if platform.system().lower() != 'windows':
		# first see if anything is owned by root
		for root, dirs, files in os.walk(wrk_dir):
			for f in files:
				if f == '':
					# check directory owner
					if os.stat(root).st_uid == 0:
						root_owner_found = True
						break
				else:
					# regular file
					fpath = os.path.join(root, f)
					print('checking ' + fpath)
					if os.stat(fpath).st_uid == 0:
						root_owner_found = True
						break
			if root_owner_found:
				break

		if root_owner_found:
			if os.getlogin() == 'root':
				print('WARNING, your mail directory contains files that are ' \
					+ 'owned by the root user ID and might not be accessible to ' \
					+ 'your regular user ID.  Your login ID is also set to root. ')

				owner_id_alpha = input('Enter the user ID that you want to be ' \
					+ 'the owner of your mail directory: ')

				owner_numeric_id = pwd.getpwnam(owner_id_alpha).pw_uid
				owner_gid = pwd.getpwnam(owner_id_alpha).pw_gid
			else:
				owner_numeric_id = pwd.getpwnam(os.getlogin()).pw_uid
				owner_gid = pwd.getpwnam(os.getlogin()).pw_gid


			for root, dirs, files in os.walk(wrk_dir):
				# Fix directory owner
				print( '==== fixing owner for directory ' \
						+ root + '. the dirs are ' + str(dirs))
				try:
					shutil.chown(root, 
						user=owner_numeric_id,
						group=owner_gid)
				except:
					chown_fail.append(root)

				for f in files:
					# Fix regular file owner
					fpath = os.path.join(root, f)
					try:
						shutil.chown(fpath, 
							user=owner_numeric_id,
							group=owner_gid)
					except:
						chown_fail.append(root)


	###########################################################################
	###########################################################################
	# download and install libgcrypt and libgpg-error as dependencies
	# of the Natural Message Server Verification programs (natmsgv
	# from https://github/naturalmessage/natmsgv)
	# Do not run this for FreeBSD, because I will use the ports tree.
	if platform.system().lower() != 'windows' and dist_name !='freebsd':
		#####  CONTINUING FOR NON-WINDOWS ONLY...                  ####
		#####  Download, configure, make, and install libgpg-error ####
		if os.path.isfile('/usr/local/lib/libgpg-error.a'):
			print('WARNING. You already have /usr/local/lib/libgpg-error.a.')
			print('I will not recompile that out of fear of putting the ')
			print('the wrong version of GPG on your system.')
			print('If you really want to recompile GPG, you can do so')
			print('manually')
		else:
			# gpg is not present, so continue
			rc, proj_dir = download_tar_bz2(wrk_dir, url_libgpg_error)
			
			if rc == 0:
				# configure
				### cd proj_dir
				print('Configuring libgpg_error...')
				rc = nm_open(['./configure', '--enable-static', 
					'--disable-shared', '--prefix=/usr/local'], proj_dir)
			
				if rc != 0:
					input('Error.  There was an error while configuring libgpg_error. ' \
						+ 'You might need to install a dependency.')
			
				# make
				print('Making libgpg_error...')
				pid = None
				rc = nm_popen(['make'], cwd=proj_dir)
			
				if rc != 0:
					input('Error.  There was an error while configuring libgpg_error. You might ' \
						+ 'need to install a dependency.')
			
				## # make install
				print('The libgpg-error modules are needed by the libgcrypt module.')
				yn = input('Do you want to install the libgpg-error programs now? (y/n): ')
				if yn.lower() in ['y', 'yes']:
					pid = None
					print('Installing libgpg_error...')
					rc = nm_popen(['make', 'install'], proj_dir)
					if rc != 0:
						print('The installation of libgpg_error failed.')
						input('Libgcrypt will not install without this.')
						return(4837434)
				else:
					print('Skipping the final installation for libgpg-error.')
			
		#####  Download, configure, make, and install libgcrypt ####
		if os.path.isfile('/usr/local/lib/libgcrypt.a'):
			print('WARNING. You already have /usr/local/lib/libgcrypt.a.')
			print('I will not recompile that out of fear of putting the ')
			print('the wrong version of GPG on your system.')
			print('If you really want to recompile GPG, you can do so')
			print('manually')
		else:
			# libgcrypt is not present, so continue
			rc, proj_dir = download_tar_bz2(wrk_dir, url_libgcrypt)
			
			if rc == 0:
				# configure
				### cd proj_dir
				print('Configuring libgcrypt...')
				# The next command defines the command and gets an id
				# for it.
				rc = nm_popen(['./configure', '--enable-static', 
					'--disable-shared',
					'--with-gpg-error-prefix=/usr/local',
					'--prefix=/usr/local'], proj_dir)
			
				if rc != 0:
					input('Error.  There was an error while configuring libgpgcrypt. ' \
						+ ' You might need to install a dependency.')
			
				# make
				print('Making libgcrypt...')
				rc = nm_popen(['make'], proj_dir)
			
				if rc != 0:
					input('Error.  There was an error while making libgcrypt.')
			
				# make install
				yn = input('Do you want to install the libgcrypt programs now? (y/n): ')
				if yn.lower() in ['y', 'yes']:
					print('Installing libgpg_error...')
					rc = nm_popen(['make', 'install'], proj_dir)

					sout, serr = pid.communicate()

					if pid.returncode != 0:
						print('Error.  There was an error while making libgcrypt. You might ')
						print('need to install a dependency.')
						if serr is not None:
							input('Press a key to see stderr error message...')
							print(str(serr))
							input('Press a key to continue ...')
				else:
					print('Skipping the final installation for libgcrypt.')
	#####  --------------------------------------------------- ####
	#####  --------------------------------------------------- ####
	#####  --------------------------------------------------- ####
	if platform.system().lower() != 'windows':
		# I NEED A SPECIAL SECTION FOR FREE BSD TO USE DYNAMIC LIBS
		# I NEED A SPECIAL SECTION FOR FREE BSD TO USE DYNAMIC LIBS
		# I NEED A SPECIAL SECTION FOR FREE BSD TO USE DYNAMIC LIBS
		# I NEED A SPECIAL SECTION FOR FREE BSD TO USE DYNAMIC LIBS
		# Install natmsgv (server verification programs)
		err_nbr, proj_subdir = install_targz_py(wrk_dir, url_natmsgv_gz, 'natmsgv-master',
			False, False)
		if err_nbr != 0:
			# Error/warning
			print('Error.  There was an error intalling the serverv verification tar.gz ' \
			+ 'file: ' + str(err_nbr))
		else:
			print('The natmsgv server verification program source code was downloaded OK.')

			if dist_name == 'freebsd':
				# rename the Makefile
				mfile = os.path.join(wrk_dir, 'natmsgv-master', 'Makefile')
				fbsd_file= os.path.join(wrk_dir, 'natmsgv-master', 'MakefileFreeBSD')

				os.remove(mfile)
				shutil.move(fbsd_file, mfile)

			# run make and install
			rc = nm_popen(['make', 'nm_verify'], os.path.join(wrk_dir, 'natmsgv-master'))

			if rc != 0:
				input('Error.  There was an error while making natmsgv. You might ' \
					+ 'need to install a dependency.')
			else:
				# install it
				rc = nm_popen(['make', 'install'], os.path.join(wrk_dir, 'natmsgv-master'))

				if rc != 0:
					input('Error.  There was an error while installing nm_verify. You might ' \
						+ 'need to install a dependency.')

	if len(chown_fail) > 0:
		print('There was a problem trying to fix the ownership of ')
		print('one or more directories.')
		print('You can fix them from the command line when you know')
		print('which user you want to own it.')
		for f in chown_fail:
			print(f)
	return(0)
######################################################################
######################################################################
if __name__ == '__main__':
	main()

