""" AWS related methods"""
import os
import boto3


def boto_connect(service, region=None, resource=False):
    """Create a boto3 client.
        :param service <string> name of boto service
        :param region <string> aws region
        :return <object>
    """
    if region is None:
        region = os.environ.get('REGION', 'us-west-2')
    funct = boto3.client if resource is False else boto3.resource
    if 'AWS_SESSION_TOKEN' in os.environ:
        return funct(service, region,
                     aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                     aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
                     aws_session_token=os.environ['AWS_SESSION_TOKEN'])
    if 'AWS_PROFILE' in os.environ:
        session = boto3.Session(
            profile_name=os.environ['AWS_PROFILE'], region_name=region)
        if resource is False:
            return session.client(service, region)
        return session.resource(service, region)
    return funct(service, region)
