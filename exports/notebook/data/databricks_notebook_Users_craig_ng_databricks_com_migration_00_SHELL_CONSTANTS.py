# Databricks notebook source
# MAGIC %sh
# MAGIC 
# MAGIC cat << EOF > ~/shell_constants.sh
# MAGIC export DBFS_LOCAL_REPO="local-dbfs-repo"
# MAGIC export REPO_URL="git@github.com:brucenelson6655/npipv2-repo.git"
# MAGIC export GIT_USER_EMAIL="bnelson.rugger@gmail.com"
# MAGIC export GIT_USER_NAME="Bbeucenelson6655"
# MAGIC export USER_EMAIL="bruce.nelson@databricks.com"
# MAGIC export USER_NAME="Bruce Nelson"
# MAGIC export DBFS_LOCAL_REPO_NAME="local-dbfs-repo"
# MAGIC export DBFS_HOME="/dbfs/\$USER_EMAIL"
# MAGIC 
# MAGIC # Export specific env variables
# MAGIC export DEFAULT_EXPORT_CONFIG_FILENAME="export"
# MAGIC export DBFS_EXPORT_CONFIG_FILENAME="export-dbfs"
# MAGIC export DATABRICKS_EXPORT_PROFILE_NAME="dr_source"
# MAGIC export DATABRICKS_EXPORT_HOST="https://adb-4686832614457882.2.azuredatabricks.net/"
# MAGIC export DATABRICKS_EXPORT_SCOPE="npip-scope"
# MAGIC export DATABRICKS_EXPORT_TOKEN_KEY="sourcetoken"
# MAGIC 
# MAGIC 
# MAGIC # Import Env Variables
# MAGIC export DATABRICKS_IMPORT_PROFILE_NAME="dr_target"
# MAGIC export DATABRICKS_IMPORT_HOST="https://adb-7913412718405082.2.azuredatabricks.net/"
# MAGIC export DATABRICKS_IMPORT_SCOPE="npip-scope"
# MAGIC export DATABRICKS_IMPORT_TOKEN_KEY="targettoken"
# MAGIC export DATABRICKS_IMPORT_HOST_FORMATTED=$(echo "$DATABRICKS_IMPORT_HOST" | awk -F[/:] '{print $4}' | sed -E 's/[^[:alnum:][:space:]]+/_/g')
# MAGIC 
# MAGIC # Import azure backend rg
# MAGIC export DATABRICKS_IMPORT_AZURE_BACKEND_RG_NAME="brn-private-endpoint"
# MAGIC export DATABRICKS_IMPORT_AZURE_BACKEND_SA_NAME="brntestendpoint"
# MAGIC export DATABRICKS_IMPORT_AZURE_BACKEND_CONTAINER_NAME="dbsyncstate"
# MAGIC export DATABRICKS_IMPORT_AZURE_BACKEND_ACCESS_KEY_SCOPE="npip-scope"
# MAGIC export DATABRICKS_IMPORT_AZURE_BACKEND_ACCESS_KEY_KEY="storageaccesskey"
# MAGIC EOF

# COMMAND ----------

# MAGIC %sh
# MAGIC 
# MAGIC cat ~/shell_constants.sh

# COMMAND ----------

def load_env():
  import os
  import pprint
  import shlex
  import subprocess

  command = shlex.split("env -i bash -c 'source ~/shell_constants.sh && env'")
  proc = subprocess.Popen(command, stdout = subprocess.PIPE)
  for line in proc.stdout:
    (key, _, value) = line.decode("utf-8").partition("=")
    os.environ[key] = value.replace("\n", "")
  proc.communicate()