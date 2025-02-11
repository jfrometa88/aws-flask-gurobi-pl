import gurobipy as gp
from gurobipy import GRB
import json

def resolver_modelo(datos):
    """
    Recibe un diccionario con los datos del modelo, lo resuelve con Gurobi
    y devuelve un diccionario con los resultados.
    """

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
         for j in materias_primas),
        name='Rest_Disp_MatPrimas'
    )

    # Restricciones: Capacidad instalada de procesos
    problema.addConstrs(
        (gp.quicksum(vars_prod[i] / coef_tecn_capacidad_instal_product[j][i] for i in productos) <= coef_aprov[j] 
         for j in procesos),
        name='Rest_Cap_Procesos'
    )

    # Restricciones: Demanda social mínima
    problema.addConstrs(
        (vars_prod[i] >= demanda_social[i] for i in demanda_social.keys()),
        name='Rest_Demanda_Social'
    )

    # Función objetivo: Maximizar utilidad marginal total
    problema.setObjective(
        gp.quicksum(vars_prod[i] * utilidad_marginal[i] for i in productos), 
        GRB.MAXIMIZE
    )

    # Resolver el modelo
    problema.optimize()

    # Verificar si hay solución óptima
    if problema.status == GRB.OPTIMAL:
        solucion = {i: vars_prod[i].X for i in productos}
        obj_value = problema.objVal
    else:
        solucion = {}
        obj_value = None

    # Construir resultado JSON
    resultado = {
        "status": problema.status,
        "objetivo": obj_value,
        "produccion_optima": solucion
    }

    return resultado
