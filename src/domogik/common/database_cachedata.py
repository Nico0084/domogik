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

Module purpose
==============

Miscellaneous utility database functions

Implements
==========


@author: Nicolas VIGNAL <nic84dev at gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.plugin import Plugin
from domogik.common import logger
from threading import Lock, RLock
import inspect

class Singleton(type):
    """ Singleton metaclass
    """
    def __init__(self, *args, **kwargs):
        """ Init the metaclass
        @ivar __instances: instance of the class
        @type __instance: object
        """
        super(Singleton, self).__init__(*args, **kwargs)

        self.__instance = None

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super(Singleton, self).__call__(*args, **kwargs)
        return self.__instance

class CacheDevicesList(Plugin):

    __metaclass__ = Singleton

#    _lockBuild = Lock()
#    _instance = None

    _access = RLock()
    _devices_list = []
    _to_update_device = {}
#    _log = None

    def __init__(self):
        if self.log is None :
#            l = logger.Logger("core_cachedevice", log_on_stdout=True)
#            self.log = l.get_logger("core_cachedevice")
            self.log.info("Init cache done :{0}".format(self))
            self.log.debug("{0}".format(inspect.stack()))
        else :
            self.log.debug(u"This is a Singleton! Not do Init part method")
        self.log.info("Cache instance {0} init call finish.".format(self))

#    def __new__(cls):
#        if cls._instance is None:
#            with cls._lockBuild:
#                if cls._instance is None:
#                    cls._instance = object.__new__(cls)
#        return cls._instance

    def devices_list(self, client_id = None):
        with self._access :
            self.log.debug(u"Read cache with {0} device ({1})".format(len(self._devices_list), self))
            if client_id is not None :
                devices_list = []
                for dev in self._devices_list:
                    if dev['client_id'] == client_id :
                      devices_list.append(dict(dev))
                return devices_list
            else :
                return list(self._devices_list)

    def uptodate(self, client_id = None, device_id = None):
        with self._access :
            if device_id is not None :
                if device_id in self._to_update_device :
                    return not self._to_update_device[device_id]
                else :
                    return False
            elif client_id is not None :
                exist = False
                for dev in self._devices_list:
                    if dev['client_id'] == client_id :
                        exist = True
                        uptodate = not self._to_update_device[dev['id']]
                        if not uptodate: return False
                return exist
            else :
                if self._devices_list is None or self._devices_list == []:
                    self.log.debug(u"Cache not updated ({0})".format(self))
                    return False
                for dev in self._devices_list:
                    uptodate = not self._to_update_device[dev['id']]
                    if not uptodate: return False
                return True
        return False

    def setData(self, device_list):
        with self._access :
            self._devices_list = device_list
            self._to_update_device = {}
            for dev in self._devices_list:
                self._to_update_device[dev['id']] = False
            self.log.debug(u"Set cache with {0} device ({1})".format(len(self._devices_list), self))

    def updateData(self, device_list, client_id = None, device_id = None):
        with self._access :
            if device_id is not None : # Update one device of device_list
                for dev in list(self._devices_list):
                    if dev['id'] == device_id :
                        dev = device_list
                        self._to_update_device[dev['id']] = False
                        break
            elif client_id is not None : # Update by client
                for dev in list(self._devices_list):
                    # 1st remove all devices for client (assume deleted device)
                    if dev['client_id'] == client_id :
                        self._devices_list.remove(dev)
                        del(self._to_update_device[dev['id']])
                self._devices_list.extend(device_list)
                for dev in device_list :
                    self._to_update_device[dev['id']] = False
            else : #  Update all devices of device_list
                for dev_n in device_list :
                    for dev in self._devices_list :
                        if dev['id'] == dev_n['id'] :
                            dev = dev_n
                            self._to_update_device[dev['id']] = False
            self.log.debug(u"Update cache with {0} device, mode : {1}/{2} ({3})".format(len(device_list), client_id, device_id, self))

    def mark_as_updating(self, client_id = None, device_id = None, sensor_id = None):
        with self._access :
            if sensor_id is not None :
                for dev in self._devices_list :
                    for key in dev['sensors'] :
                        if dev['sensors'][key]['id'] == sensor_id :
                            self._to_update_device[dev['id']] = True
                            break
            elif device_id is not None : # Mark one device
                for dev in self._devices_list :
                    if dev['id'] == device_id :
                        self._to_update_device[dev['id']] = True
                        break
            elif client_id is not None : # Mark devices by client
                for dev in self._devices_list:
                    if dev['client_id'] == client_id :
                        self._to_update_device[dev['id']] = True
            else : #  Mark all devices
                for dev_n in self._devices_list :
                    self._to_update_device[dev['id']] = True
            self.log.debug(u"Mark to update cache mode : {0}/{1}/{2} ({3})".format(client_id, device_id, sensor_id, self))

if __name__ == '__main__':
    CacheDevicesList()
