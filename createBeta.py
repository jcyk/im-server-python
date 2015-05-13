import MySQLdb

db = MySQLdb.connect("localhost","root","jcyk","beta")
cursor = db.cursor()
sql = """
    CREATE TABLE USER (
        _username varchar(20) PRIMARY KEY,
        _nickname varchar(50),
        _password varchar(20),
        _studentNo varchar(20),
        _version int
    )
"""
cursor.execute(sql)
sql = """
    CREATE TABLE TEAM(
        _teamID int NOT NULL auto_increment,
        _teamname varchar(50),
        _help int,
        primary key (_teamID)
    )
    """
cursor.execute(sql)
sql = """
    CREATE TABLE USER_TEAM (
        _teamID int,
        _username varchar(20),
        PRIMARY KEY (_teamID,_username),
        FOREIGN KEY (_teamID) REFERENCES TEAM(_teamID) on delete cascade,
        FOREIGN KEY (_username) REFERENCES USER(_username) on delete cascade
    )"""
cursor.execute(sql)
sql = """
    CREATE TABLE OFFLINEMSG (
    _OFFLINEMSGID int NOT NULL auto_increment,
    _username varchar(20),
    _context longhtext,
    PRIMARY KEY (_OFFLINEMSGID),
    FOREIGN KEY (_username) REFERENCES USER(_username) on delete cascade
    )"""
cursor.execute(sql)
db.close()
