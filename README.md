[![Tests](https://github.com/obanlatomiwa/ckanext-fcscopendata/workflows/Tests/badge.svg?branch=main)](https://github.com/obanlatomiwa/ckanext-fcscopendata/actions)

# ckanext-fcscopendata
A Custom CKAN extension for fcscopendata data portal.

## Requirements
Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9             |  tested    |

## Installation


To install ckanext-fcscopendata:
1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/obanlatomiwa/ckanext-fcscopendata.git
    cd ckanext-fcscopendata
    pip install -e .
	pip install -r requirements.txt

3. Add `fcscopendata` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. You need to initialize database from command line with the following commands:
    `ckan -c /etc/ckan/default/ckan.ini fcsc initdb`

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:
     sudo service apache2 reload



## ENV

To add Fcsc cms admin link

```
CKANEXT__FCSC__CMS = https://cms.fcsc.production.datopian.com/ghost
```