# Databricks notebook source
# MAGIC %md
# MAGIC 
# MAGIC # Install

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Install Databricks Sync
# MAGIC 
# MAGIC The main branch installation will be:
# MAGIC 
# MAGIC `pip install git+https://github.com/databrickslabs/databricks-sync`
# MAGIC 
# MAGIC Optionally you can install a custom branch/tag/revision via:
# MAGIC 
# MAGIC `pip install git+https://github.com/databrickslabs/databricks-sync@<custom branch/tag/revision>`

# COMMAND ----------

# MAGIC %pip install git+https://github.com/databrickslabs/databricks-sync

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Install Terraform

# COMMAND ----------

# MAGIC %sh
# MAGIC export TF_VERSION=0.14.8
# MAGIC terraform --version || (wget --quiet https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip \
# MAGIC   && unzip terraform_${TF_VERSION}_linux_amd64.zip \
# MAGIC   && mv terraform /usr/bin \
# MAGIC   && rm terraform_${TF_VERSION}_linux_amd64.zip)

# COMMAND ----------

# MAGIC %md 
# MAGIC 
# MAGIC # Shell Constants

# COMMAND ----------

# MAGIC %run ./00_SHELL_CONSTANTS

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Configure Git 

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Pull Git SSH Keys

# COMMAND ----------

# MAGIC %sh 
# MAGIC . ~/shell_constants.sh
# MAGIC mkdir -p ~/.ssh
# MAGIC cp -R ${DBFS_HOME}/ssh/* ~/.ssh/ 
# MAGIC chmod 400 ~/.ssh/id_rsa
# MAGIC chmod 400 ~/.ssh/id_rsa.pub
# MAGIC ls -lrt ~/.ssh

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Git config

# COMMAND ----------

# MAGIC %sh
# MAGIC cat << EOF > ~/.ssh/config
# MAGIC Host *
# MAGIC     StrictHostKeyChecking no
# MAGIC EOF

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Git user config

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC git config --global user.email $GIT_USER_EMAIL
# MAGIC git config --global user.name $GIT_USER_NAME

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## (Optional) Test clone

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC # git clone -v $REPO_URL

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Configure CLI Target

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Configure CLI Profiles

# COMMAND ----------

from databricks_cli.configure.provider import DatabricksConfig, update_and_persist_config
import os
load_env()
# Insecure = True just means that TLS wont be verified
# TODO: Make token secret
tgt_cfg = DatabricksConfig.from_token(host=os.environ["DATABRICKS_IMPORT_HOST"], 
                                      token=dbutils.secrets.get(scope=os.environ["DATABRICKS_IMPORT_SCOPE"], key=os.environ["DATABRICKS_IMPORT_TOKEN_KEY"]), insecure="true")
update_and_persist_config(os.environ["DATABRICKS_IMPORT_PROFILE_NAME"], tgt_cfg)

# COMMAND ----------

# MAGIC %md 
# MAGIC 
# MAGIC # Setup Back Ends

# COMMAND ----------

from pathlib import Path
import os
import json
import urllib.parse

from databricks_sync.sdk.utils import normalize_identifier

load_env()
home_dir = Path(os.environ["DBFS_HOME"])
backends_dir = home_dir / Path("backends")
# target_workspace_url = os.environ["DATABRICKS_IMPORT_HOST"]
# parsed_url = urllib.parse.urlparse(target_workspace_url)
normalized_host = os.environ["DATABRICKS_IMPORT_HOST_FORMATTED"]
import_workspace_dir = backends_dir / Path(normalized_host)

dbfs_files_backend_file = import_workspace_dir / "dbfs-files-backend-config.json"
non_dbfs_files_backend_file = import_workspace_dir / "non-dbfs-files-backend-config.json"

import_workspace_dir.mkdir(parents=True, exist_ok=True)

dbfs_files_key = f"{normalized_host}_dbfs_files.tfstate"
non_dbfs_files_key = f"{normalized_host}_non_dbfs_files.tfstate"

def make_json(path, key):
  j = {
    "terraform": {
      "backend": {
        "azurerm": {
          "resource_group_name": os.environ["DATABRICKS_IMPORT_AZURE_BACKEND_RG_NAME"],
          "storage_account_name": os.environ["DATABRICKS_IMPORT_AZURE_BACKEND_SA_NAME"],
          "container_name": os.environ["DATABRICKS_IMPORT_AZURE_BACKEND_CONTAINER_NAME"],
          "key": key,
          "access_key": dbutils.secrets.get(scope=os.environ["DATABRICKS_IMPORT_AZURE_BACKEND_ACCESS_KEY_SCOPE"], 
                                            key=os.environ["DATABRICKS_IMPORT_AZURE_BACKEND_ACCESS_KEY_KEY"])
        }
      }
    }
  }
  with path.open("w+") as f:
    f.write(json.dumps(j, indent=2))
  print(f"Created backend file at: {path}")

make_json(dbfs_files_backend_file, dbfs_files_key)
make_json(non_dbfs_files_backend_file, non_dbfs_files_key)

# COMMAND ----------

# MAGIC %sh
# MAGIC 
# MAGIC cat /dbfs/backends/dbfs-files-backend-config.json
# MAGIC cat /dbfs/backends/non-dbfs-files-backend-config.json

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Import DBFS Files

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Get Existing DBFS repo

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC rm -rf ~/$DBFS_LOCAL_REPO && cp ${DBFS_HOME}/dbfsexport/${DBFS_LOCAL_REPO_NAME}.tar.gz ~/ && \
# MAGIC   mkdir -p ~/$DBFS_LOCAL_REPO && \
# MAGIC   tar -xvf ~/$DBFS_LOCAL_REPO.tar.gz -C ~/

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Pre Apply Plan

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC mkdir -p ${DBFS_HOME}/artifact_dir/dbfsfiles/
# MAGIC eval "$(ssh-agent -s)"
# MAGIC ssh-add ~/.ssh/id_rsa
# MAGIC TF_VAR_CLOUD=azure GIT_PYTHON_TRACE=full databricks-sync -v debug import \
# MAGIC --profile $DATABRICKS_IMPORT_PROFILE_NAME \
# MAGIC -l ~/$DBFS_LOCAL_REPO \
# MAGIC --artifact-dir ${DBFS_HOME}/artifact_dir/dbfsfiles/ \
# MAGIC --backend-file ${DBFS_HOME}/backends/${DATABRICKS_IMPORT_HOST_FORMATTED}/dbfs-files-backend-config.json \
# MAGIC --plan \
# MAGIC --skip-refresh

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Apply

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC mkdir -p ${DBFS_HOME}/artifact_dir/dbfsfiles/
# MAGIC eval "$(ssh-agent -s)"
# MAGIC ssh-add ~/.ssh/id_rsa
# MAGIC TF_VAR_CLOUD=azure GIT_PYTHON_TRACE=full databricks-sync -v debug import \
# MAGIC --profile $DATABRICKS_IMPORT_PROFILE_NAME \
# MAGIC -l ~/$DBFS_LOCAL_REPO \
# MAGIC --artifact-dir ${DBFS_HOME}/artifact_dir/dbfsfiles/ \
# MAGIC --backend-file ${DBFS_HOME}/backends/${DATABRICKS_IMPORT_HOST_FORMATTED}/dbfs-files-backend-config.json \
# MAGIC --plan \
# MAGIC --skip-refresh \
# MAGIC --apply

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Post Apply Plan

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC mkdir -p ${DBFS_HOME}/artifact_dir/dbfsfiles/
# MAGIC eval "$(ssh-agent -s)"
# MAGIC ssh-add ~/.ssh/id_rsa
# MAGIC TF_VAR_CLOUD=azure GIT_PYTHON_TRACE=full databricks-sync -v debug import \
# MAGIC --profile $DATABRICKS_IMPORT_PROFILE_NAME \
# MAGIC -l ~/$DBFS_LOCAL_REPO \
# MAGIC --artifact-dir ${DBFS_HOME}/artifact_dir/dbfsfiles/ \
# MAGIC --backend-file ${DBFS_HOME}/backends/${DATABRICKS_IMPORT_HOST_FORMATTED}/dbfs-files-backend-config.json \
# MAGIC --plan \
# MAGIC --skip-refresh

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Import Non DBFS Files

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Pre Apply Plan

# COMMAND ----------

# MAGIC %sh
# MAGIC 
# MAGIC . ~/shell_constants.sh
# MAGIC mkdir -p ${DBFS_HOME}/artifact_dir/nondbfsfiles/
# MAGIC eval "$(ssh-agent -s)"
# MAGIC ssh-add ~/.ssh/id_rsa
# MAGIC TF_VAR_CLOUD=azure GIT_PYTHON_TRACE=full databricks-sync -v debug import \
# MAGIC --profile $DATABRICKS_IMPORT_PROFILE_NAME \
# MAGIC -g $REPO_URL \
# MAGIC --branch main \
# MAGIC --artifact-dir ${DBFS_HOME}/artifact_dir/nondbfsfiles/ \
# MAGIC --backend-file ${DBFS_HOME}/backends/${DATABRICKS_IMPORT_HOST_FORMATTED}/non-dbfs-files-backend-config.json \
# MAGIC --plan \
# MAGIC --skip-refresh

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Apply

# COMMAND ----------

# MAGIC %sh
# MAGIC 
# MAGIC . ~/shell_constants.sh
# MAGIC mkdir -p ${DBFS_HOME}/artifact_dir/nondbfsfiles/
# MAGIC eval "$(ssh-agent -s)"
# MAGIC ssh-add ~/.ssh/id_rsa
# MAGIC TF_VAR_CLOUD=azure GIT_PYTHON_TRACE=full databricks-sync -v debug import \
# MAGIC --profile $DATABRICKS_IMPORT_PROFILE_NAME \
# MAGIC -g $REPO_URL \
# MAGIC --branch main \
# MAGIC --artifact-dir ${DBFS_HOME}/artifact_dir/nondbfsfiles/ \
# MAGIC --backend-file ${DBFS_HOME}/backends/${DATABRICKS_IMPORT_HOST_FORMATTED}/non-dbfs-files-backend-config.json \
# MAGIC --plan \
# MAGIC --skip-refresh \
# MAGIC --apply

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Post Apply Plan

# COMMAND ----------

# MAGIC %sh
# MAGIC 
# MAGIC . ~/shell_constants.sh
# MAGIC mkdir -p ${DBFS_HOME}/artifact_dir/nondbfsfiles/
# MAGIC eval "$(ssh-agent -s)"
# MAGIC ssh-add ~/.ssh/id_rsa
# MAGIC TF_VAR_CLOUD=azure GIT_PYTHON_TRACE=full databricks-sync -v debug import \
# MAGIC --profile $DATABRICKS_IMPORT_PROFILE_NAME \
# MAGIC -g $REPO_URL \
# MAGIC --branch main \
# MAGIC --artifact-dir ${DBFS_HOME}/artifact_dir/nondbfsfiles/ \
# MAGIC --backend-file ${DBFS_HOME}/backends/${DATABRICKS_IMPORT_HOST_FORMATTED}/non-dbfs-files-backend-config.json \
# MAGIC --plan \
# MAGIC --skip-refresh