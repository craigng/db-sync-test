# Databricks notebook source
# MAGIC %md
# MAGIC 
# MAGIC ## SSH Key Gen

# COMMAND ----------

# MAGIC %sh
# MAGIC ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa <<< y

# COMMAND ----------

# MAGIC %md 
# MAGIC 
# MAGIC ## Move SSH keys to DBFS for long term

# COMMAND ----------

# MAGIC %sh 
# MAGIC mkdir -p /dbfs/bruce.nelson@databricks.com/ssh
# MAGIC cp -R ~/.ssh/* /dbfs/bruce.nelson@databricks.com/ssh/

# COMMAND ----------

# MAGIC %sh 
# MAGIC ls -lrt ~/.ssh
# MAGIC ls -lrt /dbfs/bruce.nelson@databricks.com/ssh/

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## Store public key into git ssh keys or your git provider's ssh keys

# COMMAND ----------

# MAGIC %sh
# MAGIC cat /dbfs/bruce.nelson@databricks.com/ssh/id_rsa.pub

# COMMAND ----------

