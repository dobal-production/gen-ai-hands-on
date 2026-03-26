#!/bin/bash
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r '. .Account')
AWS_REGION=$(aws ec2 describe-availability-zones --output text --query 'AvailabilityZones[0].[RegionName]')
EKS_CLUSTER_NAME=fsi-demo-apps
APP_NAME=regulation

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

cTag=$(date +"%G%m%d%H%M%S") 
docker build -t $APP_NAME .
docker tag $APP_NAME:latest $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ocktank/$APP_NAME:$cTag
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ocktank/$APP_NAME:$cTag
echo $cTag