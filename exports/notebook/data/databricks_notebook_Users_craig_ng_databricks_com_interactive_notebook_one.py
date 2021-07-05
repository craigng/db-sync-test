# Databricks notebook source
1 + 1

# COMMAND ----------

spark.range(1000)

# COMMAND ----------

# MAGIC %fs ls /databricks-datasets/

# COMMAND ----------

# MAGIC %fs ls

# COMMAND ----------

# MAGIC %fs mkdirs /craig_one/

# COMMAND ----------

spark.range(1000).write.format("csv").save("/craig_one/test_csv/")

# COMMAND ----------

# MAGIC %fs ls /craig_one/test_csv/

# COMMAND ----------

# MAGIC %fs mkdirs /craig_two/

# COMMAND ----------

spark.range(1000).write.format("parquet").save("/craig_two/test_parquet")

# COMMAND ----------

