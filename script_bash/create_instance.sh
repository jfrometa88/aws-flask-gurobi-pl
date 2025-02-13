#!/bin/bash

INSTANCE_NAME="FlaskEC2Instance"
ROLE_NAME="S3FullAccessRole" 
AMI_ID="ami-000089c8d02060104"  # Amazon Linux 2 AMI ID en la región us-west-2
INSTANCE_TYPE="t2.micro"
VOLUME_SIZE=8
VOLUME_TYPE="gp3"
IOPS=3000

# Crear la instancia EC2
instance_id=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --subnet-id $SUBNET_ID \
  --security-group-ids $group_id \
  --iam-instance-profile Name=$ROLE_NAME \
  --block-device-mappings "DeviceName=/dev/xvda,Ebs={VolumeSize=$VOLUME_SIZE,VolumeType=$VOLUME_TYPE,Iops=$IOPS}" \
  --user-data file://<(cat <<EOF
#!/bin/bash
sudo yum update -y
sudo yum install -y aws-cli python3-pip
pip3 install flask boto3 gurobipy matplotlib
EOF
) \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value='$INSTANCE_NAME'}]' \
  --query 'Instances[0].InstanceId' --output text)

echo "Instancia EC2 creada con ID: $instance_id"