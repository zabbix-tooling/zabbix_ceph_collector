# Ceph Collector

A zabbix collector daemon for ceph.

# Installation

## Install Dependencies

```
sudo apt-get install virtualenv
cd /opt
git clone https://github.com/vico-research-and-consulting/zabbix_ceph_collector.git
cd /opt/zabbix_ceph_collector
virtualenv /opt/zabbix_ceph_collector/env --python /usr/bin/python3
source env/bin/activate
pip install -Ur requirements.txt
```

## Run manually

```
source env/bin/activate
./ceph_collector --help
./ceph_collector
```

## Configure service

```
cp ceph_collector.service /etc/systemd/system/ceph_collector.service
chown root:root /etc/systemd/system/ceph_collector.service
systemctl daemon-reload
systemctl enable ceph_collector.service
systemctl start ceph_collector.service
systemctl status ceph_collector.service
systemctl stop ceph_collector.service
```


