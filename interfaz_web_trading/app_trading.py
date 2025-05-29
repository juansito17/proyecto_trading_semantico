# interfaz_web_trading/app_trading.py
import os
import sys
from flask import Flask, render_template, request, flash, redirect, url_for
from datetime import datetime

current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.abspath(os.path.join(current_script_dir, '..'))
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

from rdf_utils.rdf_manager_trading import RDFManagerTrading
from agentes.agente_perfil_estrategia import AgentePerfilEstrategia
from agentes.agente_senales_trading import AgenteSenalesTrading
from rdflib.namespace import RDF, XSD 

app = Flask(__name__, template_folder='templates', static_folder='../static_trading') 
app.secret_key = os.urandom(24)

ONTOLOGIA_PATH = os.path.join(project_root_dir, 'datos_trading', 'ontologia_trading.ttl')
DATOS_MUESTRA_PATH = os.path.join(project_root_dir, 'datos_trading', 'datos_trading_muestra.ttl')
DATOS_PERSIST_PATH = os.path.join(project_root_dir, 'datos_trading', 'datos_actualizados.ttl') 

try:
    rdf_manager = RDFManagerTrading(
        ontologia_path=ONTOLOGIA_PATH,
        datos_muestra_path=DATOS_MUESTRA_PATH,
        persist_path=DATOS_PERSIST_PATH
    )
    agente_estrategia = AgentePerfilEstrategia(rdf_manager)
    agente_senales = AgenteSenalesTrading(rdf_manager, agente_estrategia)
    print("RDFManager y agentes inicializados correctamente para Flask.")
except Exception as e:
    print(f"Error fatal durante la inicialización de RDF/Agentes en Flask: {e}")
    rdf_manager = None
    agente_estrategia = None
    agente_senales = None

# --- MODIFICADO: Solo WLD_USDT ---
PARES_MERCADO_DEMO = {
    "WLD_USDT": "WLD/USDT"
}
DEFAULT_PAR_MERCADO_ID = "WLD_USDT"

@app.context_processor
def inject_global_vars():
    return dict(
        current_year=datetime.utcnow().year,
        pares_mercado_demo=PARES_MERCADO_DEMO 
        # par_mercado_actual_id ya no es global, se pasa a la plantilla específica
    )

@app.route('/')
def index_redirect():
    return redirect(url_for('dashboard_par', par_mercado_id_local=DEFAULT_PAR_MERCADO_ID))

@app.route('/dashboard/') # Ruta base para el dashboard
@app.route('/dashboard/<par_mercado_id_local>')
def dashboard_par(par_mercado_id_local=DEFAULT_PAR_MERCADO_ID): # Default si no se especifica
    if not rdf_manager or not agente_senales:
        flash("Error: El sistema de análisis no está disponible.", "danger")
        return render_template('error_page_trading.html', mensaje="Error de inicialización del sistema.")

    # Forzar a WLD_USDT si se intenta acceder a otro par o a la ruta base del dashboard
    if par_mercado_id_local != "WLD_USDT":
        return redirect(url_for('dashboard_par', par_mercado_id_local="WLD_USDT"))

    par_mercado_uri = rdf_manager.ns_manager.get_uri(par_mercado_id_local)
    par_mercado_label = PARES_MERCADO_DEMO.get(par_mercado_id_local, par_mercado_id_local)
    
    datos_dashboard = {
        "par_mercado_label": par_mercado_label,
        "par_mercado_id_local": par_mercado_id_local, 
        "precio_actual": "N/A",
        "volumen24h": "N/A",
        "ultima_actualizacion_precio": "N/A",
        "valores_indicadores": [], 
        "ultima_recomendacion": None 
    }

    q_par_info = f"""
        PREFIX trade: <{rdf_manager.ns_manager.trade}>
        SELECT ?precio ?volumen
        WHERE {{
            <{par_mercado_uri}> trade:precioActual ?precio .
            OPTIONAL {{ <{par_mercado_uri}> trade:volumen24h ?volumen . }}
        }} LIMIT 1
    """
    res_par_info = rdf_manager.ejecutar_sparql(q_par_info)
    if res_par_info:
        for fila in res_par_info:
            datos_dashboard["precio_actual"] = f"{float(fila['precio']):.4f}" if fila.get("precio") else "N/A"
            datos_dashboard["volumen24h"] = f"{float(fila.get('volumen', 0)):,.2f}" if fila.get("volumen") else "N/A"
            datos_dashboard["ultima_actualizacion_precio"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    
    q_valores_indicadores = f"""
        PREFIX trade: <{rdf_manager.ns_manager.trade}>
        PREFIX rdf: <{RDF}>
        PREFIX xsd: <{XSD}>
        SELECT ?configNombre ?valorNum ?valorMACD ?valorSenalMACD ?valorHistMACD 
               ?valorBandaMedia ?valorBandaSuperior ?valorBandaInferior ?ts
        WHERE {{
            ?valorIndInst rdf:type trade:ValorIndicador ;
                          trade:seAplicaA <{par_mercado_uri}> ;
                          trade:esValorDe ?configIndURI ;
                          trade:timestampValor ?ts .
            ?configIndURI trade:nombreConfigIndicador ?configNombre .
            
            OPTIONAL {{ ?valorIndInst trade:valorNumerico ?valorNum . }}
            OPTIONAL {{ ?valorIndInst trade:valorMACD ?valorMACD . }}
            OPTIONAL {{ ?valorIndInst trade:valorSenalMACD ?valorSenalMACD . }}
            OPTIONAL {{ ?valorIndInst trade:valorHistogramaMACD ?valorHistMACD . }}
            OPTIONAL {{ ?valorIndInst trade:valorBandaMedia ?valorBandaMedia . }}
            OPTIONAL {{ ?valorIndInst trade:valorBandaSuperior ?valorBandaSuperior . }}
            OPTIONAL {{ ?valorIndInst trade:valorBandaInferior ?valorBandaInferior . }}
        }} 
        ORDER BY DESC(?ts) ?configNombre 
    """
    res_valores_ind = rdf_manager.ejecutar_sparql(q_valores_indicadores)
    indicadores_procesados = {} 
    if res_valores_ind:
        for fila_ind in res_valores_ind:
            nombre_conf = str(fila_ind["configNombre"])
            if nombre_conf not in indicadores_procesados: 
                indicador_display = {"nombre": nombre_conf, "valores": [], "ts": str(fila_ind["ts"])}
                if fila_ind.get("valorNum") is not None:
                    indicador_display["valores"].append(f"Valor: {float(fila_ind['valorNum']):.4f}")
                if fila_ind.get("valorMACD") is not None:
                    indicador_display["valores"].append(f"MACD: {float(fila_ind['valorMACD']):.4f}")
                if fila_ind.get("valorSenalMACD") is not None:
                    indicador_display["valores"].append(f"Señal MACD: {float(fila_ind['valorSenalMACD']):.4f}")
                if fila_ind.get("valorHistMACD") is not None:
                    indicador_display["valores"].append(f"Hist. MACD: {float(fila_ind['valorHistMACD']):.4f}")
                if fila_ind.get("valorBandaMedia") is not None:
                    indicador_display["valores"].append(f"Banda Media: {float(fila_ind['valorBandaMedia']):.4f}")
                if fila_ind.get("valorBandaSuperior") is not None:
                    indicador_display["valores"].append(f"Banda Sup.: {float(fila_ind['valorBandaSuperior']):.4f}")
                if fila_ind.get("valorBandaInferior") is not None:
                    indicador_display["valores"].append(f"Banda Inf.: {float(fila_ind['valorBandaInferior']):.4f}")
                
                if indicador_display["valores"]: 
                    datos_dashboard["valores_indicadores"].append(indicador_display)
                    indicadores_procesados[nombre_conf] = True

    q_ultima_recomendacion = f"""
        PREFIX trade: <{rdf_manager.ns_manager.trade}>
        PREFIX rdf: <{RDF}>
        SELECT ?recomInst ?accion ?justificacion ?confianza ?ts 
               (COALESCE(GROUP_CONCAT(DISTINCT ?desc; separator="; "), "N/A") AS ?senalesDetalle)
        WHERE {{
            ?recomInst rdf:type trade:RecomendacionTrading ;
                       trade:paraActivo <{par_mercado_uri}> ;
                       trade:accionSugerida ?accion ;
                       trade:justificacionDecision ?justificacion ;
                       trade:nivelConfianza ?confianza ;
                       trade:timestampRecomendacion ?ts .
            
            OPTIONAL {{
                ?recomInst trade:basadaEnSenal ?s .
                ?s trade:descripcionSenal ?desc .
            }}
        }}
        GROUP BY ?recomInst ?accion ?justificacion ?confianza ?ts 
        ORDER BY DESC(?ts)
        LIMIT 1
    """
    # print(f"DEBUG: Ejecutando q_ultima_recomendacion para {par_mercado_uri}")
    res_recom = rdf_manager.ejecutar_sparql(q_ultima_recomendacion)
    
    if res_recom:
        lista_res_recom = list(res_recom) 
        # print(f"DEBUG: Resultados de q_ultima_recomendacion: {len(lista_res_recom)} filas.")
        if lista_res_recom:
            fila_recom = lista_res_recom[0] 
            # print(f"DEBUG: Fila de recomendación: {fila_recom.asdict()}")
            datos_dashboard["ultima_recomendacion"] = {
                "accion": str(fila_recom["accion"]),
                "justificacion": str(fila_recom["justificacion"]),
                "confianza": f"{float(fila_recom['confianza']):.2%}" if fila_recom.get("confianza") else "N/A",
                "timestamp": str(fila_recom["ts"]),
                "senales_base": str(fila_recom.get("senalesDetalle", "N/A")) 
            }
    # else:
        # print(f"DEBUG: q_ultima_recomendacion no devolvió resultados (objeto None).")

    return render_template('dashboard_trading.html', data=datos_dashboard, par_mercado_actual_id_for_page=par_mercado_id_local)

@app.route('/ejecutar_ciclo', methods=['POST'])
def ejecutar_ciclo_agente():
    if not agente_senales or not agente_estrategia: 
        flash("Error: Los agentes de análisis o estrategia no están disponibles.", "danger")
        return redirect(request.referrer or url_for('index_redirect'))

    # --- MODIFICADO: El par siempre será WLD_USDT para el ciclo ---
    par_id_actual = "WLD_USDT" 
    nombre_estrategia_a_ejecutar = "EstrategiaPredeterminada"
        
    print(f"DEBUG [ejecutar_ciclo_agente]: Solicitud para ejecutar ciclo para el par: {par_id_actual}")
    print(f"DEBUG [ejecutar_ciclo_agente]: Usando estrategia '{nombre_estrategia_a_ejecutar}' para {par_id_actual}.")
            
    if nombre_estrategia_a_ejecutar:
        # Verificar si la estrategia existe, si no, crearla (importante para la primera ejecución)
        current_strategy_details = agente_estrategia.obtener_estrategia_activa(nombre_estrategia_a_ejecutar)
        if not current_strategy_details:
            print(f"DEBUG [ejecutar_ciclo_agente]: Estrategia '{nombre_estrategia_a_ejecutar}' no encontrada. Intentando crearla...")
            agente_estrategia.definir_o_actualizar_estrategia(
                nombre_estrategia_local=nombre_estrategia_a_ejecutar,
                nombre_display_estrategia="Estrategia Conservadora WLD (Auto-Creada)", # Nombre consistente
                par_mercado_local=par_id_actual, 
                uris_config_indicadores=["ConfigSMA20", "ConfigRSI14", "ConfigMACD12_26_9", "ConfigBB20_2"], 
                nivel_riesgo="MEDIO",
                horizonte_temporal="CORTO_PLAZO"
            )
            # Volver a obtener para confirmar
            if not agente_estrategia.obtener_estrategia_activa(nombre_estrategia_a_ejecutar):
                flash(f"Error crítico al configurar la estrategia '{nombre_estrategia_a_ejecutar}'.", "danger")
                return redirect(url_for('dashboard_par', par_mercado_id_local=par_id_actual))
            print(f"DEBUG [ejecutar_ciclo_agente]: Estrategia '{nombre_estrategia_a_ejecutar}' creada/verificada.")


        try:
            print(f"Ejecutando ciclo de análisis para la estrategia: {nombre_estrategia_a_ejecutar}")
            agente_senales.ejecutar_ciclo_analisis(nombre_estrategia_a_ejecutar)
            flash(f"Ciclo de análisis ejecutado para {PARES_MERCADO_DEMO.get(par_id_actual, par_id_actual)} usando estrategia '{nombre_estrategia_a_ejecutar}'.", "success")
        except Exception as e:
            flash(f"Error al ejecutar el ciclo de análisis: {e}", "danger")
            print(f"Error en ejecutar_ciclo_agente: {e}")
    else: # No debería llegar aquí si par_id_actual siempre es WLD_USDT
        flash(f"No se pudo determinar la estrategia para el par {par_id_actual}.", "warning")
        print(f"WARN [ejecutar_ciclo_agente]: No se ejecutó ciclo para {par_id_actual} porque nombre_estrategia_a_ejecutar es None.")

    return redirect(url_for('dashboard_par', par_mercado_id_local=par_id_actual))

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('error_page_trading.html', mensaje="Página no encontrada (404)."), 404

@app.errorhandler(500)
def error_interno_servidor(e):
    print(f"Error 500: {e}") 
    return render_template('error_page_trading.html', mensaje=f"Error interno del servidor (500): {e}"), 500

if __name__ == '__main__':
    datos_dir = os.path.join(project_root_dir, 'datos_trading')
    if not os.path.exists(datos_dir):
        os.makedirs(datos_dir)
        print(f"Directorio '{datos_dir}' creado por app_trading.py.")
    
    app.run(debug=True, port=5002)
