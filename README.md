# bp-consolidation-web

## initial build of environment with venv

```
git clone https://github.com/kimcharli/bp-consolidation-web.git
cd bp-consolidation-web
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
```

## Prep env json file

[src/app/static/env-example.json](src/app/static/env-example.json)

```json
{
    "apstra": {
        "host": "nf-apstra.pslab.link",
        "port": "443",
        "username": "admin",
        "password": "admin",
        "logging_level": "DEBUG"   
    },
    "target": {
        "main_bp": "ATLANTA-Master",
        "tor_bp": "AZ-1_1-R5R15",
        "tor_im_new": "_ATL-AS-5120-48T",
        "cabling_maps_yaml_file": "tests/fixtures/sample-cabling-maps.yaml" 
    },
    "lldp": {
        "atl1lef15-r5r13": [
            {
                "neighbor_interface_name": "et-0/0/48",
                "neighbor_system_id": "atl1tor-r5r15a",
                "interface_name": "et-0/0/16"
            },
            {
                "neighbor_interface_name": "et-0/0/48",
                "neighbor_system_id": "atl1tor-r5r15b",
                "interface_name": "et-0/0/17"
            }
        ],
        "atl1lef16-r5r14": [
            {
                "neighbor_interface_name": "et-0/0/49",
                "neighbor_system_id": "atl1tor-r5r15a",
                "interface_name": "et-0/0/16"
            },
            {
                "neighbor_interface_name": "et-0/0/49",
                "neighbor_system_id": "atl1tor-r5r15b",
                "interface_name": "et-0/0/17"
            }
        ]
    }
}        
```


## run

Duing develop
```
uvicorn src.app.main:app --reload --log-config=log_conf.yml
```

## stop the server

^C on the console


## closing

```
deactivate
```

