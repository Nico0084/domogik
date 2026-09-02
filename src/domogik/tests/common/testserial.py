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

Purpose
=======

Tools for regression tests

Usage
=====

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import time
import binascii
import json
import traceback
import sys
import os
import pwd
from domogik.common.defaultloader import DefaultLoader
from domogik.common import logger

### for compatibility
# taken from /usr/lib/python2.7/dist-packages/serial/serialutil.py

def to_bytes(seq):
    """convert a sequence to a bytes type"""
    b = bytearray()
    for item in seq:
        b.append(item)  # this one handles int and str
    return bytes(b)

# create control bytes
XON  = to_bytes([17])
XOFF = to_bytes([19])

CR = to_bytes([13])
LF = to_bytes([10])

PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE = 'N', 'E', 'O', 'M', 'S'
STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO = (1, 1.5, 2)
FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS = (5, 6, 7, 8)

### end compatibility



class SerialException(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class Serial():
    """ serial mock
    """

    def __init__(self, port, baudrate = None, bytesize = None, parity = None, stopbits = None, timeout = None, xonxoff = None, rtscts = None, writeTimeout = None, dsrdtr = None, interCharTimeout = None):
        """ Construtor
            @param port : the json file with the fake data
            @param baudrate : useless, just for compatibility
            @param bytesize : useless, just for compatibility
            @param parity : useless, just for compatibility
            @param stopbits : useless, just for compatibility
            @param timeout : useless, just for compatibility
            @param ... : useless, just for compatibility
        """
        default = DefaultLoader()
        dmg_user = default.get("DOMOGIK_USER")
        logname = pwd.getpwuid(os.getuid())[0]
        if dmg_user != logname:
            self.log.error(u"This Domogik part must be run with the user defined in /etc/default/domogik as DOMOGIK_USER : {0}".format(dmg_user))
            sys.exit(1)
        name = "serialmock"
        logg = logger.Logger(name, use_filename="{0}_{1}".format('test', name), log_on_stdout=True)
        self.log = logg.get_logger(name)

        self.log.info(u"Fake serial device created. The fake data in the file '{0}' will be used".format(port))
        # load the json file
        try:
            json_fp = open(port)
            self.data = json.load(json_fp)
            json_fp.close()
        except:
            self.log.error(u"Error while opening fake serial device from file {0} : {1}".format(port, traceback.format_exc()))
            raise SerialException(u"Error while opening fake serial device from file {0} : {1}".format(port, traceback.format_exc()))

        # read index
        self.history_idx = 0
        # loop index
        self.loop_idx = 0

        # set a flag for the first read
        self.first_read = 30

        # set the next_response (used by write function) to None
        self.next_responses = []

        # Time to wait an action
        self.waiting = 0

    def flush(self):
        pass

    def close(self):
        pass

    def reset_output_buffer(self):
        pass

    def write(self, data):
        """ Mock for input data on the serial device
            respond with the appropriate answers depending on what has been write to the fake serial device
        """

        found = False
        self.log.info(u"Receive input data {0}".format(repr(data)))
        for mock in self.data['responses']:
            if mock['type'] == "data":
                if data == mock['when']:
                    found = True
                    responses = mock['do']
                    data_for_log = data
            elif mock['type'] == "data-hex":
                if binascii.hexlify(data).lower() == mock['when'].lower():
                    found = True
                    responses = mock['do']
                    data_for_log = binascii.hexlify(data)
        if found:
            self.log.info(u"Found mock responses for data written : {0}. Response is {1}".format(data_for_log, responses))
            self.next_responses.extend(responses)
        else:
            self.log.warning("No mock response find !")

    def readline(self, length = 1):
        return self.read(length)

    def read(self, length = 1):
        """ Mock the read feature
            @param length : length of the data to read. For compatibility only
        """
        if self.first_read <> 0 :
            # first, wait for x seconds (default 30)
            # this allows to be sure that the plugin is fully ready before using the fake serial device
            self.log.info("Before the first read, we wait for {0} seconds to run history and loop...".format(self.first_read))
            self.waiting = time.time() + self.first_read
            self.first_read = 0

        # handle a response to a write action
        if self.next_responses != []:
            response = self.next_responses[0]
            if response['type'] == "data-hex":
                data = binascii.unhexlify(response['data'])
                self.log.info(u"Action {0} = reply to a write action / Delay = {1} / Data = {2}".format(response['type'], response['delay'], data))
            elif response['type'] == "data":
                self.log.info(u"Action {0} = reply to a write action / Delay = {1} / Data = {2}".format(response['type'], response['delay'], repr(response['data'])))
                data = response['data']

            time.sleep(int(response['delay']))
            # remove first item from the responses list
            self.next_responses.pop(0)
            return data

        # Handle wait action without blocking responses
        if time.time() < self.waiting :
            time.sleep(0.2)
        else :
            # handle the history part
            if self.history_idx < len(self.data['history']):
                action = self.data['history'][self.history_idx]['action']
                description = self.data['history'][self.history_idx]['description']
                self.log.info(u"Action = {0} / Description = {1}".format(action, description))
                if action == 'data':
                    value = self.data['history'][self.history_idx]['data']
                    self.log.info(u"Extrated from history {0}. Return : {1} ".format(action, value))
                    self.history_idx += 1
                    return value
                elif action == 'data-hex':
                    value = binascii.unhexlify(self.data['history'][self.history_idx]['data'])
                    self.log.info(u"Extrated from history {0}. Return : {1} ".format(action, value))
                    self.history_idx += 1
                    return value
                elif action == 'wait':
                    delay = self.data['history'][self.history_idx]['delay']
                    self.log.info(u" => History wait for {0}s".format(delay))
                    self.history_idx += 1
                    self.waiting = time.time() + delay
                else:
                    self.log.warning(u"Unkwown action : {0}".format(action))
                    self.history_idx += 1
            # and if the history is finished, handle the loop
            else:
                if self.data['loop'] == []:
                    self.log.info(u"There is nothing else to read in the fake serial device")
                    raise SerialException(u"There is nothing else to read in the fake serial device")
                else:
                    if self.history_idx == len(self.data['history']):
                        self.log.info("The history has ended. Now we start the loop")
                        self.history_idx += 1
                    if self.loop_idx == len(self.data['loop']):
                        self.loop_idx = 0
                    action = self.data['loop'][self.loop_idx]['action']
                    description = self.data['loop'][self.loop_idx]['description']
                    self.log.info(u"From loop action = {0} / Description = {1}".format(action, description))
                    if action == 'data':
                        value = self.data['loop'][self.loop_idx]['data']
                        self.log.info(u"Extrated from loop {0}. Return : {1} ".format(action, value))
                        self.loop_idx += 1
                        return value
                    elif action == 'data-hex':
                        value = binascii.unhexlify(self.data['loop'][self.loop_idx]['data'])
                        self.log.info(u"Extrated from loop {0}. Return : {1} ".format(action, value))
                        self.loop_idx += 1
                        return value
                    elif action == 'wait':
                        delay = self.data['loop'][self.loop_idx]['delay']
                        self.log.info(u" => wait for {0}s".format(delay))
                        self.loop_idx += 1
                        self.waiting = time.time() + delay
                    else:
                        self.log.warning(u"Unkwown action : {0}".format(action))
                        self.loop_idx += 1
        return

if __name__ == "__main__":

    #my_mock = Serial("/media/stock/domotique/git/domogik-plugin-rfxcom/tests/352_data.json")
    my_mock = Serial("/media/stock/domotique/git/domogik-plugin-teleinfo/tests/tests_hphc_data.json")
    while True:
        #my_mock.read()
        my_mock.readline()


