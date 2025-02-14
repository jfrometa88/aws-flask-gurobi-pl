# Optimización de Producción con programación lineal usando AWS, Python, Flask, Gurobi y Matplotlib    
**Proyecto Beginner en Cloud Computing con AWS**  

## Introducción  
¿Quieres aprender a implementar una aplicación en la nube con **AWS** y resolver modelos de optimización matemática con **Python y Gurobi**? En este proyecto aprenderás a desplegar una infraestructura en AWS desde cero, integrando **EC2, S3 y Flask** en un caso de estudio real.
Este proyecto es parte de una ruta de aprendizaje con enfoque práctico de servicios de **Amazon Web Service (AWS)**, diseñado para principiantes en **Cloud Computing**. El mismo se concibió y probó en un Sandbox de **AWS** diseñado para el aprendizaje y por tanto con restricciones en su uso. Su objetivo es proporcionar una experiencia práctica en el uso de **AWS Management Console y AWS Command Line Interface (CLI)**, con servicios de Cloud Computing como **AWS EC2, S3 y otros servicios asociados como VPC, IAM**. Combinando estos con una implmentación de una aplicación web usando **Python** con **Python SDK para AWS, Gurobi, Matplotlib y Flask** para introducir datos, resolver y acceder a los resultados de un modelo de **optimización matemática de programación lineal** basado en un caso de estudio real (accediendo vía web por Internet).  

**Referencia científica:**  
El modelo matemático está basado en la publicación:  
📄 [Planificación productiva del procesamiento pesquero en Santiago de Cuba mediante programación lineal"](https://dialnet.unirioja.es/servlet/articulo?codigo=9472260).  
*(El PDF del artículo está incluido en este repositorio para consulta académica.)*  
**Nota:** Aunque este modelo está basado en el artículo, los datos utilizados aquí son ficticios y no corresponden a los datos reales de la publicación. También se emplea gurobipy junto al solver con licencia académica no apata para la producción de Gurobi, en vez de pyomo y el solver CBC como en la publicación original.

Para cumplimentar el objetivo trazado se divide el proyecto en 4 fases con una serie de pasos con vista a implementar una arquitectura en la nube de **AWS**. El diseño de la arquitectura se puede observar a continuación:

![Arquitectura](docs/Arch_AWS.png)

🛠️ **Tecnologías utilizadas:**  
-  **AWS Management Console** → Para configurar la arquitectura en la nube.
-  **AWS CLI** → Para configurar la arquitectura en la nube programáticamente.
-  **AWS EC2** → Para implementar servidor que despliegue la aplicación web.
-  **Flask** → Para la interfaz web.
-  **Gurobi** → Para la optimización matemática.
-  **AWS S3** → Para almacenamiento de datos.
-  **Otros servicios de AWS como VPC y IAM** → Para garantizar la funcionalidad y la seguridad de la arquitectura.
-  **Matplotlib** → Para visualización de resultados.  

📂 **Código fuente:** [Repositorio en GitHub](https://github.com/jorgef88/aws-flask-gurobi-pl)  

---

# **Fase 1: Configurar una instancia EC2 en AWS**  
**Objetivo:** Tener una instancia EC2 lista para ejecutar Flask, Matplotlib, Gurobi y conectar con S3.  

### **Pasos a seguir:**  
1. **Configurar credenciales de AWS para poder desplegar la arquitectura:**
```bash
aws configure
```
2. **Crear la VPC y la infraestructura de red necesaria**.  
- Subnet pública, tabla de enrutamiento, Internet Gateway y ACL con permisos de acceso a la red necesarios (En el entorno del Sandbox de AWS se trabajó, la VPC, la subnet pública y los permisos ACL ya están preconfigurados, por lo que no es necesario crearlas manualmente=..  
- Grupo de Seguridad con permisos **SSH** (para acceder al command line de la instancia), **HTTP y HTTPS** (para permitir que la instancia descargue archivos necesarios desde Internet) y **TCP en puerto 5000** (para poder acceder al servidor Flask una vez en funcionamiento).
El código para implementar este paso mediante **AWS CLI** se encuentras en `scripts/create_sec_group.sh` y se muestra a continuación:
```bash
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
```

- IAM Role con permisos restringidos de acceso a S3.  
El código para implementar este paso mediante **AWS CLI** se encuentras en `scripts/create_role.sh` y se muestra a continuación:
``` bash
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
```

3. **Configurar la instancia EC2:**  
- **AMI:** Amazon Linux 2  
- **Tipo:** `t2.micro` (capa gratuita)  
- **Almacenamiento:** 8 GiB, gp3, 3000 IOPS  
- **Acceso:** Llaves SSH y asociación con la subnet pública  
El código para implementar este paso mediante **AWS CLI** se encuentras en `scripts/create_role.sh` y se muestra a continuación:
```bash
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
```
- **Ejecutar el script en la instancia: `scripts/setup_ec2.sh`**.
El script permite instalar los módulos necesarios para la ejecución del proyecto, tales como **Flask, Python SDK para AWS, Gurobipy y Matplotlib**. También permite configurar la licencia de **Gurobi** para el uso del solver por parte de gurobipy.
``` bash
# Descargar y configurar Gurobi (Solo si se tiene una licencia)
cd /home/ec2-user
wget https://packages.gurobi.com/10.0/gurobi10.0.1_linux64.tar.gz
tar -xvzf gurobi10.0.1_linux64.tar.gz
sudo mv gurobi10.0.1_linux64 /opt/gurobi
echo "export GUROBI_HOME=\"/opt/gurobi\"" >> ~/.bashrc
echo "export PATH=\"\$GUROBI_HOME/bin:\$PATH\"" >> ~/.bashrc
echo "export LD_LIBRARY_PATH=\"\$GUROBI_HOME/lib:\$LD_LIBRARY_PATH\"" >> ~/.bashrc
source ~/.bashrc

# Configurar la licencia de Gurobi (Sustituye XXXXX por la clave)
grbgetkey XXXXXXXX-XXXXXXXX-XXXXXXXX
```

---

# **Fase 2: Configurar un Bucket S3 en AWS**  
**Objetivo:** Crear un bucket S3 con permisos adecuados.  

1. Crear un bucket con carpetas:  
- `/input/` → Almacena datos ingresados.  
-`/output/` → Almacena resultados del modelo.
El código para implementar este paso mediante **AWS CLI** se encuentras en `scripts/create_bucket_s3.sh` y se muestra a continuación:
```bash
BUCKET_NAME="flask-pl-bucket"
aws s3api create-bucket --bucket $BUCKET_NAME --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2
echo "Bucket S3 creado: $BUCKET_NAME"

# Crear carpetas dentro del bucket
aws s3api put-object --bucket $BUCKET_NAME --key "input/"
aws s3api put-object --bucket $BUCKET_NAME --key "output/"
echo "Carpetas /input/ y /output/ creadas en el bucket $BUCKET_NAME"
```

2. **Configuración en la aplicación web de Flask `app.py`**

Fragmento de ejemplo del código:
```python
s3.put_object(Bucket=S3_BUCKET, Key=file_name, Body=json.dumps(datos))
```
Un ejemplo, tanto de los datos de entrada como los resultados del modelo almacenados en el bucket de AWS S3 se puede visualizar en las siguientes imágenes:
![input](docs/capturas_AWS/resultado_input_s3.png)
![output](docs/capturas_AWS/resultado_output_s3.png)

---

# **Fase 3: Implementar el modelo de optimización**  
**Objetivo:** Diseñar el modelo de optimización con gurobipy de manera que el usuario interactúe  desde la web.  

- **Definición del modelo en `modelo.py` y `app.py`** 

Fragmento de ejemplo del código:
```python
problema = gp.Model("Plan de Producción")

# Variables de decisión
vars_prod = problema.addVars(productos, name='Cant_Product', lb=0)

# Restricciones
problema.addConstrs(
    (gp.quicksum(vars_prod[i] * coef_tecn_prod_mat_prima[j][i] for i in productos) <= disp_mat_prima[j]
     for j in materias_primas),
    name='Restricción_Materias_P'
)

# Función objetivo
problema.setObjective(
    gp.quicksum(vars_prod[i] * utilidad_marginal[i] for i in productos),
    GRB.MAXIMIZE
)

problema.optimize()
```

**Salida esperada:** Un JSON con la **producción óptima** y el **valor de la función objetivo**.

---

# **Fase 4: Integración de los datos de entrada, la resolución del modelo y los resultados del mismo en una aplicación web con Flask**
Se desarrolló una aplicaci en **Flask** donde los usuarios pueden:  
- **Ingresar datos en un formulario web** (ver `templates/form.html`).  
- **Resolver el modelo con un clic** (ver `templates/form.html`)
- **Visualizar los resultados incluyendo gráfico**(ver `templates/resultado.html`)  

**Ejemplo de código en `app.py`**
```python
@app.route('/resolver/<dataset_id>')
def resolver(dataset_id):
    file_name = f"{INPUT_FOLDER}{dataset_id}.json"
    obj = s3.get_object(Bucket=S3_BUCKET, Key=file_name)
    datos = json.loads(obj['Body'].read().decode('utf-8'))

    resultado = resolver_modelo(datos)
    s3.put_object(Bucket=S3_BUCKET, Key=f"{OUTPUT_FOLDER}{dataset_id}.json", Body=json.dumps(resultado))

    return render_template('resultado.html', resultado=resultado, grafico=grafico_barras(resultado))
```
---
# **Cómo ejecutar la aplicación en EC2**
1. **Conéctate a la instancia EC2:**  
   - Usa SSH con la clave `tu-clave.pem`.
2. **Ubicación del código:**  
   - Subir o crear la aplicación `app.py` y la carpeta `templates` con las plantillas html a `/home/ec2-user/`.
3. **Ejecutar la aplicación:**  
   - Dentro de `/home/ec2-user/`, ejecutar:
     ```bash
     python3 app.py
     ```
4. **Abrir en el navegador:**  
   - `http://TU-IP-PUBLICA:5000/`
Un ejemplo del formulario web para los datos de entrada en la aplicación web de Flask corriendo en el servidor se puede visualizar en las siguientes imágenes:

![form1](docs/capturas_AWS/form1.png)
![form2](docs/capturas_AWS/form2.png)

Un ejemplo la visualización de los resultados del modelo en la aplicación web de Flask corriendo en el servidor se puede visualizar en las siguientes imágenes:

![resultado1](docs/capturas_AWS/resultados1.png)
![resultado2](docs/capturas_AWS/resultados2.png)

---

# 🎯 **Conclusión**
Este proyecto permite a principiantes en **Cloud Computing** experimentar con los servicios de **AWS** en un entorno práctico, combinando optimización matemática con Gurobi y programación web con Python. Aunque, tanto Flask como Gurobi se usan con fines educativos y no están optimizados para producción.

**Posibles mejoras:**  
- Implementar autenticación con AWS Cognito.  
- Implementar el modelo de optimización con **Gurobi** en **AWS Lambda**.
- Desplegar Flask con **Docker** y **AWS ECS**.  
- Mejorar la visualización con **Dash o Streamlit**.  

**¡Dime qué te pareció y si quieres colaborar!** 😃
