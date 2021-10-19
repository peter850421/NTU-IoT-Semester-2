import hashlib
import io
import time

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

s3_client = None
dynamodb_resource = None

def get_user_state(id):
    id_hash = hashlib.sha1(id.encode('utf-8')).hexdigest()[:2]
    object_name = id_hash + '/' + id + '/' + 'state'
    fileobj = download_object('smarteyes-linebotserver', object_name)
    if fileobj is not None:
        return fileobj.getvalue().decode('utf-8')
    else:
        return ""

def set_user_state(id, state):
    id_hash = hashlib.sha1(id.encode('utf-8')).hexdigest()[:2]
    object_name = id_hash + '/' + id + '/' + 'state'
    fileobj = io.BytesIO(state.encode('utf-8'))
    upload_fileobj(fileobj, 'smarteyes-linebotserver', object_name)

def test_s3(s3_client):
    fileobj = io.BytesIO()
    plt.plot([1, 2, 3, 4])
    plt.ylabel('some numbers')
    plt.savefig(fileobj, format='png')
    fileobj.seek(0)

    url = upload_fileobj(fileobj, 'smarteyes-linebotserver', 'tmp.png')
    print(url)

def test_dynamodb(dynamodb_resource):
    low = 1610064000 # GMT 2021-01-08 00:00:00
    high = 1610150399 # GMT 2021-01-08 23:59:59

    print(query_light(low,high))

def setup_s3_client(aws_access_key_id, aws_secret_access_key, aws_session_token):
    global s3_client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )

def setup_dynamodb_resource(aws_access_key_id, aws_secret_access_key, aws_session_token, region_name='us-east-1'):
    global dynamodb_resource
    dynamodb_resource = boto3.resource(
        'dynamodb',
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )

def delete_object(bucket_name, object_name):
    global s3_client
    if not s3_client:
        return None

    try:
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=object_name
        )
    except ClientError as e:
        return None

def download_object(bucket_name, object_name):
    global s3_client
    if not s3_client:
        return None

    try:
        fileobj = io.BytesIO()
        s3_client.download_fileobj(
            bucket_name, object_name, fileobj
        )
        return fileobj
    except ClientError as e:
        return None

def upload_fileobj(fileobj, bucket_name, object_name, expiration=3600):
    """Upload a file-like python object and return its URL
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    global s3_client
    if not s3_client:
        return None

    try:
        s3_client.upload_fileobj(fileobj, bucket_name, object_name)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
    except ClientError as e:
        return None

    return url

def query_light(time_start=0, time_end=time.time()):
    global dynamodb_resource
    if not dynamodb_resource:
        return None

    # search for values within a time range
    table = dynamodb_resource.Table('Light')
    response = table.scan(
        FilterExpression=Attr('Time').between(time_start, time_end)
    )

    # convert each item to float since every number is a Decimal object
    items = [(float(item['Time']), float(item['Value'])) for item in response['Items']]

    return items

def query_distance(time_start=0, time_end=time.time()):
    global dynamodb_resource
    if not dynamodb_resource:
        return None

    # search for values within a time range
    table = dynamodb_resource.Table('Distance')
    response = table.scan(
        FilterExpression=Attr('Time').between(time_start, time_end)
    )

    # convert each item to float since every number is a Decimal object
    items = [(float(item['Time']), float(item['Value'])) for item in response['Items']]

    return items

def get_id(source):
    if source['type'] == 'user':
        # u_ for user
        id = "u_" + source['userId']
    elif source['type'] == 'group':
        # g_ for group
        id = "g_" + source['groupId']
    elif source['type'] == 'room':
        # r_ for room
        id = "r_" + source['roomId']
    else:
        # _ for unidentified
        id = "_"
    return id
