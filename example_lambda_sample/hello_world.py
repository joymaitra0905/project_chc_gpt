from __future__ import print_function
from edl.utils import dynamodb


def handler(event, context):
    print('hello world')
    print(dynamodb.list_updates('example_iris'))
    print('event: %s' % event)
