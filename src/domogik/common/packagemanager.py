#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Package manager for domogik
A package could be a plugin, a web ui widget, etc

Implements
==========

TODO

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.packagexml import PackageXml, PackageException
from domogik.common.packagedata import PackageData
from domogik.common.configloader import Loader
from xml.dom import minidom
import traceback
import tarfile
import tempfile
import os
import pwd
from subprocess import Popen
import urllib
import shutil
from domogik.common import logger


SRC_PATH = "../../../"
PLG_XML_PATH = "src/share/domogik/plugins/"
TMP_EXTRACT_DIR = "domogik-pkg-mgr" # used with /tmp (or assimilated) before
CONFIG_FILE = "%s/.domogik/domogik.cfg" % os.getenv("HOME")
REPO_SRC_FILE = "%s/.domogik/sources.list" % os.getenv("HOME")
REPO_LST_FILE = "packages.lst"
REPO_LST_FILE_HEADER = "Domogik repository"
REPO_CACHE_DIR = "%s/.domogik/cache" % os.getenv("HOME")
INSTALL_PATH = "%s/.domogik/" % os.getenv("HOME")
PLUGIN_XML_PATH = "%s/plugins/plugins" % INSTALL_PATH


class PackageManager():
    """ Tool to create packages
    """

    def __init__(self):
        """ Init tool
        """
        l = logger.Logger("package-manager")
        self._log = l.get_logger("package-manager")

    def log(self, message):
        """ Log and print message
            @param message : data to log
        """
        self._log.info(message)
        print(message)


    def _create_package_for_plugin(self, name, output_dir, force):
        """ Create package for a plugin
            1. read xml file to get informations and list of files
            2. generate package
            @param name : name of plugin
            @param output_dir : target directory for package
            @param force : False : ask for confirmation
        """
        self.log("Plugin name : %s" % name)

        try:
            plg_xml = PackageXml(name)
        except:
            self.log(str(traceback.format_exc()))
            return
        self.log("Xml file OK")

        # check type == plugin
        if plg_xml.type != "plugin":
            self.log("Error : this package is not a plugin")
            return

        # display plugin informations
        plg_xml.display()

        # check file existence
        if plg_xml.files == []:
            self.log("There is no file defined : the package won't be created")
            return

        if force == False:
            self.log("\nAre these informations OK ?")
            resp = raw_input("[o/N]")
            if resp.lower() != "o":
                self.log("Exiting...")
                return

        # Create .tgz
        self._create_tar_gz("plugin-%s-%s" % (plg_xml.name, plg_xml.release), 
                            output_dir,
                            plg_xml.files, 
                            plg_xml.info_file)


    def _create_tar_gz(self, name, output_dir, files, info_file = None):
        """ Create a .tar.gz file anmmed <name.tgz> which contains <files>
            @param name : file name
            @param output_dir : if != None, the path to put .tar.gz
            @param files : table of file names to add in tar.gz
            @param info_file : path for info.xml file
        """
        if output_dir == None:
            my_tar = "%s/%s.tgz" % (tempfile.gettempdir(), name)
        else:
            my_tar = "%s/%s.tgz" % (output_dir, name)
        self.log("Generating package : '%s'" % my_tar)
        try:
            tar = tarfile.open(my_tar, "w:gz")
            for my_file in files:
                path =  str(my_file["path"])
                self.log("- %s" % path)
                tar.add(SRC_PATH + path, arcname = path)
            if info_file != None:
                self.log("- info.xml")
                tar.add(info_file, arcname="info.xml")
            tar.close()
        except: 
            msg = "Error generating package : %s : %s" % (my_tar, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)
        self.log("OK")
    

    def install_package(self, path, release = None):
        """ Install a package
            0. Eventually download package
            1. Extract tar.gz
            2. Install package
            3. Insert data in database
            @param path : path for tar.gz
        """
        #if self.is_root() == False:
        #    self.log("-i option must be used as root")
        #    return
        # package from repository
        if path[0:5] == "repo:":
            pkg, status = self._find_package(path[5:], release)
            if status != True:
                return status
            path = pkg.package_url

        # get plugin name
        full_name = os.path.basename(path)

        # twice to remove first .gz and then .tar
        name =  os.path.splitext(full_name)[0]
        name =  os.path.splitext(name)[0] 
        self.log("Plugin name : %s" % name)

        # get temp dir to extract data
        my_tmp_dir_dl = "%s/%s" % (tempfile.gettempdir(), TMP_EXTRACT_DIR)
        my_tmp_dir = "%s/%s" % (my_tmp_dir_dl, name)
        self.log("Creating temporary directory : %s" % my_tmp_dir)
        try:
            if os.path.isdir(my_tmp_dir) == False:
                os.makedirs(my_tmp_dir)
        except:
            msg = "Error while creating temporary folder '%s' : %s" % (INSTALL_PATH, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)

        # Check if we need to download package
        if path[0:4] == "http":
            self.log("Downloading package : %s" % path)
            dl_path = "%s/%s" % (my_tmp_dir_dl, full_name)
            urllib.urlretrieve(path, dl_path)
            path = dl_path
            self.log("Package downloaded : %s" % path)

        # extract in tmp directory
        self.log("Extracting package...")
        try:
            self._extract_package(path, my_tmp_dir)
        except:
            msg = "Error while extracting package '%s' : %s" % (path, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)
        self.log("Package successfully extracted.")

        # create install directory
        self.log("Creating install directory : %s" % INSTALL_PATH)
        try:
            if os.path.isdir(INSTALL_PATH) == False:
                os.makedirs(INSTALL_PATH)
        except:
            msg = "Error while creating installation folder '%s' : %s" % (INSTALL_PATH, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)

        # install plugin in $HOME
        self.log("Installing package (plugin)...")
        try:
            self._install_plugin(my_tmp_dir, INSTALL_PATH)
        except:
            msg = "Error while installing package : %s" % (traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)
        self.log("Package successfully extracted.")

        # insert data in database
        pkg_data = PackageData("%s/info.xml" % my_tmp_dir, custom_path = CONFIG_FILE)
        pkg_data.insert()

        self.log("Package installation finished")
        return True


    def _extract_package(self, pkg_path, extract_path):
        """ Extract package <pkg_path> in <extract_path>
            @param pkg_path : path to package
            @param extract_path : path for extraction
        """
        tar = tarfile.open(pkg_path)
        # check if there is no .. or / in files path
        for fic in tar.getnames():
            if fic[0:1] == "/" or fic[0:2] == "..":
                msg = "Error while extracting package '%s' : filename '%s' not allowed" % (pkg_path, fic)
                self.log(msg)
                raise PackageException(msg)
        tar.extractall(path = extract_path)
        tar.close()


    def _install_plugin(self, pkg_dir, install_path):
        """ Install plugin
            @param pkg_dir : directory where package is extracted
            @param install_path : path where we install packages
        """

        ### create needed directories
        # create install directory
        self.log("Creating directories for plugin...")
        plg_path = "%s/plugins/" % install_path
        try:
            if os.path.isdir(plg_path) == False:
                os.makedirs(plg_path)
        except:
            msg = "Error while creating plugin folder '%s' : %s" % (plg_path, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)

        ### copy files
        self.log("Copying files for plugin...")
        try:
            copytree("%s/src/domogik/xpl" % pkg_dir, "%s/xpl" % plg_path, self.log)
            self._create_init_py("%s/xpl/" % plg_path)
            self._create_init_py("%s/xpl/bin/" % plg_path)
            self._create_init_py("%s/xpl/lib/" % plg_path)
            copytree("%s/src/share/domogik" % pkg_dir, "%s/" % plg_path, self.log)
        except:
            msg = "Error while copying plugin files : %s" % (traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)

    def _create_init_py(self, path):
        """ Create __init__.py file in path
            param path : path where we wan to create the file
        """
        try:
            self.log("Create __init__.py file in %s" % path)
            open("%s/__init__.py" % path, "a").close()
        except:
            msg = "Error while crating __init__.py file in %s : %s" % (path, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)



    def update_cache(self):
        """ update local package cache
        """
        # Get repositories list
        try:
            # Read repository source file and generate repositories list
            repo_list = self.get_repositories_list()
        except:
            self.log(str(traceback.format_exc()))
            return False
             
        # Clean cache folder
        try:
            self._clean_cache(REPO_CACHE_DIR)
        except:
            self.log(str(traceback.format_exc()))
            return False
             
        # for each list, get files and associated xml
        try:
            self._parse_repository(repo_list, REPO_CACHE_DIR)
        except:
            self.log(str(traceback.format_exc()))
            return False

        return True

    def get_repositories_list(self):
        """ Read repository source file and return list
        """
        try:
            repo_list = []
            src_file = open(REPO_SRC_FILE, "r")
            for line in src_file.readlines():
                repo_list.append({"priority" : line.split()[0],
                                  "url" : line.split()[1]})
            src_file.close()
        except:
            msg = "Error reading source file : %s : %s" % (REPO_SRC_FILE, str(traceback.format_exc()))
            self.log(msg)
            raise PackageException(msg)
        # return sorted list
        return sorted(repo_list, key = lambda k: k['priority'], reverse = True)


    def _clean_cache(self, folder):
        """ If not exists, create <folfer>
            Then, clean this folder
            @param folder : cache folder to empty
        """
        # Create folder
        try:
            if os.path.isdir(folder) == False:
                os.makedirs(folder)
        except:
            msg = "Error while creating cache folder '%s' : %s" % (folder, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)

        # Clean folder
        try:
            for root, dirs, files in os.walk(folder):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
        except:
            msg = "Error while cleaning cache folder '%s' : %s" % (folder, traceback.format_exc())
            self.log(msg)
            raise PackageException(msg)


    def _parse_repository(self, repo_list, cache_folder):
        """ For each repo, get file list, check if it is higher release and
            get package's xml
            @param repo_list : repositories list
            @param cache_folder : package cache folder
        """
        package_list = []

        # get all packages url
        file_list = []
        for repo in repo_list:
            file_list.extend(self._get_files_list_from_repository(repo["url"], repo["priority"]))

        # for each package, put it in cache if higher release
        for file_info in file_list:
            pkg_xml = PackageXml(url = "%s.xml" % file_info["file"])
            self.log("Add '%s (%s)' in cache from %s" % (pkg_xml.name, pkg_xml.release, file_info["repo_url"]))
            pkg_xml.cache_package(cache_folder, file_info["file"], file_info["priority"])


    def _get_files_list_from_repository(self, url, priority):
        """ Read packages.xml on repository
            @param url : repo url
            @param prioriry : repo priority
        """
        try:
            resp = urllib.urlopen("%s/%s" % (url, REPO_LST_FILE))
            my_list = []
            first_line = True
            for data in resp.readlines():
                if first_line == True:
                    first_line = False
                    if data.strip() != REPO_LST_FILE_HEADER:
                        self.log("This is not a Domogik repository : '%s/%s'" %
                                   (url, REPO_LST_FILE))
                        break
                else:
                    my_list.append({"file" : "%s/%s" % (url, data.strip()),
                                    "priority" : priority,
                                    "repo_url" : url})
            return my_list
        except IOError:
            self.log("Bad url :'%s/%s'" % (url, REPO_LST_FILE))
            return []


    def list_packages(self):
        """ List all packages in cache folder 
            Used for printing on command line
        """
        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for f in files:
                pkg_xml = PackageXml(path = "%s/%s" % (root, f))
                pkg_list.append({"fullname" : pkg_xml.fullname,
                                 "release" : pkg_xml.release,
                                 "priority" : pkg_xml.priority,
                                 "desc" : pkg_xml.desc})
        pkg_list =  sorted(pkg_list, key = lambda k: (k['fullname'], 
                                                      k['release']))
        for pkg in pkg_list:
             self.log("%s (%s, prio: %s) : %s" % (pkg["fullname"], 
                                               pkg["release"], 
                                               pkg["priority"], 
                                               pkg["desc"]))

    def get_packages_list(self):
        """ List all packages in cache folder 
            and return a detailed list
            Used by Rest
        """
        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for f in files:
                pkg_xml = PackageXml(path = "%s/%s" % (root, f))
                pkg_list.append({"name" : pkg_xml.name,
                                 "type" : pkg_xml.type,
                                 "fullname" : pkg_xml.fullname,
                                 "release" : pkg_xml.release,
                                 "genrated" : pkg_xml.generated,
                                 "techno" : pkg_xml.techno,
                                 "doc" : pkg_xml.doc,
                                 "desc" : pkg_xml.desc,
                                 "detail" : pkg_xml.detail,
                                 "author" : pkg_xml.author,
                                 "email" : pkg_xml.email,
                                 "priority" : pkg_xml.priority,
                                 "package-url" : pkg_xml.package_url})
        return sorted(pkg_list, key = lambda k: (k['name']))

    def get_installed_packages_list(self):
        """ List all packages in install folder 
            and return a detailed list
        """
        pkg_list = []
        for root, dirs, files in os.walk(PLUGIN_XML_PATH):
            for f in files:
                pkg_xml = PackageXml(path = "%s/%s" % (root, f))
                pkg_list.append({"fullname" : pkg_xml.fullname,
                                 "name" : pkg_xml.name,
                                 "release" : pkg_xml.release,
                                 "type" : pkg_xml.type,
                                 "package-url" : pkg_xml.package_url})
        return sorted(pkg_list, key = lambda k: (k['fullname'], 
                                                 k['release']))

    def show_packages(self, fullname, release = None):
        """ Show a package description
            @param fullname : fullname of package (type-name)
            @param release : optionnal : release to display (if several)
        """
        pkg, status = self._find_package(fullname, release)
        if status == True:
            pkg.display()


    def _find_package(self, fullname, release = None):
        """ Find a package and return 
                               - xml data or None if not found
                               - a status : True if ok, a message elsewhere
            @param fullname : fullname of package (type-name)
            @param release : optionnal : release to display (if several)
        """
        pkg_list = []
        for root, dirs, files in os.walk(REPO_CACHE_DIR):
            for f in files:
                pkg_xml = PackageXml(path = "%s/%s" % (root, f))
                if release == None:
                    if fullname == pkg_xml.fullname:
                        pkg_list.append({"fullname" : pkg_xml.fullname,
                                         "release" : pkg_xml.release,
                                         "priority" : pkg_xml.priority,
                                         "xml" : pkg_xml})
                else:
                    if fullname == pkg_xml.fullname and release == pkg_xml.release:
                        pkg_list.append({"fullname" : pkg_xml.fullname,
                                         "release" : pkg_xml.release,
                                         "priority" : pkg_xml.priority,
                                         "xml" : pkg_xml})
        if len(pkg_list) == 0:
            if release == None:
                release = "*"
            msg = "No package corresponding to '%s' in release '%s'" % (fullname, release)
            self.log(msg)
            return [], msg
        if len(pkg_list) > 1:
            msg = "Several packages are available for '%s'. Please specify which release you choose" % fullname
            self.log(msg)
            for pkg in pkg_list:
                 self.log("%s (%s, prio: %s)" % (pkg["fullname"], 
                                              pkg["release"],
                                              pkg["priority"]))
            return [], msg

        return pkg_list[0]["xml"], True

    def is_root(self):
        """ return True is current user is root
        """
        if pwd.getpwuid(os.getuid())[0] == "root":
            return True
        return False


##### shutil.copytree fork #####
# the fork is necessary because original function raise an error if a directory
# already exists. In our case, some directories will exists!

class Error(EnvironmentError):
    pass

try:
    WindowsError
except NameError:
    WindowsError = None


def copytree(src, dst, cb_log):
    """Recursively copy a directory tree using copy2().

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)

    try:
        os.makedirs(dst)
    except OSError as (errno, strerror):
        if errno == 17:
            pass
        else:
            raise
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        cb_log("%s => %s" % (srcname, dstname))
        try:
            if os.path.isdir(srcname):
                copytree(srcname, dstname, cb_log)
            else:
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error, err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except OSError, why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error, errors
    



