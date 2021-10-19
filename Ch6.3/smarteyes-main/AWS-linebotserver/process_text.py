import hashlib

from process_light import process_light
from process_distance import process_distance

from util import get_id, get_user_state

def not_implemented_response():
    return {
        'type': 'text',
        'text': '目前還沒有這項功能喔！請稍後再試。'
    }

def process_text(event):
    """Process text and return a dictionary containing the appropriate response.
    Make sure that event is a text message event.
    """
    if event['type'] != 'message' or event['message']['type'] != 'text':
        return not_implemented_response()

    message = event['message']
    text = message['text']
    id = get_id(event['source'])

    response = {}

    user_state = get_user_state(id)
    if user_state == 'light':
        response = process_light(text, id, has_queried_date=True)
    elif user_state == 'distance':
        response = process_distance(text, id, has_queried_date=True)
    else:
        if "光" in text:
            response = process_light(text, id)
        elif "距離" in text:
            response = process_distance(text, id)
        else:
            response = not_implemented_response()

    return response
