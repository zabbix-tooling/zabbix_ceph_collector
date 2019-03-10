# Ceph Collector

A zabbix collector daemon for ceph.

# Installation

## Virtualenv

``` 
sudo apt-get install virtualenv
echo "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh" >> ~/.bashrc
```

## Install Dependencies

```
git clone ...
cd ceph_collector
virtualenv env --python /usr/bin/python3
. env/bin/activate
pip install -Ur requirements.txt
```

## Run manually

```
. env/bin/activate
./ceph_collector --help
./ceph_collector
```

## Configure service

TODO


