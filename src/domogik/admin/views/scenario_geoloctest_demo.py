# -*- coding: utf-8 -*-

from domogik.admin.application import app, render_template, timeit
from flask import Blueprint, abort, jsonify, request
from flask_login import login_required

import time
import json
from shapely.geometry import MultiPolygon, Polygon, Point
from shapely.ops import transform
from functools import partial
import pyproj

personState = {'status': '', 'time': time.time()}

def get_request(action, data):
    resData = {u'error': u'', u'data': {}}
    if action == 'getintersects' :
        resData = evaluate(data)
    elif action == 'getBuffer':
        resData = buildBuffer(data)
    return action, resData

@app.route('/scenario/request_geoloc_demo/<req>')
@login_required
@timeit
def geoloc_request(req):
    print(u"geoloc recieved Request : {0}".format(req))
    data = {}
    for k, v in request.args.iteritems():
        data[k] = v
    reply, msg = get_request(str(req), data)
    print(u"geoloc receive response : {1}".format(reply, msg))
    if 'error'in msg and msg['error'] !="":
        return jsonify(result='error', reply=reply, content = msg)
    else :
        return jsonify(result='success', reply=reply, content = msg)

def processState(newState):
    global personState

    print(u'  processState in : {0}'.format(personState, newState))
    if personState['status'] != newState :
        if newState == 'present' :
            if personState['status'] in ['absent', 'leave'] :
               newState = 'enter'
            elif personState['status'] == 'enter' :
                newState = 'present'
        elif newState == 'absent' :
            if personState['status'] in ['present', 'enter'] :
               newState = 'leave'
            elif personState['status'] == 'leave' :
                newState = 'absent'
    personState = {'status': newState, 'time': time.time()}
    print(u'  processState out : {0}'.format(personState))
    return newState

def getHystersis(buffer):
    global personState
    newBuffer = float(buffer)
    if personState['status'] in ['absent', 'leave'] :
        newBuffer = 0
    print(u"    getHysterisis : {0} (buffer : {1}=>{2})".format(personState['status'], buffer, newBuffer))
    return newBuffer

def getPolyBuffered(poly, bufferValue):
    bufferValue = float(bufferValue)
    print(u"***** getPolyBuffered buffer : {0}".format(bufferValue))
    if bufferValue != 0 :
        # Transform to meters
        p1Buffer = transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init='EPSG:4326'),  # EPSG:4326 est WGS 84
                pyproj.Proj(
                    proj='aea',
                    lat1=poly.bounds[1],
                    lat2=poly.bounds[3]
                )
            ),
            poly)
        p2Buffer = p1Buffer.buffer(bufferValue)
        print("*********************", p2Buffer.area)
        # transforn to geo coordinate
        result = transform(
            partial(
                pyproj.transform,
                pyproj.Proj(
                    proj='aea',
                    lat1=p2Buffer.bounds[1],
                    lat2=p2Buffer.bounds[3]
                ),
                pyproj.Proj(init='EPSG:4326')  # EPSG:4326 est WGS 84
            ),
            p2Buffer)
        return result
    else : return poly

def evaluate(data):
    """ Evaluate the person position compare to location
    """
    global personState

#    print("**** eval : ", data)
    person_hyst = data['personBuffer']
    gpsPoint = {'lat': float(data['personLat']), 'lng':float(data['personLng'])}
    operator = data['operator']
    loc_hyst = data['locationBuffer']
    location = {'type': data['ctrl_type'],
                    'lat': float(data['lat']),
                    'lng': float(data['lng']),
                    'area': data['ctrl_area'],
    }
    print(u"Eval operator = {0}, last state = {1}".format(operator, personState['status']))
    if gpsPoint is None:
        return None
    elif  location is None:
        return None
    else:
        loc_buffer =getHystersis(loc_hyst)
        # Create shapely objects
        p = Point(gpsPoint['lat'], gpsPoint['lng'])
        p1 = getPolyBuffered(p, person_hyst)
        personBuffer = list(p1.exterior.coords)
        if location['type'] == 'circle' :
            p = Point(location['lat'], location['lng'])
            p2 = getPolyBuffered(p, float(location['area']) + loc_buffer)
            locBuffer = list(p2.exterior.coords)
            state = processState('present' if p1.intersects(p2) else 'absent')
            result = operator == state
        elif location['type'] == 'polygon' :
            state = None
            result = False
            for poly in json.loads(location['area']) :
                p = Polygon(poly)
                p2 = getPolyBuffered(p, loc_buffer)
                locBuffer = list(p2.exterior.coords)
                state = processState('present' if p1.intersects(p2) else 'absent')
                if operator == state :
                    result = True
                    break
        else :
            print(u"Error area type unknown. Value='{0}'".format(location))
            return None
        print("Evaluate = {0}".format(result))
        return {'error': '', 'operator': operator, 'result': result, 'state': state, 'locbuffer': locBuffer, 'personbuffer': personBuffer}

def buildBuffer(data):
    result = {'error': ""}
    print("**** build buffer for : ", data)
    buffer = float(data['buffer'])
    type =  data['type']
    if type in ['person', 'circle'] :
        p = Point(float(data['lat']), float(data['lng']))
        polyB = getPolyBuffered(p, float(data['area']) + buffer)
#        polyB = Point(float(data['lat']), float(data['lng'])).buffer((float(data['area']) + buffer)/toDecDeg)
    elif type == 'polygon':
        for poly in json.loads(data['area']) :
            p = Polygon(poly)
            polyB = getPolyBuffered(p, buffer)

#            polyB = Polygon(poly).buffer(buffer/toDecDeg)
    result['poly'] = list(polyB.exterior.coords)
    print(result)
    return result
