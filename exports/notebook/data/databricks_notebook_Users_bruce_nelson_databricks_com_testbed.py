# Databricks notebook source
# MAGIC %sh 
# MAGIC 
# MAGIC cat /dbfs/craig.ng@databricks.com/backends/dbfs-files-backend-config.json

# COMMAND ----------

# MAGIC %sh
# MAGIC 
# MAGIC cat /dbfs/craig.ng@databricks.com/backends/non-dbfs-files-backend-config.json

# COMMAND ----------

spark.conf.set(
  "fs.azure.account.key.csntestendpoint.blob.core.windows.net",
  'wbsOCCh4ufbCIiNm31npwk0Vn5jV4cdImyfHFt/S7abqarSk1jK6W9jHN+EA2kJ6KvHoLzr9Wo8Jg6qwn5uE4Q==')

# COMMAND ----------

dbutils.fs.ls("wasbs://dbsyncstate@csntestendpoint.blob.core.windows.net/")

# COMMAND ----------

spark.conf.set(
  "fs.azure.account.key.csntestendpoint.blob.core.windows.net",
  '9JbMeWEVzyTnoDuhm8vSmsl49AjNQNRrUsJNT832/0osBpy254fC1NHxrh1OKxgyj7nWI6q64SdZzQTyPcYSfQ==')

# COMMAND ----------

dbutils.fs.ls("wasbs://dbsyncstate@csntestendpoint.blob.core.windows.net/")

# COMMAND ----------

# MAGIC %sh
# MAGIC 
# MAGIC cat /dbfs/craig.ng@databricks.com/backends/non-dbfs-files-backend-config.json

# COMMAND ----------

