# Lambda Versioning

AWS CloudFormation's AWS::Lambda::Function resource does not emit sufficient information for a ChangeSet
to detect modification, and hence create a new AWS::Lambda::Version resource automatically.

This leaves updates to a Lambda function being made only to $LATEST, rather than create a new version.  

This is demonstrated by the [not working CloudFormation template](https://github.com/geoff-possum/lambda-versioning/blob/master/versioning_not_working.cform), which creates a HelloWorld Lambda function.  
Changing any of the code or configuration leaves the Output version arn unchanged.

## Approach

What is required is to somehow trigger a Lambda Version to be created, and this is achieved by two 
Custom Resources, both backed by Lambda Functions:

* First, the Lambda code and its configuration are hashed, so that any changes are detected

* Second, the hash is passed to a version creator, so a change in the hash always triggers a new version 

The implementations are in Python and can be found in the python folder of this project.  These are created
via the CloudFormation template [custom_resource_lambdas.cform"](https://github.com/geoff-possum/lambda-versioning/blob/master/custom_resource_lambdas.cform), and generate Exports which can then be
imported to other templates.

The revised CloudFormation [template](https://github.com/geoff-possum/lambda-versioning/blob/master/versioning_working.cform) to manage versions on the HelloWorld Lambda function now includes two 
Custom Resources, `Hasher` and `VersionCreator`, which invoke the exported lambdas to perform hashing and
version creation respectively.  The hasher lambda reflects back its properties, which can then be used to
specify the HelloWorld Lambda resource - this approach ensuring that the hash and Lambda function are kept
aligned.

Performing any change to the code or configuration now results in a new version being created.

## Caveats

* Environment variables reflected by the hash function undergo an odd regex test requiring the variable name
to be 2 or more characters long - using a single letter generates an error.  This behaviour is inconsistent
with setting variables via the AWS Console

* VpcConfig must be specified in the properties to `Hasher` or the property should be removed from the 
`Lambda` resource.  This is because there is no default value that can be returned from `Hasher`, that the
AWS::Lambda::Function resource accepts to mean no VPC is being applied.  As a result, the CloudFormation
script includes Parameters for VPC details, and uses Conditions to remove VpcConfig from the `Lambda` 
resource when parameter values are not provided.

* KMS Key Arn is specified as Parameter for flexibility.

* Additional managed policies have been added to the `Role` to ensure smooth updates if VPC or Tracing is
added to the configuration


## Licence

This project is released under the MIT license. See [LICENSE](LICENSE) for details.
