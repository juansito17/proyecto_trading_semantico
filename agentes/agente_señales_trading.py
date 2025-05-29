# agentes/agente_señales_trading.py
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

class AgenteseñalesTrading:
    def __init__(self, rdf_manager: RDFManagerTrading, agente_estrategia: AgentePerfilEstrategia):
        self.rdf_manager = rdf_manager
        self.agente_estrategia = agente_estrategia
        self.ns = rdf_manager.ns_manager

    def _crear_uri_valor_indicador(self, par_mercado_local: str, config_indicador_local_id: str) -> URIRef:
        timestamp_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        id_local = f"ValorInd_{par_mercado_local}_{config_indicador_local_id}_{timestamp_id}_{str(uuid.uuid4())[:4]}"
        return self.ns.get_uri(id_local)

    def _crear_uri_señal_tecnica(self, par_mercado_local: str, tipo_señal: str) -> URIRef:
        timestamp_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        id_local = f"señal_{par_mercado_local}_{tipo_señal}_{timestamp_id}_{str(uuid.uuid4())[:4]}"
        return self.ns.get_uri(id_local)

    def _crear_uri_recomendacion(self, par_mercado_local: str) -> URIRef:
        timestamp_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        id_local = f"Recom_{par_mercado_local}_{timestamp_id}_{str(uuid.uuid4())[:4]}"
        return self.ns.get_uri(id_local)

    def _interpretar_y_almacenar_señales(self, par_mercado_uri: URIRef, par_mercado_local_id: str, valores_indicadores_calculados: dict, precio_actual: float, timestamp_actual_utc: datetime):
        print("\nInterpretando y almacenando señales técnicas...")
        señales_generadas_uris = []

        # Interpretación para RSI
        rsi_config_id = "ConfigRSI14"
        if rsi_config_id in valores_indicadores_calculados and valores_indicadores_calculados[rsi_config_id].get('valorNumerico') is not None:
            rsi_valor = valores_indicadores_calculados[rsi_config_id]['valorNumerico']
            uri_valor_rsi = valores_indicadores_calculados[rsi_config_id]['uri_valor_ind']
            tipo_señal_str = None
            desc_señal = ""

            if rsi_valor < 30:
                tipo_señal_str = "SOBREVENTA_RSI"
                desc_señal = f"RSI ({rsi_valor:.2f}) indica sobreventa para {par_mercado_local_id}."
            elif rsi_valor > 70:
                tipo_señal_str = "SOBRECOMPRA_RSI"
                desc_señal = f"RSI ({rsi_valor:.2f}) indica sobrecompra para {par_mercado_local_id}."
            elif rsi_valor < 40:  # Añadimos señales más sensibles
                tipo_señal_str = "TENDENCIA_BAJISTA_RSI"
                desc_señal = f"RSI ({rsi_valor:.2f}) indica tendencia bajista para {par_mercado_local_id}."
            elif rsi_valor > 60:
                tipo_señal_str = "TENDENCIA_ALCISTA_RSI"
                desc_señal = f"RSI ({rsi_valor:.2f}) indica tendencia alcista para {par_mercado_local_id}."
            
            if tipo_señal_str:
                señal_uri = self._crear_uri_señal_tecnica(par_mercado_local_id, tipo_señal_str)
                self.rdf_manager.agregar_tripleta(señal_uri, RDF.type, self.ns.trade.señalTecnica)
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.generadaPorIndicador, uri_valor_rsi)
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.referenteA, par_mercado_uri)
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.tiposeñal, Literal(tipo_señal_str))
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.descripcionseñal, Literal(desc_señal))
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.fechaseñal, Literal(timestamp_actual_utc.isoformat(), datatype=XSD.dateTime))
                señales_generadas_uris.append(señal_uri)
                print(f"  Señal generada: {desc_señal}")

        # Interpretación para SMA20
        sma20_config_id = "ConfigSMA20"
        if sma20_config_id in valores_indicadores_calculados and valores_indicadores_calculados[sma20_config_id].get('valorNumerico') is not None:
            sma20_valor = valores_indicadores_calculados[sma20_config_id]['valorNumerico']
            uri_valor_sma20 = valores_indicadores_calculados[sma20_config_id]['uri_valor_ind']
            tipo_señal_str = None
            desc_señal = ""

            diferencia_porcentual = ((precio_actual - sma20_valor) / sma20_valor) * 100
            if diferencia_porcentual > 2:  # Precio 2% por encima de SMA20
                tipo_señal_str = "FUERTE_TENDENCIA_ALCISTA_SMA"
                desc_señal = f"Precio ({precio_actual:.4f}) está {diferencia_porcentual:.1f}% por encima de SMA20 ({sma20_valor:.4f}) para {par_mercado_local_id}."
            elif diferencia_porcentual > 0:
                tipo_señal_str = "TENDENCIA_ALCISTA_SMA"
                desc_señal = f"Precio ({precio_actual:.4f}) está {diferencia_porcentual:.1f}% por encima de SMA20 ({sma20_valor:.4f}) para {par_mercado_local_id}."
            elif diferencia_porcentual < -2:  # Precio 2% por debajo de SMA20
                tipo_señal_str = "FUERTE_TENDENCIA_BAJISTA_SMA"
                desc_señal = f"Precio ({precio_actual:.4f}) está {abs(diferencia_porcentual):.1f}% por debajo de SMA20 ({sma20_valor:.4f}) para {par_mercado_local_id}."
            else:
                tipo_señal_str = "TENDENCIA_BAJISTA_SMA"
                desc_señal = f"Precio ({precio_actual:.4f}) está {abs(diferencia_porcentual):.1f}% por debajo de SMA20 ({sma20_valor:.4f}) para {par_mercado_local_id}."

            if tipo_señal_str:
                señal_uri = self._crear_uri_señal_tecnica(par_mercado_local_id, tipo_señal_str)
                self.rdf_manager.agregar_tripleta(señal_uri, RDF.type, self.ns.trade.señalTecnica)
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.generadaPorIndicador, uri_valor_sma20)
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.referenteA, par_mercado_uri)
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.tiposeñal, Literal(tipo_señal_str))
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.descripcionseñal, Literal(desc_señal))
                self.rdf_manager.agregar_tripleta(señal_uri, self.ns.trade.fechaseñal, Literal(timestamp_actual_utc.isoformat(), datatype=XSD.dateTime))
                señales_generadas_uris.append(señal_uri)
                print(f"  Señal generada: {desc_señal}")

        return señales_generadas_uris

    def _generar_y_almacenar_recomendacion(self, par_mercado_uri: URIRef, par_mercado_local_id: str, estrategia_uri: URIRef, señales_activas_uris: list, timestamp_actual_utc: datetime):
        print("\nGenerando recomendación de trading...")
        accion_sugerida = "MANTENER"
        justificacion = "No hay suficientes señales claras para una acción."
        confianza = 0.5
        
        tipos_señales_activas = []
        if señales_activas_uris:
            for señal_uri in señales_activas_uris:
                q_tipo_señal = f"SELECT ?tipo WHERE {{ <{señal_uri}> <{self.ns.trade.tiposeñal}> ?tipo . }}"
                res_tipo = self.rdf_manager.ejecutar_sparql(q_tipo_señal)
                if res_tipo:
                    for r in res_tipo:
                        tipos_señales_activas.append(str(r["tipo"]))
        
        print(f"  Tipos de señales activas para decisión: {tipos_señales_activas}")

        # Lógica mejorada de decisión
        señales_alcistas = ["SOBREVENTA_RSI", "TENDENCIA_ALCISTA_RSI", "TENDENCIA_ALCISTA_SMA", "FUERTE_TENDENCIA_ALCISTA_SMA"]
        señales_bajistas = ["SOBRECOMPRA_RSI", "TENDENCIA_BAJISTA_RSI", "TENDENCIA_BAJISTA_SMA", "FUERTE_TENDENCIA_BAJISTA_SMA"]
        
        señales_alcistas_count = sum(1 for s in tipos_señales_activas if s in señales_alcistas)
        señales_bajistas_count = sum(1 for s in tipos_señales_activas if s in señales_bajistas)
        
        if señales_alcistas_count >= 2:
            accion_sugerida = "COMPRAR"
            justificacion = f"Se detectaron {señales_alcistas_count} señales alcistas: " + ", ".join([s for s in tipos_señales_activas if s in señales_alcistas])
            confianza = min(0.5 + (señales_alcistas_count * 0.1), 0.9)
        elif señales_bajistas_count >= 2:
            accion_sugerida = "VENDER"
            justificacion = f"Se detectaron {señales_bajistas_count} señales bajistas: " + ", ".join([s for s in tipos_señales_activas if s in señales_bajistas])
            confianza = min(0.5 + (señales_bajistas_count * 0.1), 0.9)
        elif señales_alcistas_count == 1:
            accion_sugerida = "COMPRAR"
            justificacion = f"Se detectó una señal alcista débil: {next(s for s in tipos_señales_activas if s in señales_alcistas)}"
            confianza = 0.6
        elif señales_bajistas_count == 1:
            accion_sugerida = "VENDER"
            justificacion = f"Se detectó una señal bajista débil: {next(s for s in tipos_señales_activas if s in señales_bajistas)}"
            confianza = 0.6
        
        # Crear y almacenar la recomendación
        recomendacion_uri = self._crear_uri_recomendacion(par_mercado_local_id)
        self.rdf_manager.agregar_tripleta(recomendacion_uri, RDF.type, self.ns.trade.RecomendacionTrading)
        self.rdf_manager.agregar_tripleta(recomendacion_uri, self.ns.trade.paraActivo, par_mercado_uri)
        self.rdf_manager.agregar_tripleta(recomendacion_uri, self.ns.trade.basadaEnEstrategia, estrategia_uri)
        self.rdf_manager.agregar_tripleta(recomendacion_uri, self.ns.trade.accionSugerida, Literal(accion_sugerida))
        self.rdf_manager.agregar_tripleta(recomendacion_uri, self.ns.trade.justificacionDecision, Literal(justificacion))
        self.rdf_manager.agregar_tripleta(recomendacion_uri, self.ns.trade.nivelConfianza, Literal(confianza, datatype=XSD.float))
        self.rdf_manager.agregar_tripleta(recomendacion_uri, self.ns.trade.timestampRecomendacion, Literal(timestamp_actual_utc.isoformat(), datatype=XSD.dateTime))
        
        for señal_uri in señales_activas_uris:
            self.rdf_manager.agregar_tripleta(recomendacion_uri, self.ns.trade.basadaEnseñal, señal_uri)

        print(f"  Recomendación generada: {accion_sugerida} para {par_mercado_local_id}. Justificación: {justificacion}")
        return recomendacion_uri

    def ejecutar_ciclo_analisis(self, nombre_estrategia_local: str = "EstrategiaPredeterminada"):
        print(f"\n--- Iniciando ciclo de análisis del AgenteseñalesTrading para estrategia '{nombre_estrategia_local}' ---")

        estrategia = self.agente_estrategia.obtener_estrategia_activa(nombre_estrategia_local)
        if not estrategia:
            print(f"Error: No se pudo obtener la estrategia '{nombre_estrategia_local}'. Abortando ciclo.")
            return

        par_mercado_uri_str = estrategia["par_mercado_uri"]
        par_mercado_label = estrategia["par_mercado_label"]
        par_mercado_uri = URIRef(par_mercado_uri_str)
        par_mercado_local_id = par_mercado_uri_str.split('#')[-1]
        estrategia_uri = URIRef(estrategia["uri"])

        print(f"Estrategia obtenida: '{estrategia['nombre_display']}' para el par '{par_mercado_label}'")
        if not estrategia["configuraciones_indicadores"]:
            print("Advertencia: La estrategia no tiene configuraciones de indicadores. No se calculará nada.")
        
        limite_datos_historicos = 100 
        datos_historicos_df = it.obtener_datos_historicos_simulados(
            simbolo_par=par_mercado_label, periodo_tiempo="1d", limite=limite_datos_historicos
        )

        if datos_historicos_df is None or datos_historicos_df.empty:
            print(f"Error: No se pudieron obtener datos históricos para '{par_mercado_label}'. Abortando ciclo.")
            return
        
        print(f"Datos históricos (simulados) obtenidos para '{par_mercado_label}'. Última fecha: {datos_historicos_df.index[-1].strftime('%Y-%m-%d')}")
        
        ultimo_precio_cierre = datos_historicos_df['close'].iloc[-1]
        self.rdf_manager.actualizar_precio_par_mercado(par_mercado_uri, float(ultimo_precio_cierre))
        print(f"Precio actual de '{par_mercado_label}' actualizado en RDF a: {ultimo_precio_cierre:.4f}")

        timestamp_actual_utc = datetime.now(timezone.utc)
        valores_indicadores_calculados_para_señales = {} # Para pasar a la interpretación de señales

        for config_ind_data in estrategia["configuraciones_indicadores"]:
            config_indicador_uri = URIRef(config_ind_data["uri"])
            config_indicador_local_id = config_ind_data["nombre_local"]
            nombre_display_indicador = config_ind_data["nombre_display"]
            
            print(f"\nCalculando y almacenando: {nombre_display_indicador} para {par_mercado_label}")

            valor_indicador_inst_uri = self._crear_uri_valor_indicador(par_mercado_local_id, config_indicador_local_id)
            self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, RDF.type, self.ns.trade.ValorIndicador)
            self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.esValorDe, config_indicador_uri)
            self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.seAplicaA, par_mercado_uri)
            self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.timestampValor, Literal(timestamp_actual_utc.isoformat(), datatype=XSD.dateTime))
            
            # Guardar referencia para la interpretación de señales
            valores_indicadores_calculados_para_señales[config_indicador_local_id] = {'uri_valor_ind': valor_indicador_inst_uri}

            periodo, periodo_corto, periodo_largo, periodo_señal_macd, num_std_dev_bb = None, None, None, None, None
            q_params_config = f"PREFIX trade: <{self.ns.trade}> SELECT ?p ?o WHERE {{ <{config_indicador_uri}> ?p ?o . FILTER (?p IN (trade:periodoIndicador, trade:periodoCorto, trade:periodoLargo, trade:periodoseñal, trade:desviacionEstandar)) }}"
            res_params = self.rdf_manager.ejecutar_sparql(q_params_config)
            if res_params:
                for fila_param in res_params:
                    prop, obj = fila_param["p"], fila_param["o"]
                    if prop == self.ns.trade.periodoIndicador: periodo = int(obj)
                    elif prop == self.ns.trade.periodoCorto: periodo_corto = int(obj)
                    elif prop == self.ns.trade.periodoLargo: periodo_largo = int(obj)
                    elif prop == self.ns.trade.periodoseñal: periodo_señal_macd = int(obj)
                    elif prop == self.ns.trade.desviacionEstandar: num_std_dev_bb = float(obj)

            if "SMA" in config_indicador_local_id.upper() and periodo:
                valor_sma = it.calcular_sma(datos_historicos_df['close'], periodo=periodo)
                if valor_sma is not None:
                    self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorNumerico, Literal(valor_sma, datatype=XSD.decimal))
                    valores_indicadores_calculados_para_señales[config_indicador_local_id]['valorNumerico'] = valor_sma
                    print(f"  SMA({periodo}) = {valor_sma:.4f}")
                else: print(f"  SMA({periodo}) = N/A")
            elif "RSI" in config_indicador_local_id.upper() and periodo:
                valor_rsi = it.calcular_rsi(datos_historicos_df['close'], periodo=periodo)
                if valor_rsi is not None:
                    self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorNumerico, Literal(valor_rsi, datatype=XSD.decimal))
                    valores_indicadores_calculados_para_señales[config_indicador_local_id]['valorNumerico'] = valor_rsi
                    print(f"  RSI({periodo}) = {valor_rsi:.2f}")
                else: print(f"  RSI({periodo}) = N/A")
            elif "MACD" in config_indicador_local_id.upper() and periodo_corto and periodo_largo and periodo_señal_macd:
                valores_macd = it.calcular_macd(datos_historicos_df['close'], periodo_corto, periodo_largo, periodo_señal_macd)
                if valores_macd:
                    # Almacenar todos los componentes del MACD
                    if valores_macd.get("macd") is not None: self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorMACD, Literal(valores_macd["macd"], datatype=XSD.decimal))
                    if valores_macd.get("señal") is not None: self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorseñalMACD, Literal(valores_macd["señal"], datatype=XSD.decimal))
                    if valores_macd.get("histograma") is not None: self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorHistogramaMACD, Literal(valores_macd["histograma"], datatype=XSD.decimal))
                    valores_indicadores_calculados_para_señales[config_indicador_local_id].update(valores_macd) # Añade macd, señal, histograma
                    print(f"  MACD = L:{valores_macd.get('macd', 'N/A')}, S:{valores_macd.get('señal', 'N/A')}, H:{valores_macd.get('histograma', 'N/A')}")
                else: print(f"  MACD = N/A")
            elif "BB" in config_indicador_local_id.upper() and periodo and num_std_dev_bb:
                 valores_bb = it.calcular_bandas_bollinger(datos_historicos_df['close'], periodo, int(num_std_dev_bb))
                 if valores_bb:
                    if valores_bb.get("media") is not None: self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorBandaMedia, Literal(valores_bb["media"], datatype=XSD.decimal))
                    if valores_bb.get("superior") is not None: self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorBandaSuperior, Literal(valores_bb["superior"], datatype=XSD.decimal))
                    if valores_bb.get("inferior") is not None: self.rdf_manager.agregar_tripleta(valor_indicador_inst_uri, self.ns.trade.valorBandaInferior, Literal(valores_bb["inferior"], datatype=XSD.decimal))
                    valores_indicadores_calculados_para_señales[config_indicador_local_id].update(valores_bb) # Añade media, superior, inferior
                    print(f"  BB = M:{valores_bb.get('media', 'N/A')}, Sup:{valores_bb.get('superior', 'N/A')}, Inf:{valores_bb.get('inferior', 'N/A')}")
                 else: print(f"  BB = N/A")
            else:
                print(f"  Tipo de indicador '{config_indicador_local_id}' no reconocido o parámetros faltantes.")
        
        # 5. Interpretar Señales Técnicas
        señales_generadas_uris = self._interpretar_y_almacenar_señales(
            par_mercado_uri, 
            par_mercado_local_id, 
            valores_indicadores_calculados_para_señales, 
            float(ultimo_precio_cierre), # Pasar el precio actual
            timestamp_actual_utc
        )
        
        # 6. Generar Recomendación de Trading
        if señales_generadas_uris: # Solo generar recomendación si hubo señales
            self._generar_y_almacenar_recomendacion(
                par_mercado_uri,
                par_mercado_local_id,
                estrategia_uri, # Pasar la URI de la estrategia actual
                señales_generadas_uris,
                timestamp_actual_utc
            )
        else:
            print("\nNo se generaron señales técnicas claras, se emitirá recomendación de MANTENER por defecto.")
            # Crear una recomendación de MANTENER si no hay señales
            recomendacion_mantener_uri = self._crear_uri_recomendacion(par_mercado_local_id)
            self.rdf_manager.agregar_tripleta(recomendacion_mantener_uri, RDF.type, self.ns.trade.RecomendacionTrading)
            self.rdf_manager.agregar_tripleta(recomendacion_mantener_uri, self.ns.trade.paraActivo, par_mercado_uri)
            self.rdf_manager.agregar_tripleta(recomendacion_mantener_uri, self.ns.trade.basadaEnEstrategia, estrategia_uri)
            self.rdf_manager.agregar_tripleta(recomendacion_mantener_uri, self.ns.trade.accionSugerida, Literal("MANTENER"))
            self.rdf_manager.agregar_tripleta(recomendacion_mantener_uri, self.ns.trade.justificacionDecision, Literal("No se identificaron señales técnicas suficientes para una acción clara."))
            self.rdf_manager.agregar_tripleta(recomendacion_mantener_uri, self.ns.trade.nivelConfianza, Literal(0.5, datatype=XSD.float))
            self.rdf_manager.agregar_tripleta(recomendacion_mantener_uri, self.ns.trade.timestampRecomendacion, Literal(timestamp_actual_utc.isoformat(), datatype=XSD.dateTime))


        self.rdf_manager.guardar_datos()
        print(f"--- Ciclo de análisis completado para '{nombre_estrategia_local}'. Valores, señales y recomendación guardados. ---")


# Bloque de prueba
if __name__ == '__main__':
    print("Probando AgenteseñalesTrading...")

    ontologia_f = os.path.join(project_root_dir, 'datos_trading', 'ontologia_trading.ttl')
    datos_muestra_f = os.path.join(project_root_dir, 'datos_trading', 'datos_trading_muestra.ttl')
    persist_f_agente_señales = os.path.join(project_root_dir, 'datos_trading', 'test_agente_señales_persist.ttl')

    if os.path.exists(persist_f_agente_señales):
        try:
            os.remove(persist_f_agente_señales)
            print(f"Archivo de persistencia de prueba anterior '{persist_f_agente_señales}' eliminado.")
        except OSError as e:
            print(f"Error al eliminar el archivo de persistencia '{persist_f_agente_señales}': {e}")

    if not os.path.exists(ontologia_f) or not os.path.exists(datos_muestra_f):
        print(f"ERROR: Faltan archivos de ontología ({ontologia_f}) o datos de muestra ({datos_muestra_f}).")
    else:
        manager = RDFManagerTrading(
            ontologia_path=ontologia_f,
            datos_muestra_path=datos_muestra_f, 
            persist_path=persist_f_agente_señales 
        )
        agente_estrategia_test = AgentePerfilEstrategia(manager)
        agente_señales_test = AgenteseñalesTrading(manager, agente_estrategia_test)

        print("\nVerificando/Definiendo EstrategiaPredeterminada...")
        estrategia_base = agente_estrategia_test.obtener_estrategia_activa("EstrategiaPredeterminada")
        if not estrategia_base or not estrategia_base.get("configuraciones_indicadores"):
            print("EstrategiaPredeterminada no encontrada o sin indicadores, definiéndola...")
            agente_estrategia_test.definir_o_actualizar_estrategia(
                nombre_estrategia_local="EstrategiaPredeterminada",
                nombre_display_estrategia="Estrategia Conservadora WLD (Test señales)",
                par_mercado_local="WLD_USDT",
                uris_config_indicadores=["ConfigSMA20", "ConfigRSI14", "ConfigMACD12_26_9", "ConfigBB20_2"],
                nivel_riesgo="MEDIO",
                horizonte_temporal="CORTO_PLAZO"
            )
        agente_señales_test.ejecutar_ciclo_analisis("EstrategiaPredeterminada")

        print(f"\n--- Verificación de Recomendaciones en el Grafo para WLD_USDT ---")
        query_check_recom = f"""
            PREFIX trade: <{manager.ns_manager.trade}>
            PREFIX rdf: <{RDF}>
            SELECT ?accion ?justificacion ?confianza ?ts (GROUP_CONCAT(DISTINCT STR(?señalBase); separator=", ") AS ?señalesBase)
            WHERE {{
                ?recomInst rdf:type trade:RecomendacionTrading ;
                           trade:paraActivo trade:WLD_USDT ;
                           trade:accionSugerida ?accion ;
                           trade:justificacionDecision ?justificacion ;
                           trade:nivelConfianza ?confianza ;
                           trade:timestampRecomendacion ?ts .
                OPTIONAL {{ ?recomInst trade:basadaEnseñal ?señalBase . }}
            }} 
            GROUP BY ?accion ?justificacion ?confianza ?ts
            ORDER BY DESC(?ts) 
            LIMIT 1
        """
        resultados_recom_obj = manager.ejecutar_sparql(query_check_recom)
        lista_resultados_recom = list(resultados_recom_obj) if resultados_recom_obj else []

        if lista_resultados_recom:
            print("Última recomendación generada:")
            for fila_recom in lista_resultados_recom: # Debería ser solo una
                print(f"  Acción: {fila_recom['accion']}")
                print(f"  Justificación: {fila_recom['justificacion']}")
                print(f"  Confianza: {fila_recom['confianza']}")
                print(f"  Timestamp: {fila_recom['ts']}")
                print(f"  Basada en Señales: {fila_recom.get('señalesBase', 'N/A')}")
        else:
            print("  No se encontró ninguna recomendación para WLD_USDT en el grafo.")
            
        print(f"\nVerifica el archivo de persistencia: {persist_f_agente_señales}")
        print("\nPrueba de AgenteseñalesTrading (con señales y recomendación) completada.")
