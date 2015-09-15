Oracle TAF (Transparent Application Failover) Testing Suite
===========================================================

(note)
Here are the notes and demo code for a presentation I made to the
Northern California Oracle Users Group.  I have some slides and
a supplemental video which I am in the process of putting together.
(end note)

Here are some programs that will make it easier to test
Oracle TAF.

The main program is taf-demo.py, which demonstrates the various
actions the clients need to take to handle application failover.

The files are:

    taf-demo.py     demonstrating the various TAF client side features
    taf-control     control db nodes: start/stop/reboot
    taf-monitor     watch connection status NEEDS GENERALIZING
    taf-monitor.sh  simple shell version of the monitor
    taf-scenarios   run various start/stop scenarios
    taf-several     run many taf scenarios in multiple windows

- taf-demo.py:     demonstrating the various TAF client side features
- taf-control:     control db nodes: start/stop/reboot
- taf-monitor:     watch connection status NEEDS GENERALIZING
- taf-monitor.sh:  simple shell version of the monitor
- taf-scenarios:   run various start/stop scenarios
- taf-several:     run many taf scenarios in multiple windows

program        | note
--------------:|:---------------------------------------------------
taf-demo.py    | demonstrating the various TAF client side features
taf-control    | control db nodes: start/stop/reboot
taf-monitor    | watch connection status NEEDS GENERALIZING
taf-monitor.sh | simple shell version of the monitor
taf-scenarios  | run various start/stop scenarios
taf-several    | run many taf scenarios in multiple windows

taf-demo usage
--------------

```
Usage: taf-demo.py [options]

Options:
  -h, --help     show this help message and exit
  --node=NODE    connect to node
  --conn=CONN    connect string
  --delay=DELAY  delay interval
Commands:
      burden - cause burdensome load on node so load balance will shift away
    populate - provision the schema
          --
        idle - idle connection
  luckytrans - short transaction, showing you can get lucky and miss an error
   opentrans - open transaction, never commits
    pertrans - continually in transaction, periodically committing
      reconn - reconnect for every query
      select - select from a table, should TAF just fine
  selectdual - select from dual, should TAF just fine
  shorttrans - short transaction, then idle for a while
      xtable - special case select, with error checking for xtables
```

taf-control usage
-----------------

Because I did not want to make this too dangerous a command,
the test system is hard-coded inside the script.

There are some settings (such as sys connect string) that
you can put into taf.cfg.  There's a sample file
you can copy and modify.

```
    taf-control start|stop|bounce|reboot nodesnumbers...
    example: ./taf-control 3
```

taf-monitor usage
-----------------

This will monitor your various nodes and is handy to watch
your RAC connectability as you bounce nodes up and down.

```
Usage: taf-monitor [options] tns-wildcards...

Options:
  -h, --help   show this help message and exit
  --conn=CONN  connect string
  --tns=TNS    tns file path
  --skiptns    skip tns wildcarding
  --scroll     scroll output,no fullscreen
  --stats      print stats,must use serial option
  --fork       fork checking
  --fork2      fork checking,alternate version
```

taf-scenarios usage
-------------------

This has a couple of common failure scenarios coded.  Look at the
round-the-world example, where a client connection gets migrated
to all nodes in the cluster and ends up back at its original node.

taf-several usage
-----------------

This program pops up a bunch of windows and runs the various flavors
of the demos both with and without TAF.  The parameter can have
one of three values:  mac, macbook, linux.  These screen layouts
look good on my computers.  You will probably want to fiddle with
them.

The default is to run all demos concurrently.  If you are working
on a specific test or  tests there's a spot in the script you
can specify that.

Database Setup
--------------

Create a user TAFTEST (or any other name you like, actually) and
run the command

    taf-demo.py --conn=CONNECTSTRING populate

This will create the tables accessed while running the demos.

TNS Names Setup
---------------

Here's how I set up my TNS names for testing.  The secret sauce
is the FAILOVER_MODE section.  Note that your service doesn't have
to have any TAF settings enabled, it will pick this up from the
TNS file.  If the service has TAF settings, however, they will
override what is in your TNS file.

MHX and MHXNO are mnemonic for "MH experiment" and "MH expeririment, no
TAF".

You will need to adjust your HOST and SERVICE_NAME specifications.

    MHX =
      (DESCRIPTION =
        (ADDRESS = (PROTOCOL = TCP)(HOST = rac1-vip)(PORT = 1521))
        (ADDRESS = (PROTOCOL = TCP)(HOST = rac2-vip)(PORT = 1521))
        (ADDRESS = (PROTOCOL = TCP)(HOST = rac3-vip)(PORT = 1521))
        (LOAD_BALANCE = yes)
        (CONNECT_DATA =
          (SERVER = DEDICATED)
          (SERVICE_NAME = orcl)
          (FAILOVER_MODE =
            (BACKUP=MHX)
            (TYPE = SELECT)
            (METHOD = BASIC)
            (RETRIES = 2)
            (DELAY = 2)
          )
        )
      )

    MHXNO =
      (DESCRIPTION =
        (ADDRESS = (PROTOCOL = TCP)(HOST = rac1-vip)(PORT = 1521))
        (ADDRESS = (PROTOCOL = TCP)(HOST = rac2-vip)(PORT = 1521))
        (ADDRESS = (PROTOCOL = TCP)(HOST = rac3-vip)(PORT = 1521))
        (LOAD_BALANCE = yes)
        (CONNECT_DATA =
          (SERVER = DEDICATED)
          (SERVICE_NAME = orcl)
        )
      )

Notes
-----

If you don't have TAF enabled, you get one of these errors
on shutdown immediate no matter what operation operation
you are performing:

- ORA-01089: immediate shutdown in progress - no operations are permitted
- ORA-03113: end-of-file on communication channel


Shutdown Modes
--------------

Shutdown waits for everyone to finish & log out before it shuts down. The
database is cleanly shutdown.

Shutdown immediate rolls back all uncommitted transactions before it
shuts down. The database is cleanly shutdown.

Shutdown transactional waits for all current transactions to commit or
rollback before it shuts down. The database is cleanly shutdown.

Python Setup
------------

This package uses Python and the most excellent cx_Oracle database
interface.  I have a plain-vanilla build of both and did not specify
any special parameters.

- http://www.python.org
- http://cx-oracle.sourceforge.net
