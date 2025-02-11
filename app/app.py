from flask import Flask, request, render_template, redirect, url_for
import boto3
import json
import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import io
import base64

# Configuración de AWS S3
S3_BUCKET = "flask-pl-bucket"
INPUT_FOLDER = "input/"
OUTPUT_FOLDER = "output/"

# Cliente S3
s3 = boto3.client('s3', region_name='us-west-2')

# Datos predefinidos
default_data = {
    "productos": ["MT", "CT", "MHT", "HT", "TE", "TT", "FT", "PT", "BT", "RT", "TA", "TiE", "TiEE", "FTi", "MTi", "FC", "RC", "TC", "MM", "CM", "MHM"],
  "productos_social": ["MT", "CT", "MHT", "TiEE", "FTi", "MM", "CM"],
  "materias_primas": ["T", "Ti", "C", "M"],
  "procesos": ["Lim", "Evis", "Coc", "Emp"],
  "utilidad_marginal": {
    "MT": 703.24, "CT": 717.98, "MHT": 478.33, "HT": -863.73, "TE": 29, "TT": 848,
    "FT": 589.37, "PT": 2727.25, "BT": 3365.58, "RT": 2959.38, "TA": 632.88,
    "TiE": 291.1, "TiEE": 321.7, "FTi": 280.48, "MTi": -609.14, "FC": -854.65,
    "RC": -256.04, "TC": 942.38, "MM": 865.57, "CM": 733.5, "MHM": -458.98
  },
  "coef_tecn_prod_mat_prima": {
    "T": {"MT": 1.2, "CT": 0.8, "MHT": 1, "HT": 1.1, "TE": 1.5, "TT": 0.9, "FT": 2, "PT": 1.5, "BT": 1.6, "RT": 1, "TA": 1.1, "TiE": 0, "TiEE": 0, "FTi": 0, "MTi": 0, "FC": 0, "RC": 0, "TC": 0, "MM": 0, "CM": 0, "MHM": 0},
    "Ti": {"MT": 0, "CT": 0, "MHT": 0, "HT": 0, "TE": 0, "TT": 0, "FT": 0, "PT": 0, "BT": 0, "RT": 0, "TA": 0, "TiE": 1.3, "TiEE": 1.5, "FTi": 1.2, "MTi": 1, "FC": 0, "RC": 0, "TC": 0, "MM": 0, "CM": 0, "MHM": 0},
    "C": {"MT": 0, "CT": 0, "MHT": 0, "HT": 0, "TE": 0, "TT": 0, "FT": 0, "PT": 0, "BT": 0, "RT": 0, "TA": 0, "TiE": 0, "TiEE": 0, "FTi": 0, "MTi": 0, "FC": 1.5, "RC": 2, "TC": 1.2, "MM": 0, "CM": 0, "MHM": 0},
    "M": {"MT": 0, "CT": 0, "MHT": 0, "HT": 0, "TE": 0, "TT": 0, "FT": 0, "PT": 0, "BT": 0, "RT": 0, "TA": 0, "TiE": 0, "TiEE": 0, "FTi": 0, "MTi": 0, "FC": 0, "RC": 0, "TC": 0, "MM": 1.1, "CM": 1.2, "MHM": 1.1}
  },
  "coef_tecn_capacidad_instal_product": {
    "Lim": {"MT":600,"CT":800,"MHT":700,"HT":200,"TE":500,"TT":600,"FT":2000,"PT":1500,"BT":600,"RT":1000,"TA":1100,"TiE":300,"TiEE":850,"FTi":1000,"MTi":1000,"FC":1500,"RC":250,"TC":1200,"MM":1000,"CM":1200,"MHM":300},
    "Evis": {"MT":600,"CT":800,"MHT":700,"HT":200,"TE":500,"TT":600,"FT":2000,"PT":1500,"BT":600,"RT":1000,"TA":1100,"TiE":300,"TiEE":850,"FTi":1000,"MTi":1000,"FC":1500,"RC":250,"TC":1200,"MM":1000,"CM":1200,"MHM":300},
    "Coc": {"MT":600,"CT":800,"MHT":700,"HT":200,"TE":500,"TT":600,"FT":2000,"PT":1500,"BT":600,"RT":1000,"TA":1100,"TiE":300,"TiEE":850,"FTi":1000,"MTi":1000,"FC":1500,"RC":250,"TC":1200,"MM":1000,"CM":1200,"MHM":300},
    "Emp": {"MT":600,"CT":800,"MHT":700,"HT":200,"TE":500,"TT":600,"FT":2000,"PT":1500,"BT":600,"RT":1000,"TA":1100,"TiE":300,"TiEE":850,"FTi":1000,"MTi":1000,"FC":1500,"RC":250,"TC":1200,"MM":1000,"CM":1200,"MHM":300}
  },
  "disp_mat_prima": {"T": 2000, "Ti": 1100, "C": 500, "M": 600},
  "coef_aprov": {"Lim": 0.8, "Evis": 0.9, "Coc": 0.9, "Emp": 0.7},
  "demanda_social": {"MT": 90, "CT": 50, "MHT": 40, "TiEE": 100, "FTi": 60, "MM": 35, "CM": 70}

}

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('form.html', data=default_data, casos=listar_casos())

@app.route('/upload', methods=['POST'])
def upload():
    dataset_id = request.form['dataset_id']
    
    # Construir el JSON con la estructura correcta
    datos = {
        "productos": default_data["productos"],
        "productos_social": default_data["productos_social"],
        "materias_primas": default_data["materias_primas"],
        "procesos": default_data["procesos"],
        "utilidad_marginal": {},
        "disp_mat_prima": {},
        "coef_aprov": default_data["coef_aprov"],
        "demanda_social": default_data["demanda_social"]
    }

    # Extraer los datos del formulario correctamente
    for key, value in request.form.items():
        if key.startswith("utilidad_marginal_"):
            producto = key.replace("utilidad_marginal_", "")
            datos["utilidad_marginal"][producto] = float(value) if value else 0
        elif key.startswith("disp_mat_prima_"):
            materia = key.replace("disp_mat_prima_", "")
            datos["disp_mat_prima"][materia] = float(value) if value else 0
        else:
            pass

    # Agregar coeficientes técnicos predefinidos
    datos["coef_tecn_prod_mat_prima"] = default_data["coef_tecn_prod_mat_prima"]
    datos["coef_tecn_capacidad_instal_product"] = default_data["coef_tecn_capacidad_instal_product"]

    # Guardar los datos en S3 con la estructura correcta
    json_data = json.dumps(datos, indent=4)
    file_name = f"{INPUT_FOLDER}{dataset_id}.json"
    s3.put_object(Bucket=S3_BUCKET, Key=file_name, Body=json_data)

    return redirect(url_for('resolver', dataset_id=dataset_id))


@app.route('/resolver/<dataset_id>')
def resolver(dataset_id):
    # Cargar datos desde S3
    file_name = f"{INPUT_FOLDER}{dataset_id}.json"
    obj = s3.get_object(Bucket=S3_BUCKET, Key=file_name)
    datos = json.loads(obj['Body'].read().decode('utf-8'))

    # Resolver el modelo
    resultado = resolver_modelo(datos)

    # Guardar la solución en S3
    output_file = f"{OUTPUT_FOLDER}{dataset_id}.json"
    s3.put_object(Bucket=S3_BUCKET, Key=output_file, Body=json.dumps(resultado))

    return render_template('resultado.html', resultado=resultado, grafico=grafico_barras(resultado))

@app.route('/cargar/<dataset_id>')
def cargar(dataset_id):
    input_file = f"{INPUT_FOLDER}{dataset_id}.json"
    output_file = f"{OUTPUT_FOLDER}{dataset_id}.json"

    datos_input = json.loads(s3.get_object(Bucket=S3_BUCKET, Key=input_file)['Body'].read().decode('utf-8'))
    datos_output = json.loads(s3.get_object(Bucket=S3_BUCKET, Key=output_file)['Body'].read().decode('utf-8'))

    return render_template('form.html', data=datos_input, resultado=datos_output, casos=listar_casos(), readonly=True)

def listar_casos():
    """ Lista los archivos en la carpeta input de S3 """
    objects = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=INPUT_FOLDER)
    return [obj['Key'].split('/')[-1].replace('.json', '') for obj in objects.get('Contents', [])]

def resolver_modelo(datos):
    """ Implementación del modelo en Gurobi con todas las restricciones """

    # Extraer datos del JSON
    productos = datos["productos"]
    materias_primas = datos["materias_primas"]
    procesos = datos["procesos"]
    utilidad_marginal = datos["utilidad_marginal"]
    coef_tecn_prod_mat_prima = datos["coef_tecn_prod_mat_prima"]
    coef_tecn_capacidad_instal_product = datos["coef_tecn_capacidad_instal_product"]  
    disp_mat_prima = datos["disp_mat_prima"]
    coef_aprov = datos["coef_aprov"]
    demanda_social = datos["demanda_social"]

    # Crear el modelo
    problema = gp.Model("Plan de Producción")

    # Variables de decisión: cantidad a producir por producto
    vars_prod = problema.addVars(productos, name='Cant_Product', lb=0)

    # Restricciones: Disponibilidad de materias primas
    problema.addConstrs(
        (gp.quicksum(vars_prod[i] * coef_tecn_prod_mat_prima[j][i] for i in productos) <= disp_mat_prima[j]
         for j in materias_primas if j in coef_tecn_prod_mat_prima), 
        name='Rest_Disp_MatPrimas'
    )

    # Restricciones: Capacidad instalada de procesos
    problema.addConstrs(
        (gp.quicksum(vars_prod[i] / coef_tecn_capacidad_instal_product[j][i] 
                     for i in productos) <= coef_aprov[j]
         for j in procesos if j in coef_tecn_capacidad_instal_product),  
        name='Rest_Cap_Procesos'
    )

    # Restricciones: Demanda social mínima
    problema.addConstrs(
        (vars_prod[i] >= demanda_social.get(i, 0) for i in demanda_social.keys()),  
        name='Rest_Demanda_Social'
    )

    # Función objetivo: Maximizar utilidad marginal total
    problema.setObjective(
        gp.quicksum(vars_prod[i] * utilidad_marginal.get(i, 0) for i in productos),  
        GRB.MAXIMIZE
    )

    # Resolver el modelo
    problema.optimize()

    # Verificar si hay solución óptima
    if problema.status == GRB.OPTIMAL:
        solucion = {i: vars_prod[i].X for i in productos}
        obj_value = problema.objVal
    elif problema.status == GRB.INFEASIBLE:
        problema.computeIIS()
        problema.write("modelo_infactible.ilp")
        return {
            "status": "Infactible",
            "mensaje": "El modelo no tiene solución factible. Revisa las restricciones.",
            "produccion_optima": {},
            "objetivo": None
        }
    else:
        return {
            "status": "Sin solución",
            "mensaje": "Gurobi no encontró una solución válida.",
            "produccion_optima": {},
            "objetivo": None
        }

    return {
        "status": "Óptimo",
        "objetivo": obj_value,
        "produccion_optima": solucion
    }



def grafico_barras(resultado):
    """ Genera un gráfico de barras con los resultados """
    productos = list(resultado["produccion_optima"].keys())
    valores = list(resultado["produccion_optima"].values())

    plt.figure(figsize=(10, 5))
    plt.bar(productos, valores, color='blue')
    plt.xlabel("Productos")
    plt.ylabel("Producción óptima")
    plt.title("Producción óptima por producto")

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
