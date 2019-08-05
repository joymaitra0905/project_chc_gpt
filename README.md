# Enterprise Data Lake [![Build Status](https://travis-ci.com/SanofiDSE/data-lake-config.svg?token=GY1QuvqPbwBdXLxYiytW&branch=master)](https://travis-ci.com/SanofiDSE/data-lake-config)

This repository is for files related to configuring AWS and other resources for the
Enterprise Data Lake. Installing the EDL python package in this repository will make two command line programs
available. `edl` for deploying EDL resources in AWS and `edl-api` for interacting
with the EDL APIs. Both programs have sub-commands which can be listed by calling
the programs with `--help` or `-h`. Add a sub-command to get help for a specific
sub-command. The python package `edl`
contains helper functions and utilities that can be used when writing
PySpark pipelines and lambda functions.

## Features

The EDL provides/manages the following functions:

* **Data Location Management**: Processes for creating data storage locations and
  recording privacy and security policies associated with each location.
* **Data Import and Storage**: Processes for moving data into these locations,
  triggering related processes such as ETL and QC, and recording associated
  metadata.
* **Data Transformation**: Processes for transforming data in one location,
  and storing the results in a new location.
* **Access Control**: Processes for granting and revoking access to individual
  users while following the privacy and security policies associated with the
  data.
* **Data Access**: Processes for accessing the data from supported analysis
  tools/platforms while following the privacy and security policies associated
  with the data.


## Installation

* Clone the repository

* If you're developing a pipeline to run on the EDL, run the script
  `pipeline_setup.sh`

* If you're doing dev work on the EDL itself, run the script
  `dev_setup.sh`

Both setup scripts will install the EDL python package which besides making `edl`
available from python make `edl/installed_scripts/dl.py`
available as the command line program `edl`, and make `edl_api/edl_api.py`
available as the command line program `edl-api`.

## Examples
See examples of how to use `edl-api` in the folder `examples/`. See
the folders under `pipelines/` for examples of Spark and PySpark
pipelines. See `projects/example_lambda*`for examples deploying
lambda functions.

# Architecture

## General

The EDL is built on AWS, in Sanofi Cloud accounts managed by GIS. The GIS
team deploys all components related to the VPC, including roles that manage
VPCs such as the main Databricks role. The remaining infrastructure is deployed
using scripts in this code repository via Cloudformation stacks.

The IAM policies in the UAT and PROD accounts each give only minimal (primarly
read-only) privileges to users, but include a Cloudformation role with much
wider privileges. The scripts in the repository run using this role, so that only
scripted changes can be made.

The code that manages Cloudformation is organized as follows:

* `edl/`: Resources that are part of the EDL python package.
* `edl/cloudformation/`: Libraries that interact with Cloudformation and
  determine what gets deployed.
  * `stack_client.py`: Low-level functions for interacting with Cloudformation.
  * `stack_manager.py`: Functions that deploy specific components.
* `edl/installed_scripts/dl.py`: Main program for deploying and updating
  resources. It is made available as the command `edl`.
* `edl/core_resources/`: Resources that are used for core deployment.
  * `config/`: YAML files that define specifics of the deployment.
  * `pipelines/ingest/`: The ingest pipeline.
  * `rest_api/`: API resources.
* `pipelines/`: Pipelines that are not part of the core deployment.
* `projects/`: Various project specific files.

## Data Location Management

Data is organized into *datasets*, each representing a collection of data
that may be changing over time. Each dataset is organized into a
collection of *updates*. Once an update is complete, it cannot be
changed/updated, so the only way for a dataset to change is by adding updates.

The updates in a dataset may be complete snapshots of the dataset, or may
encode deltas. By deltas, we mean that an update may encode a list of changes
that can be combined with a previous snapshot to generate a new snapshot.
The conventions for defining a delta will be specific to the dataset. The
mechanics for converting deltas into snapshots will be defined in the
**Data Transformation** section below.

Each dataset falls under one of the following *security tiers*:
* **Internal**: Data that can be shared with all Sanofi employees.
* **Restricted**: Data that has the same level of associated risk as internal
  data, but can only be shared with a limited subset of Sanofi employees.
* **Sensitive**: Data that has non-trivial risk associated with it and can only
  be shared with a limited set of Sanofi employees, on a need-to-know basis.

Datasets and updates are stored in S3 buckets defined by their security tier,
an AWS region and the EDL *instance* - either `dev01`, `uat` or `prod`.

```
sanofi-datalake-<INSTANCE>-<TIER>-<REGION>
```

Within each bucket, the top-level folders are for individual datasets. Each
dataset folder has a `/raw/` folder for data in arbitrary formats, and a
`/data/` folder for parquet files. So a directory structure might look
like this:

```
s3://bucket/dataset1/raw/update1/file1.csv
                                /file2.csv
                        /update2/file3.csv
                                /file4.csv
                    /data/update1/file1.parquet
                                 /file2.parquet
                         /update2/file3.parquet
                                 /file4.parquet
           /dataset2/raw/update1/file5.csv
          .
          .
          .
```


## Data Import and Storage

Data is imported via a Spark job that:
0) Creates a new update folder in the `/raw/` folder.
1) Copies raw data from an external source into this folder, unzipping it if
   necessary.
2) Creates a new update folder in the `/data/` folder.
3) Converts the raw data to parquet and saves the results in this folder.

The code defining this process is in `edl/core_resources/pipelines/ingest/`
and uses the pipeline framework described in the *Data Transformation* section.

The ingest process is triggered by a REST API call defined in the config
file `edl/core_resources/config/api_config.yaml`. The code for all API calls is in the
`edl/core_resources/rest_api/` folder, and helper scripts for calling the API can be found in
the `utils/` folder.

Data can be pulled from multiple types of sources including S3. Each data bucket
has a drop bucket (`sanofi-datalake-drop-<INSTANCE>-<TIER>-<REGION>`) that external
users/systems can drop data into.


## Data Transformation

Data transformations in production can be defined by writing either PySpark or
SparkSQL code. The EDL provides a deploy script that packages any custom
code with a wrapper script that runs it in the chosen environment (Glue, EMR,
etc.)

To define a custom PySpark pipeline, all code must be in a single directory with
two files:
* A YAML file called `pipeline_config.yaml` that defines parameters used by
  the deploy script.
* A PySpark script called `pipeline.py` that defines a `run()` function.

The pipeline script is deploy into an environment where it can import any
libraries in the `edl/utils/` folder and any files in the directory containing
the two files above.

An example PySpark script can be found in `pipelines/example/`.

To define a SQL pipeline, queries should be saved as `.sql` files in a single
directory along with a YAML file called `pipeline_config.yaml` that defines
where the results of these queries should be saved.

An example SQL script can be found in `pipelines/sql_example/`.


## Access Control

All data access is controlled via IAM Roles. The create/update dataset function
in the deploy script (`edl deploy-dataset ...`)
creates a number of roles with different levels or read/write access, as
defined in the template `edl/cloudformation/templates/folder_acls.yaml`. The
core deploy script also creates a role with access to all internal-tier
datasets, defined in the template
`edl/cloudformation/templates/default_acls.yaml`.


## Data Access

Data can be accessed directly in S3 via the AWS S3 API, or from a JDBC/ODBC
connection provided by Athena.

