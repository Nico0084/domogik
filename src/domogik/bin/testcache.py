# -*- coding: utf-8 -*-

from multiprocessing.managers import SyncManager
from domogik.bin.cachedb import WorkerCache, CACHE_NAME

from subprocess import Popen
from threading import Thread

import os
import sys
import traceback

PYTHON = sys.executable

class DeviceCache(SyncManager):
    pass

class Manager(object):

    def __init__(self):
        print(u"Manager init cache")
        self._cache_pid = None
        thr__runCacheDevices = Thread(None,
                                      self._runCacheDevices,
                                      "run_cache_devices",
                                      (),
                                      {})
        thr__runCacheDevices.start()
#        self.__cacheData = WorkerCache()
        print(u"Manager instanciate cache")

    def _runCacheDevices(self):
        print(u"Manager run cache")
#        self.__cacheData = WorkerCache()
#        self.log.info(u"Cache running")
        self._pid_dir_path = ""
        try:
            the_path = os.path.join(os.path.dirname(__file__), "{0}.py".format(CACHE_NAME))
            print(u"Path for component '{0}' is : {1}".format(CACHE_NAME, the_path))
        except:
            msg = u"Error while trying to get the module path. The component will not be started !. Error is : {0}".format(traceback.format_exc())
            print(msg)
            return 0

        ### Generate command
        # we add the STARTED_BY_MANAGER useless command to allow the plugin to ignore this command line when it checks if it is already laucnehd or not
#        cmd = "{0} && {1} {2}".format(STARTED_BY_MANAGER, PYTHON, the_path)
        cmd = "{0} {1}".format(PYTHON, the_path)

        ### Execute command
        print(u"Execute command : {0}".format(cmd))
        subp = Popen(cmd,
                     shell=True)
        self._cache_pid = subp.pid
        print(u"Cache running on pid {0}".format(self._cache_pid))
#        subp.communicate()
        pid_file = os.path.join(self._pid_dir_path,
                                CACHE_NAME + ".pid")
        print(u"Write pid file for pid '{0}' in file '{1}'".format(str(self._cache_pid), pid_file))
        fil = open(pid_file, "w")
        fil.write(str(self._cache_pid))
        fil.close()

    def force_leave(self, status = False, return_code = None):
        if self._cache_pid is not None :
            DeviceCache.register('force_leave')
            m = DeviceCache(address=('', 40409), authkey=b'abracadabra')
            m.connect()
            print(u"force_leave called. Exit to memory devices cache {0}".format(m))
            # Actually Killing all subProcess. Not really academic, but I d'ont find other way ! and raise an exception."
            try :
                m.force_leave()
            except :
                pass

if __name__ == '__main__':
    cacheManager = Manager()
    raw_input("return to end")
    cacheManager.force_leave()

