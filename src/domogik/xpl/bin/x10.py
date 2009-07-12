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

Module purpose
==============

xPL X10 client

Implements
==========

- x10Main.__init__(self)
- x10Main.x10_cmnd_cb(self, message)
- x10Main.x10_monitor_cb(self, unit, order, args = None)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.lib.x10 import *
from domogik.xpl.lib.xplconnector import *
from domogik.xpl.lib.module import *
from domogik.common.configloader import Loader
from domogik.common import logger
from domogik.xpl.lib.queryconfig import *

class x10Main(xPLModule):

    def __init__(self):
        '''
        Create the X10Main class
        This class is used to connect x10 (through heyu) to the xPL Network
        '''
        xPLModule.__init__(self, name = 'x10')
        self.__myxpl = Manager()
        self._config = Query(self.__myxpl)
        res = xPLResult()
        self._config.query('x10', 'heyu_cfg_path', res)
        try:
            self.__myx10 = X10API(res.get_value())
        except:
            print "Something went wrong during heyu init, check logs"
            exit(1)
        #Create listeners
        Listener(self.x10_cmnd_cb, self.__myxpl, {'schema': 'x10.basic',
                'type': 'xpl-cmnd'})
        self._log = self.get_my_logger()
        self._monitor = X10Monitor(res.get_value())
        self._monitor.get_monitor().add_cb(self.x10_monitor_cb)
        self._monitor.get_monitor().start()
        self._log.debug("Heyu correctly started")

    def x10_cmnd_cb(self, message):
        '''
        General callback for all command messages
        '''
        commands = {
            'on': lambda d, h, l: self.__myx10.on(d),
            'off': lambda d, h, l: self.__myx10.off(d),
            'all_units_on': lambda d, h, l: self.__myx10.house_on(h),
            'all_units_off': lambda d, h, l: self.__myx10.house_off(h),
            'all_lights_on': lambda d, h, l: self.__myx10.lights_on(h),
            'all_lights_off': lambda d, h, l: self.__myx10.lights_off(h),
            'bright': lambda d, h, l: self.__myx10.bright(d, l),
            'dim': lambda d, h, l: self.__myx10.dim(d, l),
            'brightb': lambda d, h, l: self.__myx10.bright(d, l),
            'dimb': lambda d, h, l: self.__myx10.dim(d, l),
        }
        cmd = None
        dev = None
        house = None
        level = None
        if 'command' in message:
            cmd = message.get_key_value('command')
        if 'device' in message:
            dev = message.get_key_value('device')
        if 'house' in message:
            house = message.get_key_value('house')
        if 'level' in message:
            level = message.get_key_value('level')
        self._log.debug("%s received : device = %s, house = %s, level = %s" % (
                cmd, dev, house, level))
        commands[cmd](dev, house, level)

    def x10_monitor_cb(self, unit, order, args = None):
        """
        Callback for x10 monitoring
        @param unit : the unit of the element controled
        @param order : the order sent to the unit
        """
        self._log.debug("X10 Callback for %s" % unit)
        mess = Message()
        mess.set_type("xpl-trig")
        mess.set_schema("x10.basic")
        mess.set_data_key("device", unit)
        mess.set_data_key("command", order)
        if args:
            mess.set_data_key("level",args)
        print mess
        self.__myxpl.send(mess)

if __name__ == "__main__":
    x = x10Main()
