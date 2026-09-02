# -*- coding: utf-8 -*-

from common.database import DbHelper
import time

db = DbHelper(echo_output=True, use_cache=False, owner="Test Application")
host = 'vmdevubuntu18'
name = 'xplgw'
key = 'configured'
pause = 0
print(db.get_db_name())

with db.session_scope():
    print("================= Timeline device =======================")
    data = db.get_timeline(device_id=2)
    print(data)
    for elt in data:
        print(elt)
    print("================= Timeline client =======================")
    data = db.get_timeline(client_id="7")
    print(data)
    for elt in data:
        print(elt)
    print("================= Timeline global =======================")
    data = db.get_timeline()
    print(data)
    for elt in data:
        print(elt)
