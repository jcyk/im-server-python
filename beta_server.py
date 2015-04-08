# -*- coding: UTF-8 -*-
from SocketServer import (TCPServer as TCP,
                          StreamRequestHandler as SRH,
                          ThreadingMixIn as TMI)
from time import ctime
import json
import base64
import traceback
import MySQLdb
import time
import random
import os

onlineDic = {}
HOST = '192.168.1.106'
PORT = 5296
ADDR = (HOST, PORT)
TAIL = '######'

onlinehander = {}
class Server(TMI, TCP):
    pass

def sendMsg(username,context):
    if onlinehander.has_key(username):   
        onlinehander[username].request.sendall(context+TAIL)
        print "MSG SEND TO",onlinehander[username].client_address,context
    else:
        db = MySQLdb.connect("localhost","root","jcyk","beta")
        cursor = db.cursor()
        #
        sql = 'insert into OFFLINEMSG (_username,_context) values(%s,%s)'
        cursor.execute(sql,(username,context))
        db.commit()
        db.close()


def fetchTeaminfo(teamID):
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    #
    team = {}
    team['teamID'] = teamID
    sql = "select _teamname from TEAM where _teamID=%s"
    cursor.execute(sql,(teamID,))
    teamname = cursor.fetchone()
    teamname = teamname[0]
    team['teamname'] = teamname
    teammember = []
    sql = "select USER._username,_nickname from USER_TEAM,USER where USER_TEAM._username=USER._username and _teamID =%s"
    cursor.execute(sql,(teamID,))
    person = cursor.fetchall()
    for x in person:
        teammember.append({'username':x[0],'nickname':x[1]})
    team['teammember'] = teammember
    return team

def getTeaminfo(req,context):
    teamID = req['teamID']
    res = fetchTeaminfo(req)
    res['type'] = 'teaminfo_result'
    return json.dumps(res)

def getOfflinemsg(req,context):
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    username = req['username']
    #
    sql = 'select _OFFLINEMSGID,_context from OFFLINEMSG where _username = %s'
    cursor.execute(sql,(username,))
    result = cursor.fetchall()
    for row in result:
        print "ATTEMPT SEND OFFLINEMSG TO",username,row[1]
        sql = 'delete from OFFLINEMSG where _OFFLINEMSGID=%s'
        cursor.execute(sql,(row[0],))
        db.commit()
        sendMsg(username,row[1])    
    db.close()
    return ''

def teamchat(req,context):
    username = req['from']
    teamID = req['teamID']
    body = req['body']
    datetime = req['datetime']
    messageNo = req['messageNo']
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    #
    sql = 'select _username from USER_TEAM where _teamID =%s'
    cursor.execute(sql,(teamID,))
    result = cursor.fetchall()
    for row in result:
        if(username!=row[0]):
            sendMsg(row[0],context)
    res ={}
    res['type'] = 'teamchat_result'
    res['MessageNo'] = messageNo
    db.close()
    return json.dumps(res)

def updateUserinfo(req,context):
    username = req['username']
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    #
    sql  = 'select _nickname,_version,_studentNo from USER where _username =%s'
    cursor.execute(sql,(username,))
    result = cursor.fetchone()
    if req.has_key('nickname'):
        nickname = req['nickname']
    else:
        nickname = result[0]
    if req.has_key('studentNo'):
        studentNo = req['studentNo']
    else:
        studentNo = result[2]
    sql = 'update USER set _nickname =%s, _version=_version+1,_studentNo=%s  where _username=%s'
    cursor.execute(sql,(nickname,studentNo,username))
    db.commit()
    if(req.has_key('head')):
        filename = '%s.png'%username
        ls_f = base64.b64decode(req['head'])
        f = open(filename,'wb')
        f.write(ls_f)
        f.close()
    res = {}
    res['type'] = 'updateUserinfo_result'
    res['version'] = result[1]+1
    return json.dumps(res)


def getUserinfo(req,context):
    username  = req['username']
    oversion = req['version']
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    #
    sql  = 'select _nickname,_version,_studentNo from USER where _username =%s'
    cursor.execute(sql,(username,))
    result = cursor.fetchone()
    version = result[1]
    res = {}
    res['type'] = 'userinfo_result'
    res['version'] = version
    res['username'] = username
    if(oversion==version):
        pass
    else:
        filename = '%s.png'%username
        if  os.path.exists(filename):
            f = open(filename,'rb')
            ls_f = base64.b64encode(f.read())
            f.close()
            res['head'] =  ls_f
        else:
            res['head'] = 'null'
        res['nickname'] = result[0]
        res['studentNo'] = result[2]
    db.close()
    return json.dumps(res)

def register(req,context):
    username = MySQLdb.escape_string(req['username'])
    nickname = MySQLdb.escape_string(req['nickname'])
    password = MySQLdb.escape_string(req['password'])
    studentNo = MySQLdb.escape_string(req['studentNo'])
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    #
    sql = "insert into USER (_username,_nickname,_password,_studentNo,_version) values(%s,%s,%s,%s,%s)"
    try:
        cursor.execute(sql,(username,nickname,password,studentNo,1))
        db.commit()
        db.close()
        res = {}
        res['type'] = 'register_result'
        res['body'] = 'ok'
        if(req.has_key('head')):
            filename = '%s.png'%username
            ls_f = base64.b64decode(req['head'])
            f = open(filename,'wb')
            f.write(ls_f)
            f.close()
        return json.dumps(res)
    except:
        db.rollback()
        db.close()
        res = {}
        res['type'] = 'register_result'
        res['body'] = 'error'
        return json.dumps(res)

def login(req,context):
    username = MySQLdb.escape_string(req['username'])
    password = MySQLdb.escape_string(req['password'])
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    #
    sql = "select _password from USER WHERE _username = %s"
    try:
        cursor.execute(sql,(username,));
        result = cursor.fetchone()
        if result[0] != password:
            db.close()
            res = {}
            res['type'] = 'login_result'
            res['body'] = 'error: wrong password'
            return json.dumps(res)
    except:
        db.close()
        res= {}
        res['type'] = 'login_result'
        res['body'] = 'error: no such user'
        return json.dumps(res)
    res= {}
    res['type'] = 'login_result'
    res['body'] = 'ok'
    return json.dumps(res)

def createteam (req,context):
    creator = req['creator']
    teamname = req['teamname']
    help = random.randint(0,1000000009)
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    #
    sql = "insert into TEAM (_teamname,_help) values(%s,%s) "
    try:
        cursor.execute(sql,(teamname,help))
        db.commit()
        sql = "select _teamID from TEAM where _teamname = %s and _help =%s"
        cursor.execute(sql,(teamname,help))
        result = cursor.fetchone()
        teamID = result[0]
        sql = "insert into USER_TEAM (_teamID,_username) values(%s,%s)"
        cursor.execute(sql,(teamID,creator))
        db.commit()
    except:
        db.rollback()
        db.close()
        res = {}
        res['type'] = 'createteam_result'
        res['teamID'] = 'error'
        res['teamname'] = 'error'
        return json.dumps(res)
    res = {}
    res['type'] = 'createteam_result'
    res['teamID'] = teamID
    res['teamname'] = teamname
    db.close()
    return json.dumps(res)

def addfriend (req,context):
    to =req['to']
    sendMsg(to,context)

def iamin(req,context):
    username = req['username']
    teamID =req['teamID']
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    sql = "insert into USER_TEAM values(%s,%s)"
    cursor.execute(sql,(teamID,username))
    db.commit()
    db.close()

def myteam(req,context):
    username = req['username']
    db = MySQLdb.connect("localhost","root","jcyk","beta")
    cursor = db.cursor()
    #
    res = {}
    res['type'] = 'myteam_result'
    teamlist = []
    sql = "select USER_TEAM._teamID from USER_TEAM,TEAM where TEAM._teamID=USER_TEAM._teamID and _username =%s"
    cursor.execute(sql,(username,))
    result = cursor.fetchall()
    for row in result:
        teamID = row[0]
        team = fetchTeaminfo(teamID)
        teamlist.append(team)
    res['body'] = teamlist
    return json.dumps(res)


class MyRequestHandler(SRH):
    def handle(self):
        print 'Got connection from ',self.client_address
        username = "#"
        data = ''
        while True:
            raw = self.request.recv(4096)
            if not raw:
                print 'error'
                break
            data+=raw
            if raw[len(raw)-1]!='}':
                continue
            print "RECV FROM",self.client_address,data
            request = json.loads(data)
            msg=''
            if request['type'] == 'register':
                msg = register(request,data)
            elif request['type'] =='login':
                msg = login(request,data)
                res = json.loads(msg)
                if(res['body']=='ok'):
                    username = request['username']
                    onlinehander[username] = self
                    print time.asctime( time.localtime(time.time()) ),username,'is online'
            elif request['type'] =='createteam':
                msg = createteam(request,data)
            elif request['type'] =='addfriend':
                msg = addfriend(request,data)
            elif request['type'] =='myteam':
                msg = myteam(request,data)
            elif request['type'] == 'userinfo':
                msg  = getUserinfo(request,data)
            elif request['type'] == 'teamchat':
                msg = teamchat(request,data)
            elif request['type'] == 'getofflinemsg':
                msg = getOfflinemsg(request,data)
            elif request['type'] == 'teaminfo':
                msg = getTeaminfo(request,data)
            elif request['type'] == 'updateuserinfo':
                msg = updateUserinfo(request,data)
            data = ''
            self.request.sendall(msg+TAIL)
            print "SEND TO",self.client_address,msg
        if onlinehander.has_key(username):
            del onlinehander[username]
            print time.asctime( time.localtime(time.time()) ),username,'is offline'
        print 'End connection with',self.client_address

tcpServ = Server(ADDR, MyRequestHandler)
print 'waiting for connection...'
tcpServ.serve_forever()
#f = open(r'test.png','rb')
#ls_f = base64.b64encode(f.read())
#res = {}
#res['type'] = 'png'
#res['body'] = ls_f
#tot.append(res)



