#!/usr/bin/env dls-python
## \namespace read_archiver
# read_archiver.py is a python script to read bits
# from pmac status mbbo records in the archiver
# The intended use case is to query for changes in status bits
#  
# Example query:
# \verbatim
#   dls-python read_archiver.py BL02I-MO-STEP-05:AXIS1:status3 0x4 2015-02-10@00:00 2015-02-11@11:40
# \endverbatim
# queries for bit 0x4 of status byte 3 which represents following error.
# The output in this case was
# \verbatim
# 1 Mon Feb 9 08:42:44 2015 False 0
# 6 Wed Feb 11 11:26:44 2015 True 0
# 7 Wed Feb 11 11:29:48 2015 False 0
# 11 Wed Feb 11 11:34:04 2015 True 0
# 12 Wed Feb 11 11:36:04 2015 False 0
# \endverbatim
# The output indicates that the axis went into following error twice 
#
# Help text from read_archiver.py -h
#\verbatim
#read bits from bit field records in DLS archiver
#Invocation:
#   read_archiver.py <pvname> <value> <start_time> <end_time>
#
#Where:
#   <pvname> is a bit field pv, e.g. BL23I-MO-STEP-01:PLCDISBITS00
#   <value>  is a bit field mask in decimal or hex, e.g. 0x800 or 2048
#   <start_time> is a time in the format "%Y-%m-%d@%H:%M" (no seconds)
#                for example 2012-11-11@17:10
#   <end_time>   is a time in the format "%Y-%m-%d@%H:%M" (no seconds)
#
#The output is of the form:
#
#  count date_time [True/False] severity
# 
#Example pvs and masks:
#
#  for $(pmac):PLCDISBITS00 use these values
#       plc0           0x1             
#       plc1           0x2   
#       plc2           0x4   
#       plc3           0x8   
#       plc4           0x10  
#       plc5           0x20  
#       plc6           0x40  
#       plc7           0x80  
#       plc8           0x100 
#       plc9           0x200 
#       plc10          0x400 
#       plc11          0x800 
#       plc12          0x1000
#       plc13          0x2000
#       plc14          0x4000
#       plc15          0x8000
#
#  for $(pmac):AXIS<N>:status1 use these values cf. Turbo SRM p. 310-315
#       motor activated           0x8000
#       negative end limit set    0x4000
#       positive end limit set    0x2000
#       amplifier enabled         0x800
#       open loop mode            0x400
#       desired velocity zero     0x20
#       home search in progress   0x4
#
#  for $(pmac):AXIS<N>:status3 use these values
#       assigned to c.s.          0x8000
#       stopped on position limit 0x800
#       home complete             0x400
#       fatal following error     0x4
#       warning following error   0x2
#       in position               0x1
#\endverbatim

import time
import sys
from xmlrpclib import ServerProxy, Error

Archiver_URL = "http://archiver.pri.diamond.ac.uk/" \
                + "archive/cgi/ArchiveDataServer.cgi"

def help():
    print sys.argv[0] + """
read bits from bit field records in DLS archiver
Invocation:
   read_archiver.py <pvname> <value> <start_time> <end_time>

Where:
   <pvname> is a bit field pv, e.g. BL23I-MO-STEP-01:PLCDISBITS00
   <value>  is a bit field mask in decimal or hex, e.g. 0x800 or 2048
   <start_time> is a time in the format "%Y-%m-%d@%H:%M" (no seconds)
                for example 2012-11-11@17:10
   <end_time>   is a time in the format "%Y-%m-%d@%H:%M" (no seconds)

The output is of the form:

  count date_time [True/False] severity
 
Example pvs and masks:

  for $(pmac):PLCDISBITS00 use these values
       plc0           0x1             
       plc1           0x2   
       plc2           0x4   
       plc3           0x8   
       plc4           0x10  
       plc5           0x20  
       plc6           0x40  
       plc7           0x80  
       plc8           0x100 
       plc9           0x200 
       plc10          0x400 
       plc11          0x800 
       plc12          0x1000
       plc13          0x2000
       plc14          0x4000
       plc15          0x8000

  for $(pmac):AXIS<N>:status1 use these values cf. Turbo SRM p. 310-315
       motor activated           0x8000
       negative end limit set    0x4000
       positive end limit set    0x2000
       amplifier enabled         0x800
       open loop mode            0x400
       desired velocity zero     0x20
       home search in progress   0x4

  for $(pmac):AXIS<N>:status3 use these values
       assigned to c.s.          0x8000
       stopped on position limit 0x800
       home complete             0x400
       fatal following error     0x4
       warning following error   0x2
       in position               0x1

"""

def main(pvname, check_value_str, start_str, end_str ):
    server = ServerProxy(Archiver_URL)
    archiver_key = 1000 # key for "all" archiver
    # start time
    t1 = time.strptime(start_str, "%Y-%m-%d@%H:%M")
    time1 = time.mktime(t1)
    t2 = time.strptime(end_str, "%Y-%m-%d@%H:%M")
    time2 = time.mktime(t2)
    check_value = int(check_value_str,0)

    complete = False
    no_data = False
    count = 1
    while not complete:
        result = server.archiver.values(archiver_key, [pvname], 
                                    int(time1), 0, int(time2), 0, 100, 0)
        assert(len(result) == 1)
        if len(result[0]['values']) == 0:
            no_data = True
        if len(result[0]['values']) != 100:
            complete = True
        for entry in result[0]['values']:
            bit_value = entry['value'][0] & check_value == check_value 
            if count == 1:
                last_value = not bit_value
            if bit_value != last_value:
                print count, time.ctime(entry['secs']), bit_value, entry['sevr']
                last_value = bit_value
            count = count + 1
        #Time of latest value
        if not no_data:
            if result[0]['values'][-1]['secs'] >= time2:
                complete = True
            else:
                time1 = result[0]['values'][-1]['secs'] + 1
    if no_data:
        print "no data available"

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        help()
        sys.exit(1)
    if len(sys.argv) < 5:
        help()
        sys.exit(1)

    (pvname, check_value_str, start_str, end_str ) = sys.argv[1:5]
    main(pvname, check_value_str, start_str, end_str )
