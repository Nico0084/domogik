#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: mschneider $
# $LastChangedDate: 2009-02-01 10:21:50 +0100 (dim. 01 févr. 2009) $
# $LastChangedRevision: 300 $

#This script use arguments from command line to forge & send a message
from xPLAPI import *
import optparse

class Sender:

    supported_schemas = ["datetime.basic","dawndusk.request","x10.basic","sensor.basic"]

    def __init__(self):
        self.parse_parameters()
        print "Create Manager"
        self.__myxpl = Manager(ip = "192.168.1.24", port  = 5037)
        print "Forge message"
        mess = self.forge_message()
        print "send message"
        self.__myxpl.send(mess)
        print "leave"
        self.__myxpl.leave()
        exit(0)

    def parse_parameters(self):
        '''
        Read parameters from command line and parse them
        '''
        parser = optparse.OptionParser()
        parser.add_option("-d","--dest",type="string",dest="message_dest", default="broadcast")
        (self._options, self._args) = parser.parse_args()

        #Parsing of args
        if len(self._args) != 2:
            self.usage()
            exit(1)

        if self._args[0] not in self.supported_schemas:
            print "Schema not supported"
            self.usage()
            exit(2)

    def forge_message(self):
        '''
        Create the message based on script arguments
        '''
        message = Message()
        message.set_type("xpl-cmnd")
        message.set_schema(self._args[0])
        datas = self._args[1].split(',')
        for data in datas:
            if "=" not in data:
                print "Bad formatted commands\n Must be key=value"
                self.usage()
                exit(4)
            else:
                message.set_data_key(data.split("=")[0], data.split("=")[1])
        return message

    def usage(self):
        print "usage : send.py message_type message_contents"
        print "\tmessage_type : Type of the message, must correpond to one of the supported schemas"
        print "\tmessage_contents : comma separated pairs key=value that will be put in message"

if __name__ == "__main__":
    s = Sender()
    s.parse_parameters()
