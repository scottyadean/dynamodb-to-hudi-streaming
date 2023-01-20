""" Functions Associated with Steams  """


def get_dynamodb_stream_image(event: str, payload: dict):
    """ Get Data Image from dynamodb event stream event object
        :param event <str> event type name
        :param payload <dict> event stream data
    """
    if event.strip().upper() in ["INSERT", "MODIFY"]:
        return payload.get("dynamodb").get("NewImage")

    return payload.get("dynamodb").get("OldImage")
