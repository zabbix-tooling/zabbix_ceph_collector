# Ceph Collector

A zabbix collector daemon for ceph.

# Installation

## Install Dependencies

```
sudo apt-get install virtualenv
INSTALLDIR="$PWD"
INSTALLDIR="/opt"
cd $INSTALLDIR
git clone https://github.com/vico-research-and-consulting/zabbix_ceph_collector.git
virtualenv $INSTALLDIR/zabbix_ceph_collector/env --python /usr/bin/python3
source $INSTALLDIR/zabbix_ceph_collector/env/bin/activate
pip install -Ur $INSTALLDIR/zabbix_ceph_collector/requirements.txt
```

## Run manually

```
cd $INSTALLDIR/zabbix_ceph_collector/
source env/bin/activate
./ceph_collector --help
./ceph_collector
```

## Configure service

```
cp $INSTALLDIR/zabbix_ceph_collector/ceph_collector.service /etc/systemd/system/ceph_collector.service
chown root:root /etc/systemd/system/ceph_collector.service
systemctl daemon-reload
systemctl enable ceph_collector.service
systemctl start ceph_collector.service
systemctl status ceph_collector.service
systemctl stop ceph_collector.service
```


