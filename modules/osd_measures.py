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
from pprint import pprint, pformat
from pyzabbix import ZabbixMetric, ZabbixSender
from modules.helpers import file_is_locked, debug_cmd, execute_cmd, check_on_leader, get_daemons


class OsdStats():

    def __init__(self, args):
        self.args = args
        self.daemons = {}
        self.results_now = {}
        self.results_last = {}
        self.last_discovery = 0
        self.stats_to_fetch = ['op_latency', 'op_r_latency', 'op_w_latency', 'op_rw_latency']

    def get_stats(self):
        collected_results = {}

        for ceph_daemon in get_daemons("osd", self.args.regex_filter):
            (exitcode_osd_perfdump, out_osd_perfdump, err_osd_perfdump) = execute_cmd("ceph daemon %s perf dump" % ceph_daemon)
            osd_perfdump = json.loads(out_osd_perfdump)
            collected_results.setdefault(ceph_daemon, {})
            for stat_item in self.stats_to_fetch:
                collected_results[ceph_daemon][stat_item] = osd_perfdump['osd'][stat_item]

        self.results_now = collected_results
        return collected_results

    def discover(self):
        zabbix_discovery_keys = 'ceph.osd.discovery'
        new_osds = False
        for daemon_name, data in self.results_now.items():
            if daemon_name not in self.daemons:
                osd_type = OsdStats.get_osd_details(daemon_name)['type']
                self.daemons[daemon_name] = {'{#OSD}': daemon_name, '{#DEVICECLASS}': osd_type}
                new_osds = True

        self.daemons["node"] = {'{#OSD}': "node", '{#DEVICECLASS}': 'all'}
        discovery_seconds_ago = time.time() - self.last_discovery

        if new_osds or discovery_seconds_ago > self.args.discovery_deadline:
            send_data = []
            for key, value in self.daemons.items():
                send_data.append(value)

            nr_devices = len(send_data)
            send_data = {'data': send_data}
            send_data = json.dumps(send_data, ensure_ascii=False)

            logging.debug("discovery data for %s : >>>%s<<<" % (zabbix_discovery_keys, send_data))

            packet = [
                ZabbixMetric(self.args.zabbix_host, zabbix_discovery_keys, send_data)
            ]
            result = ZabbixSender(use_config=True).send(packet)
            if result.failed > 0:
                logging.error("failed to send discovery for %s devices" % nr_devices)
            else:
                logging.info("successfully sent discovery for %s devices" % nr_devices)

            self.last_discovery = time.time()

    def process(self):
        stats = {}

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("results last: " + pformat(self.results_last))
            logging.debug("results now: " + pformat(self.results_now))

        metrics = list()

        for stat_type in self.stats_to_fetch:
            avgcount_node = 0
            avgsum_node = 0
            for daemon_name, data in self.results_now.items():
                avgcount_osd = data[stat_type]["avgcount"] - self.results_last[daemon_name][stat_type]["avgcount"]
                avgsum_osd = data[stat_type]["sum"] - self.results_last[daemon_name][stat_type]["sum"]

                if avgcount_osd == 0:
                    logging.info("%-5s %-20s %s" % (daemon_name, stat_type, "0"))
                    metrics.append(ZabbixMetric(self.args.zabbix_host, "osd_stat[%s,%s]" % (daemon_name, stat_type), "0"))
                else:
                    calc = float(avgsum_osd / avgcount_osd)
                    logging.info("%-5s %-20s %s" % (daemon_name, stat_type, calc))
                    metrics.append(ZabbixMetric(self.args.zabbix_host, "osd_stat[%s,%s]" % (daemon_name, stat_type), calc))

                avgcount_node += data[stat_type]["avgcount"] - self.results_last[daemon_name][stat_type]["avgcount"]
                avgsum_node += data[stat_type]["sum"] - self.results_last[daemon_name][stat_type]["sum"]

            if avgcount_node == 0:
                logging.info("node   %-20s %s" % (stat_type, "0"))
                metrics.append(ZabbixMetric(self.args.zabbix_host, "osd_stat[%s,%s]" % ("node", stat_type), "0"))
            else:
                calc = float((avgsum_node / avgcount_node))
                logging.info("node   %-20s %s" % (stat_type, calc))
                metrics.append(ZabbixMetric(self.args.zabbix_host, "osd_stat[%s,%s]" % ("node", stat_type), calc))

        result = ZabbixSender(use_config=True).send(metrics)
        if result.failed > 0:
            logging.error("failed to send %s of %s measures" % (result.failed, len(metrics)))
        else:
            logging.info("successfully sent %s measures" % len(metrics))

        return stats

    def collect(self):
        self.get_stats()
        self.discover()
        if len(self.results_last.keys()) > 0:
          self.process()
        self.results_last = self.results_now
        time.sleep(self.args.frequency)

    @staticmethod
    def get_osd_details(osd):
        ret = {
            "type": "unknown",
            "device": "unknown"
        }

        (exitcode, out, err) = execute_cmd("lsblk --json --output KNAME,ROTA,MOUNTPOINT,PKNAME")
        result = json.loads(out)
        if exitcode != 0:
            logging.error("unable to get device type for %s")
            return ret

        dev_path = re.sub(r"^osd.(\d+)$", r"/var/lib/ceph/osd/ceph-\1", osd)
        for dev_data in result['blockdevices']:
            if dev_data['mountpoint'] == dev_path:
                ret['device'] = "/dev/" + dev_data['pkname']
                if dev_data['rota'] == "1":
                    ret['type'] = 'hdd'
                else:
                    ret['type'] = 'ssd'
                break
        return ret


