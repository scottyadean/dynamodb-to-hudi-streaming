# Serverless Steaming Data

Example of using Servless Framework to Stream data from dynamodb to a Hudi table.

### Project Overview

Sample sls streaming service pipeline

[Read More Info Here:](https://aws.amazon.com/blogs/big-data/build-a-serverless-pipeline-to-analyze-streaming-data-using-aws-glue-apache-hudi-and-amazon-s3/)

### SetUp

- [install nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- nvm install --lts
- nvm use --lts
- npm install -g serverless
- npm install

#### Plugins

[sls-glue](https://www.npmjs.com/package/serverless-glue)

### Diagram

```
[INSERT] -> [DynamoDB] -> [Kinesis stream] -> [Lambda Handler] -> [ETL] -> [Kinesis stream] <- [Glue Streaming Job] -> [ s3 Parquet File ] -> [Hudi Table]
```

### Deploy

Make sure you do an SLS Print First to check the env vars.
`sls print --stage development`

If your ready to deploy use the standard sls deploy
`sls deploy --stage development`

### Things that are not created yet:

I did not create the Kinesis table in the sls because I cant find the cloudformation to make one. You'll have to manually create a new table under the database and set the Data store = Kinesis , Data format = JSON

Check the glue job properties under:
`glue -> jobs -> job name -> job details -> advanced properties`

In the glue job manually set the type to: Spark Straming because the
sls glue-plugin wont do that for some reason. While you are there you might want to set
the Worker type = G0.25X the smallest size for testing.

Under advanced properties in the glue job manually check the option
Use "Glue data catalog as the Hive metastore" = true

Note: Check the hudi connection: <env>-media-hudi-connection on the glue job under the
connection details

### Running the Example:

Start The Job: You will have to manaully start the straming job in the glue admin console on aws: go to your glue job in the aws console, click the Run button in the top right corner
this will start the sreaming job.

Send fake data to your service by calling python generate_fake_data.py
this will push fake data into the sample dynamodb table development-streaming-media-table
and kick off the streaming process. view the streams in lambda and in the Athena table.
