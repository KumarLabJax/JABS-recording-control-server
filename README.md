# JAX Mouse Behavior Analysis Control Service

Flask Service to coordinate the centralized control of multiple JAX Mouse 
Behavior Analysis enclosures.


#### Setup

##### Virtual Environment
create a virtual environment:
```
python3 -m venv venv.jax-mba-service
source venv.jax-mba-service/bin/activate
pip install -r requirements.txt
```

##### Config
Edit the config file to specify server specific values.

To autogenerate `jax-mba-service.config`, or to regenerate JWT secrets run:
```python manage.py init_config```


## JAX Mouse Behavior Analysis Control Service Management
The flask service is managed with the manage.py module. Depending on the 
template options selected, some features may be unavailable.

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

## Configuring for Production

For a non-development configuration, the service should be run using Nginx and 
uwsgi with a Postgresql database.

### Prerequisites

* Python 3 (tested with Python 3.7)
* Postgresql (tested with Postgresql 9.2.24)
* Nginx (tested with 1.12.2-3)

Everything else required is installed into the Python virtual environment
described above.

### Flask Service

#### Service Account
setup a service account for uwsgi to use to run the Flask app

```bash
useradd --system jax-mba
```

#### Postgresql 

First, as the postgres user, create a new database, schema, and a user. You will
need the username, database name, and password you choose here to complete the
app configuration file in the next step.

```text
sudo su - postgres
createuser jaxmba
createdb jax_mba_db
psql
psql (9.2.24)
Type "help" for help.

postgres-# alter user jaxmba with encrypted password '<password>';
postgres-# grant all privileges on database jax_mba_db to jaxmba ;
\q
exit
```

Next you will need to edit the pg_hba.conf file so that Postgresql will allow
the database user to connect with a username and password. Run the following 
command to find the location of pg_hba.conf:

``` sudo su postgres -c "psql -t -c 'show hba_file'"```

Then edit this file:

sudo vi <PATH TO pg_hba.conf>

and add the following line:

```host    jax_mba_db    jaxmba     0.0.0.0/0 md5```

This allows the postgres user jaxmba to access the jax_mba_db database from any 
host using SCRAM-SHA-256 or MD5 authentication to verify the user's password.

Once pg_hba.conf has been modified, restart postgresql for the change to take 
effect.

#### virtual env and app config file
Create a python virtual environment and then generate a config file template as 
described above.

To project sensitive information such as the Flask and JWT secrets, and the 
postgresql password, this config file should not be world-readable if anyone
not authorized to have this information has access to the server. In this case, 
the service account created above mush have read permission to this
configuration file through the files owner or group.

#### uWSGI configuration 
Next, create a uwsgi configuration file. There is a template located at 
`deploy/example.uwsgi.ini`. Copy this file to `deploy/example.uwsgi.ini` and 
edit to reflect your installation.


#### Systemd service 

Configure the Flask service to run as a Systemd service. This template can serve
as a starting point for a Systemd unit file. Edit to reflect your install 
location and virtual environment name and copy it to 
/etc/systemd/system/jax-mba.service

```text
[Unit]
Description=JAX Mouse Behavior Analysis Web Service

Requires=network.target

After=network.target

[Service]
TimeoutStartSec=0
RestartSec=10
Restart=always
ExecStart=/usr/bin/bash -c 'cd /opt/compsci/jax-mba-service; source venv.jax-mba-service/bin/activate; uwsgi --ini deploy/uwsgi.ini'

[Install]
WantedBy=multi-user.target
```

The Flask service can be started with `sudo systemctl start jax-mba`. Set it to 
start at boot with `sudo systemctl enable jax-mba`

#### Nginx

The last step in configuring the web service is to configure Nginx to act as a 
proxy for API requests. The following is a starting point for a Nginx config
file. This file assumes that this Nginx server will also be hosting the static
content for the UI. You will need to change the `root` parameter to point to 
the directory with the UI index.html file. `uwsgi_pass` will also have to be 
set to the location that you've configured uWSGI to open the socket.

Note that for a production configuration you will want to setup SSL to avoid 
sending passwords over plain text.
TODO: add information about configuring Nginx to use https

```text
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

# Load dynamic modules. See /usr/share/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    include /etc/nginx/conf.d/*.conf;

    server {
        listen       80 default_server;
        listen       [::]:80 default_server;
        server_name  _;
        
        # change root to point to the UI build
        #root         /usr/share/nginx/html;
        root	/INSTALL_PATH/jax-mba-frontend/dist/ui;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;
        
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # pass any requests for api endpoints or swaggerui on to the Flask app
        # via the unix socket 
        location /api { try_files $uri @api; }
        location @api {
            include uwsgi_params;
            uwsgi_pass unix:///var/run/uwsgi/uwsgi.sock;
        }

        location /swaggerui {
            include uwsgi_params;
            uwsgi_pass unix:///var/run/uwsgi/uwsgi.sock;          
        }

        location /swagger.json {
            include uwsgi_params;
            uwsgi_pass unix:///var/run/uwsgi/uwsgi.sock;
        }

        error_page 404 /404.html;
            location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
            location = /50x.html {
        }
    }
}

```