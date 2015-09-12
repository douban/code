import json
from vilya.libs.rdstore import rds


def publish(channels, data, pubkey="codelive"):
    rds.publish(pubkey, json.dumps({'channels': channels, 'data': data}))
