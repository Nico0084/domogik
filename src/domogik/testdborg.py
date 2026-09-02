# -*- coding: utf-8 -*-

from common.database import DbHelper

db = DbHelper(echo_output=False, use_cache=False, owner="Test Application")
host = 'vmdevubuntu16'
name = 'nutserve'
print(db.get_db_name())

with db.session_scope():
    config = db.get_core_config()
    print(type(config),  config)
    listCP = db.list_plugin_config('plugin', name, host)
    print(type(listCP),  listCP)
    listCP = db.get_plugin_config('plugin', name, host, "host")
    print(type(listCP),  listCP)
    listCP = db.list_all_plugin_config()
    print(type(listCP),  listCP)
