# Databricks notebook source
# MAGIC %md
# MAGIC ##### Useful Links
# MAGIC * https://www.linkedin.com/pulse/setting-up-external-hive-metastore-mysql-databricks-spark-kalyanapu?articleId=6630999929265414148
# MAGIC * https://docs.microsoft.com/en-gb/azure/databricks/data/metastores/external-hive-metastore
# MAGIC * https://docs.microsoft.com/en-us/azure/mysql/howto-create-users?tabs=single-server
# MAGIC * https://docs.microsoft.com/en-us/azure/mysql/concepts-data-access-security-private-link

# COMMAND ----------

# MAGIC %md
# MAGIC ##### You will need access to your underlying ADLS for tables - use whatever means you need to to set up access to your underlying storage to be able to back up your existing metastore

# COMMAND ----------

# DBTITLE 0,You will need access to your underlying ADLS for tables
# MAGIC %run ../storageaccess 

# COMMAND ----------

# MAGIC %md
# MAGIC ##### we will need to mount a filesystem to store our metastore backup files

# COMMAND ----------

# dbutils.fs.unmount("/mnt/util")

# COMMAND ----------

# Lets mount a filesystem to store our metastore backup 
# import json

# kvsecret = json.loads(dbutils.secrets.get(scope = "npip-scope", key = "bnelson-brntestendpoint-key"))

# dbutils.fs.mount(
#   source = "wasbs://" + kvsecret["container"] + "@" + kvsecret["account"] + ".blob.core.windows.net",
#   mount_point = "/mnt/util",
#   extra_configs = {"fs.azure.account.key." + kvsecret["account"] + ".blob.core.windows.net":kvsecret["key"]})

# display(dbutils.fs.ls("/mnt/util"))

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ##### Predifined vars to aid in setup

# COMMAND ----------

mstemp = '/dbfs/mnt/util/migrate'
dbmstemp = 'dbfs:/mnt/util/migrate'

# COMMAND ----------

import os
import json

os.environ['MSTMP'] = mstemp
os.environ['DBMSTMP'] = dbmstemp


# COMMAND ----------

# MAGIC %md
# MAGIC Now generate the database and table create scripts.  Technical note about database locationUri values:  If Presto will be sharing this external metastore then it needs databases to have a locationUri like this on Azure - abfss://<file-system-name>@<storage-account-name>.dfs.core.windows.net/ - rather than a dbfs path because it doesn't recognize dbfs

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC #### export metastore ! 

# COMMAND ----------

# The results of the listDatabases catalog command can be displayed with display().  The results of the listTables command cannot
dbs = spark.catalog.listDatabases()
display(dbs)

# COMMAND ----------

# MAGIC %fs
# MAGIC mkdirs dbfs:/mnt/util/migrate

# COMMAND ----------

# MAGIC %fs
# MAGIC mkdirs dbfs:/mnt/util/migrate/tables

# COMMAND ----------

# Generate the database create script - include the location

dbf = open(mstemp + "/metastore_schema_dbs.ddl", "w+")
for db in dbs:
  DDL = "CREATE DATABASE IF NOT EXISTS {} LOCATION '{}'".format(db.name, db.locationUri)
  dbf.write(DDL)
  dbf.write("\n")
dbf.close()


# COMMAND ----------

# MAGIC %md
# MAGIC Create a DBFS location that will only contain the table create scripts.  That way they can all be read in and executed at once.  Note - the below location is a DBFS mount, but any location that can be accessed by multiple clusters in a workspace will do.

# COMMAND ----------

# MAGIC %md
# MAGIC This script will generate the table and view create statements for the new external metastore.  Delta and non-Delta tables need to be treated differently, so this script takes that into account.  This script also takes into account view creation, it ignores temporary views and handles the specialized Hive tables with SERDE configuration (the SHOW CREATE TABLE statement throws an error on those types of tables).  This script creates one table create script per database.

# COMMAND ----------

# Generate the table create script.  This should work both for Delta and non-Delta external tables.  NOTE - Make sure to execute this script with a 7.x cluster because the output format of the "SHOW CREATE TABLE" statement has changed
# NOTE: Temporary tables are ignored. Views are supported.
# Hive tables that were configured with SERDE options are also supported.  These types of tables - used by applications like Presto to look at Delta tables - will error on the SHOW CREATE TABLE statement.
# The exception for those Hive tables is caught, and instead DESCRIBE DETAIL and DESCRIBE are used to construct the DDL for those tables.

for db in dbs:
  f = open(mstemp + "/tables/metastore_schema_{}.ddl".format(db.name), "w+")
  tables = spark.catalog.listTables(db.name)
  for t in tables:
    if t.isTemporary:
      continue
    try:
      DDL = spark.sql("SHOW CREATE TABLE {}.{}".format(db.name, t.name))
      DDLstr = DDL.first()[0]
      # if the create table statement has a "USING DELTA" then do a create statement that only specifies the name and the location so that it will inherit all the properties of the existing delta table at that storage location.  
      if "USING DELTA" in DDLstr.upper():
        deltaDetail = spark.sql("DESCRIBE DETAIL {}.{}".format(db.name, t.name))
        deltaLocation = deltaDetail.select("location").first()[0]
        deltaDDL = "CREATE TABLE IF NOT EXISTS {}.{} USING delta LOCATION '{}'".format(db.name, t.name, deltaLocation)
        f.write(deltaDDL)
      # If the create statement has "CREATE VIEW" then this is a view - modify the creation statement accordingly
      elif "CREATE VIEW" in DDLstr.upper():
        viewDDL = DDLstr.replace("\n"," ")
        viewDDL = viewDDL.replace("CREATE VIEW", "CREATE VIEW IF NOT EXISTS")
        f.write(viewDDL)
      # Else use the create table output, modify the beginning to add "if not exists" to make the script safer.  If the location setting is missing then look it up with the "describe detail" statement and add it
      else:
        nonDeltaDDL = DDLstr.replace("\n"," ")
        nonDeltaDDL = nonDeltaDDL.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
        if "LOCATION" not in nonDeltaDDL.upper():
          nonDeltaDetail = spark.sql("DESCRIBE DETAIL {}.{}".format(db.name, t.name))
          nonDeltaLocation = nonDeltaDetail.select("location").first()[0]
          nonDeltaDDL = nonDeltaDDL + " LOCATION '" + nonDeltaLocation + "'"
        f.write(nonDeltaDDL)
      f.write("\n")
    except:
      hiveTableDetail = spark.sql("DESCRIBE DETAIL {}.{}".format(db.name, t.name))
      hiveTableLocation = hiveTableDetail.select("location").first()[0]
      hiveTableColumns = spark.sql("DESCRIBE {}.{}".format(db.name, t.name))
      columnList = hiveTableColumns.rdd.collect()
      hiveDDL = "CREATE EXTERNAL TABLE IF NOT EXISTS {}.{} (".format(db.name, t.name)
      for row in columnList:
        column = "`" + row["col_name"] + "` " + row["data_type"] + ","
        hiveDDL = hiveDDL + column
      # remove the extra comma after the last column
      hiveDDL2 = hiveDDL[:-1]
      hiveDDL2 = hiveDDL2 + ") ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.SymlinkTextInputFormat' OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat' LOCATION '" + hiveTableLocation + "'"
      f.write(hiveDDL2)
      f.write("\n")
f.close()

# COMMAND ----------

# MAGIC %md
# MAGIC View the scripts in their directory and you can run head on a couple to see what was generated

# COMMAND ----------

# MAGIC %sh
# MAGIC ls -lR /dbfs/mnt/util/migrate

# COMMAND ----------

# MAGIC %md
# MAGIC ##### You will need access to your underlying ADLS for tables - use whatever means you need to to set up access to your underlying storage to be able to back up your existing metastore

# COMMAND ----------

# DBTITLE 0,You will need access to your underlying ADLS for tables
# MAGIC %run ../storageaccess 

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Predifined vars to aid in setup

# COMMAND ----------

dbhostname = "bruce-mysql.mysql.database.azure.com"
databname = "metastore31"
msver = "3.1"
mstemp = '/dbfs/mnt/util/migrate'
dbmstemp = 'dbfs:/mnt/util/migrate'
dbuser = 'bnelson@bruce-mysql'

# COMMAND ----------

# MAGIC %md
# MAGIC List the databases on the new metastore to confirm that only the default exists

# COMMAND ----------

dbs = spark.catalog.listDatabases()
display(dbs)

# COMMAND ----------

# MAGIC %md
# MAGIC These two statements will execute the script that creates the databases

# COMMAND ----------

createDbsDf = spark.read.text(dbmstemp + "/metastore_schema_dbs.ddl")
display(createDbsDf)

# COMMAND ----------

sqlArray = [row.value for row in createDbsDf.collect()]
for sql in sqlArray:
  result = spark.sql(sql)

# COMMAND ----------

# MAGIC %md
# MAGIC Validate that the databases now exist in the new metastore

# COMMAND ----------

dbs = spark.catalog.listDatabases()
display(dbs)

# COMMAND ----------

# MAGIC %md
# MAGIC Confirm the set of tables in the database you're targeting is empty

# COMMAND ----------

# MAGIC %sql
# MAGIC use default;
# MAGIC show tables;

# COMMAND ----------

# MAGIC %md
# MAGIC Now execute the following two statements to run all of the table create scripts.  Note if you want to execute the table create scripts one database at a time you can reference the individual files.

# COMMAND ----------

createTablesDf = spark.read.text(dbmstemp + "/tables/*")
display(createTablesDf)

# COMMAND ----------

sqlArray = [row.value for row in createTablesDf.collect()]
for sql in sqlArray:
  result = spark.sql(sql)

# COMMAND ----------

# MAGIC %md
# MAGIC Confirm the tables were created in each DB on the external metastore

# COMMAND ----------

# MAGIC %sql
# MAGIC use default;
# MAGIC show tables;

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC #### export metastore ! 

# COMMAND ----------

# MAGIC %md
# MAGIC ### Stop here. 