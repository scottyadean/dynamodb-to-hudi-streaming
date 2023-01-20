""" insert data in to test data every 5 seconds """
import uuid
import time
import boto3
from faker import Faker


def put_data(client, data):
    """ add fake data to the dynamodb table"""
    table = client.Table("development-streaming-media-table")
    return table.put_item(Item=data)


def get_data(faker):
    """ Create a fake order  """
    name = faker.name().split(" ")
    fake_id = str(uuid.uuid4())
    return {
        "first_name": name[0],
        "last_name": name[1],
        "address": faker.address().replace("\n", " "),
        "text": faker.text().replace("\n", " "),
        "pk": fake_id,
        "sk": fake_id,
        "city": faker.city(),
        "state": faker.state()
    }


def generate_data():
    """ start the loop to stream in data """
    faker = Faker()
    session = boto3.Session(
        profile_name='clearcapital-dev', region_name='us-west-2')
    dyndb = session.resource('dynamodb')
    for i in range(1, 20):
        json_data = get_data(faker)
        print(i, " > ", json_data)
        put_data(dyndb, json_data)
        time.sleep(5)


if __name__ == "__main__":
    generate_data()
