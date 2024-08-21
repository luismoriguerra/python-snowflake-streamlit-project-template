## Create Dev connection

/Users/luismori/.snowflake/connections.toml

## Command 

https://docs.snowflake.com/en/developer-guide/snowflake-cli-v2/command-reference/connection-commands/add-connection



## Connection file 

~/.snowflake/connections.toml

```
[dev]
account = ""
user = ""
password = ""
database = ""
schema = ""
warehouse = ""
role = ""
```

## Define default connection 

```
snow connection set-default dev
```
