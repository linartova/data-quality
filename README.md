# data-quality
This repository contains all materials tied to the Data Quality Framework Project.

## FHIR data quality
### How to load data into FHIR QC tool

Run conversion to FHIR with commands:

```
python run.py "data_file_name" --fhir <server_url>
```

## OMOP data quality
### How to load data into OMOP QC tool

Run conversion to OMOP with commands:

```
python run.py "data_file_name" --ohdsi_host "host" --ohdsi_port "port" --ohdsi_user "user" --ohdsi_password "pswd" --ohdsi_database "dtbs" --ohdsi_schema "schema"
```

## Both

Run conversion to both standards with commands:

```
python run.py "data_file_name" --fhir <server_url> --ohdsi_host "host" --ohdsi_port "port" --ohdsi_user "user" --ohdsi_password "pswd" --ohdsi_database "dtbs" --ohdsi_schema "schema"
```

