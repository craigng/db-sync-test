# Databricks notebook source
# MAGIC %fs ls

# COMMAND ----------

# MAGIC %fs ls /craig_one/

# COMMAND ----------

# MAGIC %fs ls /craig_two/

# COMMAND ----------

spark.range(1000).write.csv("/craig_three/test_csv/")

# COMMAND ----------

# MAGIC %fs ls /craig_three/

# COMMAND ----------

spark.range(1000).write.parquet("/craig_four/test_parquet/")

# COMMAND ----------

# MAGIC %fs ls /craig_four/

# COMMAND ----------

