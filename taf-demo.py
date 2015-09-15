#!/usr/anim/bin/pypix
"""
Demo codez for client TAF handling.

various ora codes handled:
  while connecting:
   ORA-01033: ORACLE initialization or shutdown in progress
   ORA-12514: TNS:listener does not currently know of service requested
                  in connect descriptor
   ORA-12520: TNS:listener could not find available handler for
   ORA-12521: TNS:listener does not currently know of instance
   ORA-12528: TNS:listener: all appropriate instances are blocking
   ORA-12537: TNS:connection closed
  while processing:
   ORA-25401: can not continue fetches
   ORA-25402: transaction must roll back
   ORA-25408: can not safely replay call

  from alter system kill session '...':
   ORA-00028: your session has been killed
  from alter system kill session '...' immediate:
   ORA-25402: transaction must roll back (if in transaction)

  untested:
   ORA-03114: not connected to ORACLE
"""

import sys
import cx_Oracle
import time
import optparse

#-----------------------------------------------------------------------
delay_interval=.5
def delay(n=1):
    """wait a bit"""
    time.sleep(n*delay_interval)

#-----------------------------------------------------------------------
def now():
    """does anybody have the time?"""
    return time.strftime('%T')

#-----------------------------------------------------------------------
def nodeconnect(connstr,preference=None):
    """connect to oracle, possibly looking for a particular node"""
    try:
        if preference is None:
            return cx_Oracle.connect(connstr)
        else:
            while True:
                conn=cx_Oracle.connect(connstr)
                myinstance=instance(conn)[0]
                print now(),'got instance...',myinstance
                if myinstance==preference:
                    return conn
                else:
                    conn.close()
    except cx_Oracle.DatabaseError,e:
        # ORA-01033: ORACLE initialization or shutdown in progress
        # ORA-12537: TNS:connection closed
        # ORA-12528: TNS:listener: all appropriate instances are blocking
        #            new connections
        # ORA-12521: TNS:listener does not currently know of instance
        #            requested in connect descriptor
        # ORA-12520: TNS:listener could not find available handler for
        #            requested type of server
        # ORA-12514: TNS:listener does not currently know of service
        #            requested in connect descriptor
        if e.message.code in [1033,12514,12537,12528,12521,12520]:
            print 'RETRYING:', e.message.message.strip()
            time.sleep(2)
            return nodeconnect(connstr,preference)
        else:
            raise(e)


#-----------------------------------------------------------------------
def instance(conn):
    """what instance are we connected to?"""
    curs=conn.cursor()
    try:
        curs.execute("""select sys_context('userenv','instance'),
                              sys_context('userenv','server_host') from dual""")
        r=curs.fetchone()
    except cx_Oracle.DatabaseError,e:
        # ORA-25401: can not continue fetches
        # ORA-25402: transaction must roll back
        # ORA-25408: can not safely replay call
        if e.message.code in [25401,25402,25408]:
            ###print 'ignoring(case 1):', e.message.message.strip()
            r=('unknown-instance','unknown-host')
        else:
            raise(e)
    curs.close()
    return r

#-----------------------------------------------------------------------
def checknode(conn,node):
    """check to see if our node has changed and print msg if so"""
    newnode=instance(conn)
    if newnode != node:
        node=newnode
        print '---',node,'---'
    return node

#-----------------------------------------------------------------------
def do_reconn(connstr,unused_parm):
    """reconnect for every query"""

    while True:
        conn = nodeconnect(connstr)
        curs = conn.cursor()
        curs.execute("select sysdate from dual")
        tt=curs.fetchone()[0]
        print tt,now(),instance(conn)
        conn.close()
        delay()


#-----------------------------------------------------------------------
def do_idle(connstr,node):
    """idle connection"""
    print 'sitting idle'
    conn=nodeconnect(connstr,node)
    curs=conn.cursor()

    node='none'
    while True:
        node=checknode(conn,node)
        print now(),instance(conn)
        delay(20)

#-----------------------------------------------------------------------
def do_select(connstr,node):
    """select from a table, should TAF just fine"""
    selectguts(connstr,node,"select x from taf_nums order by x")

#-----------------------------------------------------------------------
def do_selectdual(connstr,node):
    """select from dual, should TAF just fine"""
    selectguts(connstr,node,"select level from dual connect by level<=1000000")

#-----------------------------------------------------------------------
def selectguts(connstr,node,query):
    """common code of select"""
    print 'long-running select'
    conn=nodeconnect(connstr,node)
    curs=conn.cursor()

    node='none'
    curs.execute(query)
    
    # no TAF checks needed, handled automatically
    for r in curs:
        node=checknode(conn,node)
        print r,now(),instance(conn)
        delay()

#-----------------------------------------------------------------------
def do_selectxtable(connstr,node):
    """special case select, with error checking for xtables"""
    print 'long-running xtab select'
    conn=nodeconnect(connstr,node)
    curs=conn.cursor()

    node='none'
    query="select x,sys_context('userenv','instance') from taf_nums order by x"
    
    while True:
        try:
            curs.execute(query)
            for r in curs:
                node=checknode(conn,node)
                print r,now(),instance(conn)
                delay()
        except cx_Oracle.DatabaseError,e:
            # ORA-25401: can not continue fetches
            # ORA-25402: transaction must roll back
            # ORA-25408: can not safely replay call
            if e.message.code in [25401,25402,25408]:
                print 'caught',e.message.message.strip()
                continue
            else:
                raise(e)

#-----------------------------------------------------------------------
def do_opentrans(connstr,node):
    """open transaction, never commits"""
    trans_guts(connstr,node,False)

#-----------------------------------------------------------------------
def do_pertrans(connstr,node):
    """continually in transaction, periodically committing"""
    trans_guts(connstr,node,True)

#-----------------------------------------------------------------------
def trans_guts(connstr,node,docommit):
    """transaction guts"""
    conn=nodeconnect(connstr,node)
    curs=conn.cursor()

    NCOUNT=100
    while True:
        try:
            for i in range(NCOUNT,0,-1):
                print i,now(),instance(conn)
                curs.execute("insert into taf_junk(x) values(:1)",[i])
                delay()
            if docommit:
                print 'committing...'
                conn.commit()

        except cx_Oracle.DatabaseError,e:
            # ORA-25401: can not continue fetches
            # ORA-25402: transaction must roll back
            # ORA-25408: can not safely replay call
            if e.message.code in [25401,25402,25408]:
                print 'TAF rollback, restarting transaction...'
                conn.rollback()
                time.sleep(1)
                NCOUNT=100
                continue
            else:
                raise(e)

#-----------------------------------------------------------------------
def do_shorttrans(connstr,node):
    """short transaction, then idle for a while"""
    conn=nodeconnect(connstr,node)
    curs=conn.cursor()

    while True:
        print now(),instance(conn)
        try:
            # do something with short time window
            curs.execute("insert into taf_junk(x) values(-1)")
            conn.commit()
        except cx_Oracle.DatabaseError,e:
            # ORA-25401: can not continue fetches
            # ORA-25402: transaction must roll back
            # ORA-25408: can not safely replay call
            if e.message.code in [25401,25402,25408]:
                print 'caught ORA-2540x, restarting transaction...'
                time.sleep(1)
                conn.rollback()
                continue
            else:
                raise(e)
        # and idle for a while
        print 'idling...'
        delay(20)

#-----------------------------------------------------------------------
def do_luckytrans(connstr,node):
    """short transaction, showing you can get lucky and miss an error"""
    conn=nodeconnect(connstr,node)
    curs=conn.cursor()

    # if the node is downered in your idle time, you won't get an
    # exception and this loop will be fine.  Feeling Lucky?
    while True:
        print now(),instance(conn)
        curs.execute("insert into taf_junk(x) values(-1)")
        conn.commit()
        print 'idling...'
        delay(20)

#-----------------------------------------------------------------------
def aprint(s):
    """print a msg without newline, flush it"""
    sys.stdout.write(s)
    sys.stdout.flush()
    
#-----------------------------------------------------------------------
def do_populate(connstr,unused_parm):
    """provision the schema"""
    conn=nodeconnect(connstr)
    curs=conn.cursor()

    for (t,nrows) in [['taf_nums',1000000],['taf_junk',2]]:
        aprint('%s...'%(t))
        try:
            curs.execute('drop table %s'%(t))
            aprint('(dropped)')
        except cx_Oracle.DatabaseError,e:
            # ORA-00942: table or view does not exist
            if e.message.code not in [942]:
                raise(e)
        aprint('(creating)')
        curs.execute("create table %s(x number)"%(t))
        aprint('(populating)')
        curs.execute("""insert into %s(x) (
                            select level+1000000 from dual
                            connect by level <= %s)
                     """%(t,nrows))
        curs.execute('select count(*) from %s'%(t));
        aprint('(%s rows)'%(curs.fetchone()[0]))
        aprint('(indexing)')
        curs.execute("create index %s_index1 on %s(x)"%(t,t))
        aprint('(committing)')
        conn.commit()
        print ''

#-----------------------------------------------------------------------
def do_burden(connstr,node):
    """cause burdensome load on node so load balance will shift away"""

    conns=[]
    for x in range(10):
       conns.append(nodeconnect(connstr,node))

    x=1
    while True:
        for conn in conns:
            x+=1
            # intentionally cause reparse, we're making a burden!
            curs=conn.cursor()
            curs.execute('insert into taf_junk(x) values (%d)'%(x))
            curs.execute('select count(*) from taf_junk')
            print curs.fetchone(),
            curs.close()
        print

cmdproc={
    'populate'	: do_populate,
    'burden'	: do_burden,
    'reconn'	: do_reconn,
    'idle'	: do_idle,
    'select'	: do_select,
    'dual':      do_selectdual,
    'xtable'	: do_selectxtable,
    'opentrans'	: do_opentrans,
    'pertrans'	: do_pertrans,
    'shorttrans': do_shorttrans,
    'luckytrans': do_luckytrans,
    }

#-----------------------------------------------------------------------
def cmds_help():
    print 'Commands:'
    k=cmdproc.keys()
    k.sort()
    for x in k:
        doc=cmdproc[x].func_doc
        print '  %10s - %s'%(x,doc)

#-----------------------------------------------------------------------
def main():
    """the main thing is to keep the main thing the main thing"""

    parser = optparse.OptionParser()
    parser.add_option( "", "--node", help="connect to node")
    parser.add_option( "", "--conn", help="connect string")
    parser.add_option( "", "--delay", help="delay interval")
    (opts, args) = parser.parse_args(sys.argv)

    if len(args) != 2 or opts.conn is None:
        parser.print_help()
        cmds_help()
        sys.exit(1)

    if opts.delay is not None:
        global delay_interval
        delay_interval = float(opts.delay)

    cmd=args[1]

    if cmdproc.has_key(cmd):
        cmdproc[cmd](opts.conn,opts.node)
    else:
        parser.print_help()
        cmds_help()
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
