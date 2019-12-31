import json
import subprocess
import sys
import os
import argparse
import datetime
import time
import fcntl
import socket
import re
import glob
import logging
from pyzabbix import ZabbixMetric, ZabbixSender

lock_file_handle = None

def debug_cmd(out, err):
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug("STDOUT: >>>%s<<<\n" % out.decode('utf8'))
        logging.debug("STDERR: >>>%s<<<\n" % err.decode('utf8'))


def execute_cmd(cmd, dryrun=False):
    logging.debug("=> '%s'" % cmd)
    if dryrun:
        return (0, "n/a", "n/a")
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = process.communicate()
        if process.returncode != 0:
            logging.error("'%s' FAILED WITH CODE %s" % (cmd, process.returncode))
            debug_cmd(out, err)
            sys.exit(1)
        else:
            debug_cmd(out, err)
        return (process.returncode, out.decode('utf8'), err.decode('utf8'))


def file_is_locked(file_path):
    global lock_file_handle
    lock_file_handle = open(file_path, 'w')
    try:
        fcntl.lockf(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except IOError:
        return True


def check_on_leader():
    (exitcode, out, err) = execute_cmd("ceph daemon mon.%s mon_status" % socket.gethostname())
    result = json.loads(out)
    if exitcode == 0 and result['state'] == 'leader':
        return True
    return False


def get_daemons(daemon_type, regex_filter):
    os.chdir("/var/run/ceph/")
    daemons = []
    for filename in glob.glob("ceph*.asok"):
        m = re.match(r"^ceph-(.+\.\d+).asok$", filename)
        if not m:
            continue
        daemon_name = m.group(1)
        m = re.match(regex_filter, daemon_name)
        if m:
            daemons.append(daemon_name)
    return daemons