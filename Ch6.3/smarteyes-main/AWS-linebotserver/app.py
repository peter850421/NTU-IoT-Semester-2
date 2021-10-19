import base64
import hashlib
import hmac

import json
import requests

from util import setup_s3_client, setup_dynamodb_resource
from process_text import process_text

channel_access_token = '' # TODO: Line Channel Access Token Here
channel_secret = '' # TODO: Line Channel Secret Here

HEADER = {
    'Content-type': 'application/json',
    'Authorization': 'Bearer ' + channel_access_token
}

def lambda_handler(event, context):
    # parse aws credentials file ./s3_credentials
    # file is in the format of:
    #   [default]
    #   aws_access_key_id=...
    #   aws_secret_access_key=...
    #   aws_session_token=...
    s3_credentials = {}
    with open('s3_credentials', 'r') as reader:
        for line in reader.readlines():
            words = line.split('=')
            if len(words) > 1:
                # has key value
                s3_credentials[words[0].strip()] = words[1].strip()

    dynamodb_credentials = {}
    with open('dynamodb_credentials', 'r') as reader:
        for line in reader.readlines():
            words = line.split('=')
            if len(words) > 1:
                # has key value
                dynamodb_credentials[words[0].strip()] = words[1].strip()

    # perform signature validation to check that the event is actually from Line
    hash = hmac.new(
        channel_secret.encode('utf-8'),
        event['body'].encode('utf-8'),
        hashlib.sha256).digest()
    signature = base64.b64encode(hash)
    print(json.dumps(event))

    # bug in Line where the key 'X-Line-Signature' could be 'x-line-signature'
    if 'X-Line-Signature' in event['headers']:
        x_signature_key = 'X-Line-Signature'
    elif 'x-line-signature' in event['headers']:
        x_signature_key = 'x-line-signature'
    else:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": 'Invalid signature'
            })
        }

    if signature == event['headers'][x_signature_key].encode('utf-8'):
        # if the signature is valid
        # load body of event
        body = json.loads(event['body'])

        # setup AWS S3 and DynamoDB
        setup_s3_client(
            s3_credentials['aws_access_key_id'],
            s3_credentials['aws_secret_access_key'],
            s3_credentials['aws_session_token']
        )
        setup_dynamodb_resource(
            aws_access_key_id=dynamodb_credentials['aws_access_key_id'],
            aws_secret_access_key=dynamodb_credentials['aws_secret_access_key'],
            aws_session_token=dynamodb_credentials['aws_session_token'],
            region_name='us-east-1',
        )

        for event in body['events']:
            # for every Line event
            if event['type'] == 'message':
                # if the event is a message
                message = event['message']
                response = {
                    'replyToken': event['replyToken'],
                    'messages': []
                }

                if message['type'] == 'text':
                    # if the message is text
                    text = message['text']
                    response['messages'].append(process_text(event))
                elif message['type'] == 'sticker':
                    response['messages'].append({
                        'type': 'sticker',
                        'stickerId': message['stickerId'],
                        'packageId': message['packageId']
                    })

                if len(response['messages']) > 0:
                    print(response)
                    response = requests.post('https://api.line.me/v2/bot/message/reply',
                        headers=HEADER,
                        data=json.dumps(response))
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({})
        }

# import json

# def lambda_handler(event, context):
#     # TODO implement
#     return {
#         'statusCode': 200,
#         'body': json.dumps('Hello from Lambda!')
#     }
