import boto3
from botocore.vendored import requests
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

def new_version(lambda_arn, text):
  try:
    client = boto3.client('lambda')
    return (
      True, 
      { "VersionArn": "{}:{}".format(lambda_arn, client.publish_version(FunctionName=lambda_arn)["Version"]) }, 
      "{} Successful".format(text)
    )
  except Exception as e:
    print e
    return (False, "", "Error during {}: {}".format(text, e))

def lambda_handler(event, context):
  print event
  properties = event.get('ResourceProperties', {})
  arn = properties.get('LambdaFunctionArn', "")
  physical_resource_id = str(uuid4())
  data = {}
  req_type = event.get('RequestType', "")
  if req_type == 'Create':
    res, data, reason = new_version(arn, "Create")
  elif req_type == 'Update':
    res, data, reason = new_version(arn, "Update")
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
 