# Long-Term Monitoring System Control Service

Flask Service to coordinate the centralized control of multiple long-term monitoring systems


#### Setup

##### Virtual Environment
create a virtual environment:
```
python3 -m venv venv.ltmcs
source venv.ltmcs/bin/activate
pip install -r requirements.txt
pip freeze > requirements.txt
```

##### Config
Edit the `config.ini` file to specify server specific values.

To autogenerate `ltm_control_service.config` secrets, call:
```python -m manage init_config```


## Long-Term Monitoring System Control Service Management
The flask service is managed with the manage.py module. Depending on the template options you selected, some features 
may be unavailable.

It can be accessed with either:
```bash
python -m manage --help
```
or
```bash
python manage.py --help
```

```bash
usage: manage.py [-?] {run,db,start_workers,test,test_xml,shell,runserver} ...

positional arguments:
  {run,db,start_workers,test,test_xml,shell,runserver}
    run                 The main entrypoint to running the app :return: None
    db                  Perform database migrations
    start_workers       Start the celery worker(s)
    test                Run unit tests
    test_xml            Runs the unit tests specifically for bamboo CI/CD
    shell               Runs a Python shell inside Flask application context.
    runserver           Runs the Flask development server i.e. app.run()

optional arguments:
  -?, --help            show this help message and exit

```

Credits
-------
This package was created with Cookiecutter and the `cookiecutter_flask_service` project template. The template was 
created and is maintained by Alexander Berger <alexander.berger@jax.org>.

This application was created by Glen Beane <glen.beane@jax.org>.
