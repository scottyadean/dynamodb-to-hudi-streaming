""" process incoming stream """
import os
import json
import random
import base64
from datetime import datetime

from utils.aws_helpers import boto_connect
from utils.date_helpers import get_year_month_day
from utils.dict_helpers import decode_json, flatten_dict
from utils.dict_helpers import CustomJsonEncoder
from utils.stream_helpers import get_dynamodb_stream_image


def stream_handler(event, _):
    """" handle in coming stream from dynamodb table """
    print("event", event)

    for record in event["Records"]:
        process_record(record)

    print(f"Record Count: {len(event['Records'])} ")


def process_record(record):
    """ transform each record passed by the event stream """
    payload = json.loads(base64.b64decode(record["kinesis"]["data"]))
    event_name = payload.get("eventName")
    json_data = get_dynamodb_stream_image(event_name, payload)
    print(f"payload {payload}:{type(payload)} | event:{event_name}")

    if json_data is not None:
        # get the dynamodb encoded record from the payload.
        data = decode_json(json_data)
        print("data", data)

        # fake Record ETL
        data["awsRegion"] = payload.pop("awsRegion")
        data["eventID"] = payload.pop("eventID")
        data["eventName"] = payload.pop("eventName")
        data["eventSource"] = payload.pop("eventSource")
        year, month, day = get_year_month_day()
        data["year"] = year
        data["month"] = month
        data["day"] = day
        data["date"] = datetime.now().strftime('%Y-%m-%d')

        # Flatten the json data into a table.
        json_dict = json.loads(json.dumps(data, cls=CustomJsonEncoder))
        table_data = flatten_dict(json_dict)
        print("flatten table data", table_data)

        # Connect to the Stream and push the data into the Kinesis Table
        # Note the Glue Job will read data from the Table and send it to our Lake
        kinesis_client = boto_connect('kinesis', os.getenv("REGION"))
        res = kinesis_client.put_record(
            StreamName=os.getenv("STREAM_TO_HUDI"),
            Data=json.dumps(table_data),
            PartitionKey=str(random.randint(1, 10))
        )

        print("response", res)
        print(
            f"data sent to kinesis stream {os.getenv('STREAM_TO_HUDI')}", table_data)
