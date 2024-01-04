# bp-consolidation-web

## initial build of environment with venv

```
git clone https://github.com/kimcharli/bp-consolidation-web.git
cd bp-consolidation-web
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
```

## run

environment in .env file
```
app_host=0.0.0.0
app_port=8000
apstra_server_host=nf-apstra.pslab.link
apstra_server_port=443
apstra_server_username=admin
apstra_server_password=zaq1@WSXcde3$RFV
logging_level=DEBUG
main_bp=ATLANTA-Master
tor_bp=AZ-1_1-R5R15
```

run
```
run-web
```

Duing develop
```
uvicorn src.app.main:app --reload
```

## closing

```
deactivate
```

