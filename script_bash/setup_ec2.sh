#!/bin/bash

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




