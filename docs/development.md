

## Project structure

```
.
├── .streamlit/
│   └── secrets.toml
├── common/
│   └── helpers.py
├── streamlit_app.py
├── snowflake.yml
├── environment.yml
└── Makefile
```


## Define env variables 
.streamlit/secrets.toml
```
[snowflake]
account = ""
user = ""
password = ""
role = ""
warehouse = ""
database = ""
schema = ""
key_path = ""

```

## Define Anaconda local environment

## Install packages from environment file 

Any new packagge needs to be added in `environment.yml`


## New python files 

any new python file must go within `common` folder and udpate references in `snowflake.yml`

```
  additional_source_files:
    - common/helpers.py
```