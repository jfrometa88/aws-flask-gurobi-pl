#!/bin/bash

# Variables
ROLE_NAME="S3FullAccessRole"
POLICY_NAME="S3FullAccessPolicy"
BUCKET_NAME="flask-pl-bucket"  

# Crear el rol IAM con permisos para EC2
aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}'

echo "Rol IAM $ROLE_NAME creado."

# Crear una política de permisos para acceso completo al bucket S3 específico
aws iam create-policy --policy-name $POLICY_NAME --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [
    {
      \"Effect\": \"Allow\",
      \"Action\": \"s3:*\", 
      \"Resource\": [
        \"arn:aws:s3:::$BUCKET_NAME\",
        \"arn:aws:s3:::$BUCKET_NAME/*\"
      ]
    }
  ]
}"

echo "Política $POLICY_NAME creada."

# Obtener el ARN de la política
POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text)

# Asociar la política al rol
aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn $POLICY_ARN

echo "Política $POLICY_NAME adjuntada al rol $ROLE_NAME."


