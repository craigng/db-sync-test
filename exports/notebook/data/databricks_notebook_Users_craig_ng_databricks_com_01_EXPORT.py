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

# MAGIC %pip install git+https://github.com/databrickslabs/databricks-sync@permissions-fix-for-ndpe

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

# MAGIC %sh
# MAGIC cat << EOF > ~/.ssh/config
# MAGIC Host *
# MAGIC     StrictHostKeyChecking no
# MAGIC EOF

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Configure GIT user

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC git config --global user.email $USER_EMAIL
# MAGIC git config --global user.name $USER_NAME

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## (Optional) Test clone

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC cd /tmp && git clone -v $REPO_URL

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Configure CLI Source

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Configure CLI Profiles

# COMMAND ----------

from databricks_cli.configure.provider import DatabricksConfig, update_and_persist_config
import os
load_env()
# Insecure = True just means that TLS wont be verified

tgt_cfg = DatabricksConfig.from_token(host=os.environ["DATABRICKS_EXPORT_HOST"], 
                                      token=dbutils.secrets.get(scope=os.environ["DATABRICKS_EXPORT_SCOPE"], key=os.environ["DATABRICKS_EXPORT_TOKEN_KEY"]), insecure="true")
update_and_persist_config(os.environ["DATABRICKS_EXPORT_PROFILE_NAME"], tgt_cfg)


# COMMAND ----------

# MAGIC %sh
# MAGIC cat ~/.databrickscfg

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Export DBFS Files

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Export YAML File

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC cat > ${DBFS_EXPORT_CONFIG_FILENAME}.yaml <<EOF
# MAGIC name: test
# MAGIC objects:
# MAGIC   dbfs_file:
# MAGIC     dbfs_path:
# MAGIC     - "dbfs:/FileStore/jars"
# MAGIC EOF

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Get Existing DBFS repo

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC (rm -rf ~/${DBFS_LOCAL_REPO_NAME} && cp ${DBFS_HOME}/dbfsexport/${DBFS_LOCAL_REPO_NAME}.tar.gz ~/ && \
# MAGIC   mkdir -p ~/${DBFS_LOCAL_REPO_NAME} && \
# MAGIC   tar -xvf ~/${DBFS_LOCAL_REPO_NAME}.tar.gz -C ~/) || \
# MAGIC mkdir -p ~/${DBFS_LOCAL_REPO_NAME}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Export in Local Git

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC databricks-sync -v debug export --profile ${DATABRICKS_EXPORT_PROFILE_NAME} -l ~/${DBFS_LOCAL_REPO_NAME} -c ${DBFS_EXPORT_CONFIG_FILENAME}.yaml --dask

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Tar and Backup repo in dbfs

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC cd ~ && tar cvzf ${DBFS_LOCAL_REPO_NAME}.tar.gz ${DBFS_LOCAL_REPO_NAME} && \
# MAGIC   mkdir -p ${DBFS_HOME}/dbfsexport && \
# MAGIC   cp ${DBFS_LOCAL_REPO_NAME}.tar.gz ${DBFS_HOME}/dbfsexport/${DBFS_LOCAL_REPO_NAME}.tar.gz

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC ls -lrt ${DBFS_HOME}/dbfsexport/

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Export Non DBFS Objects

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Export YAML File

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC cat > ${DEFAULT_EXPORT_CONFIG_FILENAME}.yaml <<EOF
# MAGIC name: test
# MAGIC objects:
# MAGIC   notebook:
# MAGIC     # Notebook path can be a string, a list or a YAML items collection (multiple subgroups starting with - )
# MAGIC     notebook_path: "/Shared"
# MAGIC     # Use Custom map var to setup a new location
# MAGIC     custom_map_vars:
# MAGIC       path: "(?<variable>^\/[^\/]*\/)"
# MAGIC EOF

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Run Export

# COMMAND ----------

# MAGIC %sh
# MAGIC . ~/shell_constants.sh
# MAGIC databricks-sync -v debug export --profile ${DATABRICKS_EXPORT_PROFILE_NAME} -g ${REPO_URL} -c ${DEFAULT_EXPORT_CONFIG_FILENAME}.yaml --branch main --dask