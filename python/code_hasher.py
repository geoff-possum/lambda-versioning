import boto3
from botocore.vendored import requests
from hashlib import sha512
import json
from uuid import uuid4

def send(event, context, response_status, Reason=None, ResponseData=None, PhysicalResourceId=None):
  response_url = event.get('ResponseURL', "")
  json_body = json.dumps({
    'Status' : response_status,
    'Reason' : Reason or 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
    'PhysicalResourceId' :  PhysicalResourceId or context.log_stream_name,
    'StackId' : event.get('StackId', ""),
    'RequestId' : event.get('RequestId', ""),
    'LogicalResourceId' : event.get('LogicalResourceId', ""),
    'NoEcho' : True,
    'Data' : ResponseData})
  headers = {
    'content-type' : '',
    'content-length' : str(len(json_body))
  }
  try:
    print json_body
    response = requests.put(response_url,data=json_body,headers=headers)
    print("Status code: " + response.reason)
  except Exception as e:
    print("Failed to send response to CFN: error executing requests.put: " + str(e))

def hash(code_object):
    m = sha512()
    m.update(bytes(code_object))
    return m.hexdigest()

def build_lambda_object(properties):
    code = {}
    if properties.get('ZipFile', ''):
      code['ZipFile'] = properties['ZipFile']
    else:
      code = {
        'S3Bucket' : properties.get('S3Bucket', ''),
        'S3Key' : properties.get('S3Key', ''),
        'S3ObjectVersion' : properties.get('S3ObjectVersion', '')
      }
    return {
      'Code': code,
      'DeadLetterConfig': properties.get('DeadLetterConfig', {}),
      'Description': properties.get('Description', ''),
      'Environment': properties.get('Environment', { 'Variables' : {} } ),
      'Handler': properties.get('Handler', ''),
      'KmsKeyArn': properties.get('KmsKeyArn', ''),
      'Layers': properties.get('Layers', []),
      'MemorySize': properties.get('MemorySize', ''),
      'ReservedConcurrentExecutions': properties.get('ReservedConcurrentExecutions', 5),
      'Role': properties.get('Role', ''),
      'Runtime': properties.get('Runtime', ''),
      'Timeout': properties.get('Timeout', ''),
      'TracingConfig': properties.get('TracingConfig', { 'Mode' : 'PassThrough' } ),
      'VpcConfig': properties.get('VpcConfig', {})
    }

def get_hash(properties, text):
    try:
        info = build_lambda_object(properties)
        code_hash = hash(info)
        return (
            True, 
            { 
                'Code': info['Code'],
                'CodeHash': code_hash,
                'DeadLetterConfig': info['DeadLetterConfig'],
                'Description': info['Description'],
                'Environment': info['Environment'],
                'Handler': info['Handler'],
                'KmsKeyArn': info['KmsKeyArn'],
                'Layers': info['Layers'],
                'MemorySize': info['MemorySize'],
                'ReservedConcurrentExecutions': info['ReservedConcurrentExecutions'],
                'Role': info['Role'],
                'Runtime': info['Runtime'],
                'Timeout': info['Timeout'],
                'TracingConfig': info['TracingConfig'],
                'VpcConfig': info['VpcConfig']
            },
            "{} Successful".format(text)
        )
    except Exception as e:
        print e
        return (False, {}, "Error during {}: {}".format(text, e))

def lambda_handler(event, context):
  print event
  properties = event.get('ResourceProperties', {})
  physical_resource_id = str(uuid4())
  data = {}
  req_type = event.get('RequestType', "")
  if req_type == 'Create':
    res, data, reason = get_hash(properties, "Create")
  elif req_type == 'Update':
    res, data, reason = get_hash(properties, "Update")
  elif req_type == 'Delete':
    physical_resource_id = properties.get('PhysicalResourceId', '')
    res = True
    reason = "Delete Successful"
  else:
    res = False
    reason = "Unknown operation: " + req_type
  status = "FAILED"
  if res:
    status = "SUCCESS"
  send(event, context, status, Reason=reason, ResponseData=data, PhysicalResourceId=physical_resource_id)
