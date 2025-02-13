#!/bin/bash

BUCKET_NAME="flask-pl-bucket"
aws s3api create-bucket --bucket $BUCKET_NAME --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2
echo "Bucket S3 creado: $BUCKET_NAME"

# Crear carpetas dentro del bucket
aws s3api put-object --bucket $BUCKET_NAME --key "input/"
aws s3api put-object --bucket $BUCKET_NAME --key "output/"
echo "Carpetas /input/ y /output/ creadas en el bucket $BUCKET_NAME"