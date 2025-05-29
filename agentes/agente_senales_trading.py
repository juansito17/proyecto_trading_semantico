# agentes/agente_senales_trading.py
import os
import sys
from datetime import datetime, timezone
import pandas as pd # Para manejar los datos históricos
import uuid # Para generar URIs únicas

# --- Modificación para permitir la ejecución directa del script ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.abspath(os.path.join(current_script_dir, '..'))
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)
# --- Fin de la modificación ---

from rdf_utils.rdf_manager_trading import RDFManagerTrading
from agentes.agente_perfil_estrategia import AgentePerfilEstrategia # Para obtener la estrategia
from utils import indicadores_tecnicos as it # Importar el módulo de indicadores
from rdflib import Literal, URIRef
from rdflib.namespace import XSD, RDF

class AgenteSenalesTrading:
    def __init__(self, rdf_manager: RDFManagerTrading, agente_estrategia: AgentePerfilEstrategia):
        """
        Inicializa el Agente de Señales de Trading.

        Args:
            rdf_manager (RDFManagerTrading): Instancia del gestor RDF.
            agente_estrategia (AgentePerfilEstrategia): Instancia del agente de perfil de estrategia.
        """
        self.rdf_manager = rdf_manager
        self.agente_estrategia = agente_estrategia
        self.ns = rdf_manager.ns_manager

    def _crear_uri_valor_indicador(self, par_mercado_local: str, config_indicador_local_id: str) -> URIRef:
        """Crea una URI única para una instancia de ValorIndicador."""
        timestamp_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        # Usar config_indicador_local_id en la URI
        id_local = f"ValorInd_{par_mercado_local}_{config_indicador_local_id}_{timestamp_id}_{str(uuid.uuid4())[:4]}"
        return self.ns.get_uri(id_local)

    def ejecutar_ciclo_analisis(self, nombre_estrategia_local: str = "EstrategiaPredeterminada"):
        """
        Ejecuta un ciclo completo de análisis:
        1. Obtiene la estrategia activa.
        2. Obtiene datos de mercado.
        3. Calcula los indicadores definidos en la estrategia.
        4. Almacena los valores de los indicadores en el grafo RDF.
        (Pasos futuros: interpretar señales, generar recomendaciones).
        """
        print(f"\n--- Iniciando ciclo de análisis del AgenteSenalesTrading para estrategia '{nombre_estrategia_local}' ---")

        # 1. Obtener Estrategia Activa
        estrategia = self.agente_estrategia.obtener_estrategia_activa(nombre_estrategia_local)
        if not estrategia:
            print(f"Error: No se pudo obtener la estrategia '{nombre_estrategia_local}'. Abortando ciclo.")
            return

        par_mercado_uri_str = estrategia["par_mercado_uri"]
        par_mercado_label = estrategia["par_mercado_label"] # Ej: "WLD/USDT"
        par_mercado_uri = URIRef(par_mercado_uri_str) # Convertir a URIRef
        par_mercado_local_id = par_mercado_uri_str.split('#')[-1]

        print(f"Estrategia obtenida: '{estrategia['nombre_display']}' para el par '{par_mercado_label}'")
        if not estrategia["configuraciones_indicadores"]:
            print("Advertencia: La estrategia no tiene configuraciones de indicadores. No se calculará nada.")
        
        # 2. Obtener Datos de Mercado (Simulados por ahora)
        limite_datos_historicos = 100 
        datos_historicos_df = it.obtener_datos_historicos_simulados(
            simbolo_par=par_mercado_label,
            periodo_tiempo="1d", 
            limite=limite_datos_historicos
        )

        if datos_historicos_df is None or datos_historicos_df.empty:
            print(f"Error: No se pudieron obtener datos históricos para '{par_mercado_label}'. Abortando ciclo.")
            return
        
        print(f"Datos históricos (simulados) obtenidos para '{par_mercado_label}'. Última fecha: {datos_historicos_df.index[-1].strftime('%Y-%m-%d')}")
        
        ultimo_precio_cierre = datos_historicos_df['close'].iloc[-1]
        self.rdf_manager.actualizar_precio_par_mercado(par_mercado_uri, float(ultimo_precio_cierre))
        print(f"Precio actual de '{par_mercado_label}' actualizado en RDF a: {ultimo_precio_cierre:.4f}")

        # 3. Calcular Indicadores y 4. Almacenar Valores en RDF
        timestamp_actual_utc = datetime.now(timezone.utc)

        for config_ind_data in estrategia["configuraciones_indicadores"]:
            config_indicador_uri = URIRef(config_ind_data["uri"])
            config_indicador_local_id = config_ind_data["nombre_local"] # Esta es la variable correcta
            nombre_display_indicador = config_ind_data["nombre_display"]
            
            print(f"\nCalculando y almacenando: {nombre_display_indicador} para {par_mercado_label}")

            valor_indicador_inst_uri = self._crear_uri_valor_indicador(par_mercado_local_id, config_indicador_local_id)
            self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, RDF.type, self.ns.trade.ValorIndicador)
            self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.esValorDe, config_indicador_uri)
            self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.seAplicaA, par_mercado_uri)
            self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.timestampValor, Literal(timestamp_actual_utc.isoformat(), datatype=XSD.dateTime))
            
            periodo = None
            periodo_corto = None
            periodo_largo = None
            periodo_senal_macd = None
            num_std_dev_bb = None

            q_params_config = f"""
                PREFIX trade: <{self.ns.trade}>
                SELECT ?p ?o
                WHERE {{
                    <{config_indicador_uri}> ?p ?o .
                    FILTER (?p IN (trade:periodoIndicador, trade:periodoCorto, trade:periodoLargo, trade:periodoSenal, trade:desviacionEstandar))
                }}
            """
            res_params = self.rdf_manager.ejecutar_sparql(q_params_config)
            if res_params:
                for fila_param in res_params:
                    prop = fila_param["p"]
                    obj = fila_param["o"]
                    if prop == self.ns.trade.periodoIndicador: periodo = int(obj)
                    elif prop == self.ns.trade.periodoCorto: periodo_corto = int(obj)
                    elif prop == self.ns.trade.periodoLargo: periodo_largo = int(obj)
                    elif prop == self.ns.trade.periodoSenal: periodo_senal_macd = int(obj)
                    elif prop == self.ns.trade.desviacionEstandar: num_std_dev_bb = float(obj)

            # --- CORRECCIÓN AQUÍ ---
            # Usar config_indicador_local_id en lugar de config_indicador_local
            if "SMA" in config_indicador_local_id.upper() and periodo:
                valor_sma = it.calcular_sma(datos_historicos_df['close'], periodo=periodo)
                if valor_sma is not None:
                    self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorNumerico, Literal(valor_sma, datatype=XSD.decimal))
                    print(f"  SMA({periodo}) = {valor_sma:.4f}")
                else: print(f"  SMA({periodo}) = N/A (datos insuficientes o error)")

            elif "RSI" in config_indicador_local_id.upper() and periodo:
                valor_rsi = it.calcular_rsi(datos_historicos_df['close'], periodo=periodo)
                if valor_rsi is not None:
                    self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorNumerico, Literal(valor_rsi, datatype=XSD.decimal))
                    print(f"  RSI({periodo}) = {valor_rsi:.2f}")
                else: print(f"  RSI({periodo}) = N/A (datos insuficientes o error)")
            
            elif "MACD" in config_indicador_local_id.upper() and periodo_corto and periodo_largo and periodo_senal_macd:
                valores_macd = it.calcular_macd(datos_historicos_df['close'], 
                                                periodo_corto=periodo_corto, 
                                                periodo_largo=periodo_largo, 
                                                periodo_senal=periodo_senal_macd)
                if valores_macd:
                    if valores_macd.get("macd") is not None:
                        self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorMACD, Literal(valores_macd["macd"], datatype=XSD.decimal))
                    if valores_macd.get("senal") is not None:
                        self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorSenalMACD, Literal(valores_macd["senal"], datatype=XSD.decimal))
                    if valores_macd.get("histograma") is not None:
                        self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorHistogramaMACD, Literal(valores_macd["histograma"], datatype=XSD.decimal))
                    print(f"  MACD({periodo_corto},{periodo_largo},{periodo_senal_macd}) = L: {valores_macd.get('macd', 'N/A')}, S: {valores_macd.get('senal', 'N/A')}, H: {valores_macd.get('histograma', 'N/A')}")
                else: print(f"  MACD({periodo_corto},{periodo_largo},{periodo_senal_macd}) = N/A (datos insuficientes o error)")

            elif "BB" in config_indicador_local_id.upper() and periodo and num_std_dev_bb: 
                 valores_bb = it.calcular_bandas_bollinger(datos_historicos_df['close'],
                                                          periodo=periodo,
                                                          num_std_dev=int(num_std_dev_bb))
                 if valores_bb:
                    if valores_bb.get("media") is not None:
                        self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorBandaMedia, Literal(valores_bb["media"], datatype=XSD.decimal))
                    if valores_bb.get("superior") is not None:
                        self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorBandaSuperior, Literal(valores_bb["superior"], datatype=XSD.decimal))
                    if valores_bb.get("inferior") is not None:
                        self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorBandaInferior, Literal(valores_bb["inferior"], datatype=XSD.decimal))
                    print(f"  BB({periodo},{num_std_dev_bb}) = M: {valores_bb.get('media', 'N/A')}, Sup: {valores_bb.get('superior', 'N/A')}, Inf: {valores_bb.get('inferior', 'N/A')}")
                 else: print(f"  BB({periodo},{num_std_dev_bb}) = N/A (datos insuficientes o error)")
            
            else:
                # Usar config_indicador_local_id en el mensaje de error
                print(f"  Tipo de indicador '{config_indicador_local_id}' no reconocido o parámetros faltantes para cálculo. Parámetros obtenidos: p={periodo}, pc={periodo_corto}, pl={periodo_largo}, ps={periodo_senal_macd}, std={num_std_dev_bb}")
        
        self.rdf_manager.guardar_datos()
        print(f"--- Ciclo de análisis completado para '{nombre_estrategia_local}'. Valores de indicadores guardados. ---")

# Bloque de prueba
if __name__ == '__main__':
    print("Probando AgenteSenalesTrading...")

    ontologia_f = os.path.join(project_root_dir, 'datos_trading', 'ontologia_trading.ttl')
    datos_muestra_f = os.path.join(project_root_dir, 'datos_trading', 'datos_trading_muestra.ttl')
    persist_f_agente_senales = os.path.join(project_root_dir, 'datos_trading', 'test_agente_senales_persist.ttl')

    if os.path.exists(persist_f_agente_senales):
        try:
            os.remove(persist_f_agente_senales)
            print(f"Archivo de persistencia de prueba anterior '{persist_f_agente_senales}' eliminado.")
        except OSError as e:
            print(f"Error al eliminar el archivo de persistencia '{persist_f_agente_senales}': {e}")

    if not os.path.exists(ontologia_f) or not os.path.exists(datos_muestra_f):
        print(f"ERROR: Faltan archivos de ontología ({ontologia_f}) o datos de muestra ({datos_muestra_f}).")
    else:
        manager = RDFManagerTrading(
            ontologia_path=ontologia_f,
            datos_muestra_path=datos_muestra_f, 
            persist_path=persist_f_agente_senales 
        )
        agente_estrategia_test = AgentePerfilEstrategia(manager)
        agente_senales_test = AgenteSenalesTrading(manager, agente_estrategia_test)

        print("\nVerificando/Definiendo EstrategiaPredeterminada...")
        estrategia_base = agente_estrategia_test.obtener_estrategia_activa("EstrategiaPredeterminada")
        if not estrategia_base or not estrategia_base.get("configuraciones_indicadores"):
            print("EstrategiaPredeterminada no encontrada o sin indicadores, definiéndola...")
            agente_estrategia_test.definir_o_actualizar_estrategia(
                nombre_estrategia_local="EstrategiaPredeterminada",
                nombre_display_estrategia="Estrategia Conservadora WLD (Test Senales)",
                par_mercado_local="WLD_USDT",
                uris_config_indicadores=["ConfigSMA20", "ConfigRSI14", "ConfigMACD12_26_9", "ConfigBB20_2"],
                nivel_riesgo="MEDIO",
                horizonte_temporal="CORTO_PLAZO"
            )
            estrategia_base = agente_estrategia_test.obtener_estrategia_activa("EstrategiaPredeterminada")
            if not estrategia_base:
                 print("FALLO CRÍTICO: No se pudo definir/cargar EstrategiaPredeterminada para la prueba.")
                 sys.exit(1) 

        agente_senales_test.ejecutar_ciclo_analisis("EstrategiaPredeterminada")

        print(f"\n--- Verificación de Valores de Indicadores en el Grafo para WLD_USDT ---")
        query_check_valores = f"""
            PREFIX trade: <{manager.ns_manager.trade}>
            PREFIX rdf: <{RDF}>
            PREFIX xsd: <{XSD}>
            SELECT ?configNombre ?valorNum ?valorMACD ?valorBandaMedia ?ts
            WHERE {{
                ?valorIndInst rdf:type trade:ValorIndicador ;
                              trade:seAplicaA trade:WLD_USDT ;
                              trade:esValorDe ?configIndURI ;
                              trade:timestampValor ?ts .
                ?configIndURI trade:nombreConfigIndicador ?configNombre .
                OPTIONAL {{ ?valorIndInst trade:valorNumerico ?valorNum . }}
                OPTIONAL {{ ?valorIndInst trade:valorMACD ?valorMACD . }}
                OPTIONAL {{ ?valorIndInst trade:valorBandaMedia ?valorBandaMedia . }}

            }} ORDER BY DESC(?ts) LIMIT 10
        """
        # Re-ejecutar la consulta para obtener resultados frescos
        resultados_check_obj = manager.ejecutar_sparql(query_check_valores)
        
        # Convertir el generador a lista para poder verificar su longitud y iterar múltiples veces si es necesario
        lista_resultados_check = list(resultados_check_obj) if resultados_check_obj else []

        if lista_resultados_check:
            print("Últimos valores de indicadores almacenados:")
            for i, fila in enumerate(lista_resultados_check):
                print(f"  {i+1}. Config: {fila['configNombre']}, Num: {fila.get('valorNum')}, MACD: {fila.get('valorMACD')}, BandaMedia: {fila.get('valorBandaMedia')}, TS: {fila['ts']}")
        else:
            print("  No se encontraron valores de indicadores para WLD_USDT en el grafo (consulta devolvió None, error o lista vacía).")
            
        print(f"\nVerifica el archivo de persistencia: {persist_f_agente_senales}")
        print("\nPrueba de AgenteSenalesTrading (cálculo y almacenamiento de indicadores) completada.")

