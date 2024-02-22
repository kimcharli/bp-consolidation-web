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

Duing develop
```
uvicorn src.app.main:app --reload --log-config=log_conf.yml
```

## closing

```
deactivate
```

