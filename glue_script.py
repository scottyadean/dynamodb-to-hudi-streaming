""" pool for data coming from a kinesis stream
    More info here:
    https://aws.amazon.com/blogs/big-data/build-a-serverless-pipeline-to-analyze-streaming-data-using-aws-glue-apache-hudi-and-amazon-s3/
    Sample Code here:
    https://github.com/aws-samples/aws-glue-streaming-etl-with-apache-hudi/blob/main/glue-streaming-job-script/glue_job_script.py
"""
import sys
import boto3
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.sql.session import SparkSession
#from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
#from pyspark.sql import DataFrame, Row
from pyspark.sql.functions import *
#from pyspark.sql.functions import col, to_timestamp, monotonically_increasing_id, to_date, when
from awsglue import DynamicFrame


RECORD_KEY = 'pk'
PRECOMBINE = 'sk'

ARG_LIST = ["JOB_NAME", "database_name", "kinesis_table_name",
            "starting_position_of_kinesis_iterator", "window_size",
            "hudi_table_name", "connector_name", "s3_path_hudi", "s3_path_spark"]

args = getResolvedOptions(sys.argv, ARG_LIST)

print("*"*200)
print(args)
print("*"*200)


def create_spark_session():
    """ Return spark session context"""
    spark_sess = SparkSession \
        .builder \
        .config('spark.serializer', 'org.apache.spark.serializer.KryoSerializer') \
        .config('spark.sql.hive.convertMetastoreParquet', 'false') \
        .config('spark.sql.legacy.pathOptionBehavior.enabled', 'true') \
        .getOrCreate()
    return spark_sess


# Settings
spark = create_spark_session()
sc = spark.sparkContext
glueContext = GlueContext(sc)
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
database_name = args["database_name"]
kinesis_table_name = args["kinesis_table_name"]
hudi_table_name = args["hudi_table_name"]
s3_path_hudi = args["s3_path_hudi"]
s3_path_spark = args["s3_path_spark"]
connector_name = args["connector_name"]
curr_session = boto3.session.Session()
curr_region = curr_session.region_name

# can be set to "latest", "trim_horizon" or "earliest"
starting_position_of_kinesis_iterator = args["starting_position_of_kinesis_iterator"]

# The amount of time to spend processing each batch
window_size = args["window_size"]

# get dataframe
data_frame_DataSource0 = glueContext.create_data_frame.from_catalog(
    database=database_name,
    table_name=kinesis_table_name,
    transformation_ctx="DataSource0",  # <- I dont understand this
    additional_options={"inferSchema": "true",
                        "startingPosition": starting_position_of_kinesis_iterator}
)


def evolved_schema(kinesis_df, table):
    """ ensure the incoming record has the correct current schema,
        new fresh columns are fine, if a column exists in current
        schema but not in incoming record then manually add before inserting

        You dont have to do get the schema like this you could just return
        a static schema.
    """
    try:
        print("Table: ", table)
        # get existing table's schema
        glue_catalog_df = spark.sql(f"SELECT * FROM {table} LIMIT 0")
        # sanitize for hudi specific system columns
        columns_to_drop = ['_hoodie_commit_time', '_hoodie_commit_seqno', '_hoodie_record_key',
                           '_hoodie_partition_path', '_hoodie_file_name']
        glue_catalog_df_sanitized = glue_catalog_df.drop(*columns_to_drop)
        if (kinesis_df.schema != glue_catalog_df_sanitized.schema):
            merged_df = kinesis_df.unionByName(
                glue_catalog_df_sanitized, allowMissingColumns=True)
        return (merged_df)
    except Exception as err:
        print(err)
        return (kinesis_df)


def process_batch(data_frame, batch_id):
    """ This method is passed to the glue forEachBatch generator callback  """
    print(batch_id)
    if data_frame.count() > 0:
        kinesis_dynamic_frame = DynamicFrame.fromDF(
            data_frame, glueContext, "from_kinesis_data_frame")
        kinesis_data_frame = kinesis_dynamic_frame.toDF()

        kinesis_data_frame = evolved_schema(
            kinesis_data_frame, f"{database_name}.{hudi_table_name}")

        glueContext.write_dynamic_frame.from_options(
            frame=DynamicFrame.fromDF(
                kinesis_data_frame, glueContext, "evolved_kinesis_data_frame"),
            connection_type="marketplace.spark",
            connection_options={
                "path": s3_path_hudi,
                "connectionName": connector_name,
                "hoodie.datasource.write.storage.type": "COPY_ON_WRITE",
                'className': 'org.apache.hudi',
                'hoodie.table.name': hudi_table_name,
                'hoodie.datasource.write.recordkey.field': RECORD_KEY,
                'hoodie.datasource.write.table.name': hudi_table_name,
                'hoodie.datasource.write.operation': 'upsert',
                'hoodie.datasource.write.precombine.field': PRECOMBINE,
                'hoodie.datasource.hive_sync.enable': 'true',
                "hoodie.datasource.hive_sync.mode": "hms",
                'hoodie.datasource.hive_sync.sync_as_datasource': 'false',
                'hoodie.datasource.hive_sync.database': database_name,
                'hoodie.datasource.hive_sync.table': hudi_table_name,
                'hoodie.datasource.hive_sync.use_jdbc': 'false',
                'hoodie.datasource.hive_sync.partition_extractor_class': 'org.apache.hudi.hive.MultiPartKeysValueExtractor',
                'hoodie.datasource.write.hive_style_partitioning': 'true',
                'hoodie.write.concurrency.mode': 'optimistic_concurrency_control', 'hoodie.cleaner.policy.failed.writes': 'LAZY', 'hoodie.write.lock.provider': 'org.apache.hudi.aws.transaction.lock.DynamoDBBasedLockProvider', 'hoodie.write.lock.dynamodb.table': 'hudi-lock-table', 'hoodie.write.lock.dynamodb.partition_key': 'tablename', 'hoodie.write.lock.dynamodb.region': f'{curr_region}', 'hoodie.write.lock.dynamodb.endpoint_url': f'dynamodb.{curr_region}.amazonaws.com', 'hoodie.write.lock.dynamodb.billing_mode': 'PAY_PER_REQUEST', 'hoodie.bulkinsert.shuffle.parallelism': 2000
            }
        )


# For New Records in Stream
glueContext.forEachBatch(
    frame=data_frame_DataSource0,
    batch_function=process_batch,
    options={
        "windowSize": window_size,
        "checkpointLocation": s3_path_spark
    }
)

job.commit()
