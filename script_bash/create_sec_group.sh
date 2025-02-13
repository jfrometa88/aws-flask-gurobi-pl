#!/bin/bash

# Variables necesarias
SUBNET_ID="subnet-xxxxxxxx"  # Reemplaza con el ID de la Subnet pública
SECURITY_GROUP_NAME="FlaskSecurityGroup"

# Crear el grupo de seguridad
group_id=$(aws ec2 create-security-group \
  --group-name "$SECURITY_GROUP_NAME" \
  --description "Security group for Flask server that allows connections SSH, HTTP, HTTPS y TCP in port 5000 " \
  --vpc-id $(aws ec2 describe-subnets --subnet-ids $SUBNET_ID --query "Subnets[0].VpcId" --output text) \
  --query 'GroupId' --output text)

echo "Security Group creado con ID: $group_id"

# Agregar reglas de entrada al grupo de seguridad
aws ec2 authorize-security-group-ingress --group-id $group_id --protocol tcp --port 22 --cidr 0.0.0.0/0 #para permitir conexión SSH y acceder al command line de la instancia
aws ec2 authorize-security-group-ingress --group-id $group_id --protocol tcp --port 80 --cidr 0.0.0.0/0 #para permitir conexión HTTP desde internet necesaria para configuración
aws ec2 authorize-security-group-ingress --group-id $group_id --protocol tcp --port 443 --cidr 0.0.0.0/0 #para permitir conexión HTTPS desde internet necesaria para configuración
aws ec2 authorize-security-group-ingress --group-id $group_id --protocol tcp --port 5000 --cidr 0.0.0.0/0 #para permitir conexión al servidor Flask desde internet

echo "Reglas de seguridad agregadas al Security Group."