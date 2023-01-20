""" helper methods associated to dictionary objects """
import json
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from decimal import Decimal


def decode_json(dynamo_obj: dict) -> dict:
    """Convert a DynamoDB dict into a standard dict."""
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in dynamo_obj.items()}


def encode_json(python_obj: dict) -> dict:
    """Convert a standard dict into a DynamoDB ."""
    serializer = TypeSerializer()
    return {k: serializer.serialize(v) for k, v in python_obj.items()}


def flatten_dict(data, parent_key="", sep="_"):
    """flatten data into a single dict"""
    try:
        items = []
        for key, value in data.items():
            new_key = parent_key + sep + key if parent_key else key
            if isinstance(value, dict):
                items.extend(flatten_dict(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
        return dict(items)
    except Exception as err:
        return {"error": err}


def dict_clean(items):
    """ remove null values from a dict """
    result = {}
    for key, value in items:
        if value is None:
            value = "n/a"
        if value == "None":
            value = "n/a"
        if value == "null":
            value = "n/a"
        if len(str(value)) < 1:
            value = "n/a"
        result[key] = str(value)
    return result


class CustomJsonEncoder(json.JSONEncoder):
    """" this seems pointless could just be a function"""

    def default(self, obj):
        """ set dynamodb decimal type to float """
        if isinstance(obj, Decimal):
            return float(obj)
        return super(CustomJsonEncoder, self).default(obj)
