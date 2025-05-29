# agentes/agente_perfil_estrategia.py
import os
import sys # Importar sys para modificar el path

# --- Modificación para permitir la ejecución directa del script ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.abspath(os.path.join(current_script_dir, '..'))
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)
# --- Fin de la modificación ---

from rdf_utils.rdf_manager_trading import RDFManagerTrading
from rdflib import Literal, URIRef
from rdflib.namespace import XSD, RDF

class AgentePerfilEstrategia:
    def __init__(self, rdf_manager: RDFManagerTrading):
        """
        Inicializa el Agente de Perfil de Estrategia.
        Args:
            rdf_manager (RDFManagerTrading): Instancia del gestor RDF.
        """
        self.rdf_manager = rdf_manager
        self.ns = rdf_manager.ns_manager # El agente SÍ usa self.ns correctamente

    def definir_o_actualizar_estrategia(self,
                                        nombre_estrategia_local: str,
                                        nombre_display_estrategia: str,
                                        par_mercado_local: str, 
                                        uris_config_indicadores: list[str], 
                                        nivel_riesgo: str = "MEDIO", 
                                        horizonte_temporal: str = "CORTO_PLAZO"
                                        ) -> URIRef | None:
        estrategia_uri = self.ns.get_uri(nombre_estrategia_local)
        par_mercado_uri = self.ns.get_uri(par_mercado_local)
        
        triples_a_eliminar = list(self.rdf_manager.graph.triples((estrategia_uri, None, None)))
        for triple in triples_a_eliminar:
            self.rdf_manager.graph.remove(triple)

        self.rdf_manager.agregar_tripleta(estrategia_uri, RDF.type, self.ns.trade.Estrategia)
        self.rdf_manager.agregar_tripleta(estrategia_uri, self.ns.trade.nombreEstrategia, Literal(nombre_display_estrategia, lang="es"))
        self.rdf_manager.agregar_tripleta(estrategia_uri, self.ns.trade.monitoreaPar, par_mercado_uri)
        self.rdf_manager.agregar_tripleta(estrategia_uri, self.ns.trade.nivelRiesgoPreferido, Literal(nivel_riesgo))
        self.rdf_manager.agregar_tripleta(estrategia_uri, self.ns.trade.horizonteTemporal, Literal(horizonte_temporal))

        for config_indicador_local in uris_config_indicadores:
            config_indicador_uri = self.ns.get_uri(config_indicador_local)
            self.rdf_manager.agregar_tripleta(estrategia_uri, self.ns.trade.utilizaConfigIndicador, config_indicador_uri)

        print(f"AgentePerfilEstrategia: Estrategia '{nombre_display_estrategia}' (<{estrategia_uri.split('#')[-1]}>) definida/actualizada.")
        self.rdf_manager.guardar_datos() 
        return estrategia_uri

    def obtener_estrategia_activa(self, nombre_estrategia_local: str = "EstrategiaPredeterminada") -> dict | None:
        estrategia_uri = self.ns.get_uri(nombre_estrategia_local)
        
        query_final = f"""
            PREFIX trade: <{self.ns.trade}>
            PREFIX rdf: <{RDF}>
            SELECT 
                ?nombreEstrategia ?parMonitoreadoURI ?simboloBase ?simboloCotizacion 
                ?nivelRiesgo ?horizonteTemporal
                (GROUP_CONCAT(DISTINCT STR(?configIndicadorURI); separator=",") AS ?configsIndicadoresURIs)
                (GROUP_CONCAT(DISTINCT ?nombreCfgInd; separator="||") AS ?nombresConfigsIndicadores)
            WHERE {{
                <{estrategia_uri}> rdf:type trade:Estrategia ;
                                 trade:nombreEstrategia ?nombreEstrategia ;
                                 trade:monitoreaPar ?parMonitoreadoURI ;
                                 trade:nivelRiesgoPreferido ?nivelRiesgo ;
                                 trade:horizonteTemporal ?horizonteTemporal .
                
                ?parMonitoreadoURI trade:tieneActivoBase ?activoBaseURI ;
                                   trade:tieneActivoCotizacion ?activoCotizacionURI .
                ?activoBaseURI trade:simboloCripto ?simboloBase .
                ?activoCotizacionURI trade:simboloCripto ?simboloCotizacion .
                
                OPTIONAL {{
                    <{estrategia_uri}> trade:utilizaConfigIndicador ?configIndicadorURI .
                    OPTIONAL {{ ?configIndicadorURI trade:nombreConfigIndicador ?nombreCfgInd . }}
                }}
            }}
            GROUP BY ?nombreEstrategia ?parMonitoreadoURI ?simboloBase ?simboloCotizacion ?nivelRiesgo ?horizonteTemporal
            LIMIT 1
        """
        resultados = self.rdf_manager.ejecutar_sparql(query_final)

        if resultados:
            filas = list(resultados)
            if not filas:
                print(f"AgentePerfilEstrategia: No se encontraron detalles (QUERY FINAL vacía) para '{nombre_estrategia_local}'.")
                return None

            fila = filas[0] # Resultado de la consulta (un objeto ResultRow)
            fila_dict = fila.asdict() # Convertir a diccionario para facilitar la verificación de claves

            # print(f"DEBUG: Fila devuelta por SPARQL (como dict): {fila_dict}") # Descomentar para ver todas las claves

            claves_esperadas = ["nombreEstrategia", "parMonitoreadoURI", "simboloBase", 
                                "simboloCotizacion", "nivelRiesgo", "horizonteTemporal"]
            
            claves_faltantes = [k for k in claves_esperadas if k not in fila_dict]

            if claves_faltantes:
                print(f"AgentePerfilEstrategia: Faltan datos esenciales (QUERY FINAL) para '{nombre_estrategia_local}'.")
                print(f"  Claves esperadas pero faltantes en el resultado: {claves_faltantes}")
                print(f"  Claves disponibles en el resultado: {list(fila_dict.keys())}")
                return None

            # Si todas las claves esperadas están, proceder
            configs_uris_str = fila_dict.get("configsIndicadoresURIs")
            nombres_configs_str = fila_dict.get("nombresConfigsIndicadores")
            
            lista_configs = []
            if configs_uris_str and str(configs_uris_str).strip(): 
                uris = str(configs_uris_str).split(',')
                nombres = str(nombres_configs_str).split('||') if nombres_configs_str and str(nombres_configs_str).strip() else [None] * len(uris)
                
                temp_nombres = [None] * len(uris)
                nombres_disponibles = str(nombres_configs_str).split('||') if nombres_configs_str and str(nombres_configs_str).strip() else []
                
                for i, uri_str_val in enumerate(uris):
                    if uri_str_val and uri_str_val.strip():
                        nombre_display_config = nombres[i] if i < len(nombres) and nombres[i] and nombres[i].strip() else uri_str_val.split('#')[-1]
                        lista_configs.append({
                            "uri": uri_str_val,
                            "nombre_local": uri_str_val.split('#')[-1],
                            "nombre_display": nombre_display_config
                        })
            
            estrategia_data = {
                "uri": str(estrategia_uri),
                "nombre_local": nombre_estrategia_local,
                "nombre_display": str(fila_dict["nombreEstrategia"]),
                "par_mercado_uri": str(fila_dict["parMonitoreadoURI"]),
                "par_mercado_label": f"{fila_dict['simboloBase']}/{fila_dict['simboloCotizacion']}",
                "nivel_riesgo": str(fila_dict["nivelRiesgo"]),
                "horizonte_temporal": str(fila_dict["horizonteTemporal"]),
                "configuraciones_indicadores": lista_configs
            }
            print(f"AgentePerfilEstrategia: Estrategia activa recuperada: {estrategia_data['nombre_display']}")
            return estrategia_data
        
        print(f"AgentePerfilEstrategia: No se encontró la estrategia '{nombre_estrategia_local}' (bloque de resultados vacío para QUERY FINAL).")
        return None

# Bloque de prueba
if __name__ == '__main__':
    print("Probando AgentePerfilEstrategia...")

    ontologia_f = os.path.join(project_root_dir, 'datos_trading', 'ontologia_trading.ttl')
    datos_muestra_f = os.path.join(project_root_dir, 'datos_trading', 'datos_trading_muestra.ttl')
    persist_f = os.path.join(project_root_dir, 'datos_trading', 'test_agente_estrategia_persist.ttl')

    if os.path.exists(persist_f):
        try:
            os.remove(persist_f)
            print(f"Archivo de persistencia de prueba anterior '{persist_f}' eliminado.")
        except OSError as e:
            print(f"Error al eliminar el archivo de persistencia de prueba '{persist_f}': {e}")

    if not os.path.exists(ontologia_f) or not os.path.exists(datos_muestra_f):
        print(f"ERROR: Faltan archivos de ontología ({ontologia_f}) o datos de muestra ({datos_muestra_f}). Verifica las rutas.")
    else:
        manager = RDFManagerTrading(
            ontologia_path=ontologia_f,
            datos_muestra_path=datos_muestra_f, 
            persist_path=persist_f 
        )
        agente_estrategia = AgentePerfilEstrategia(manager)

        print(f"\n--- Contenido del grafo después de cargar datos de muestra ({len(manager.graph)} tripletas) ---")
        
        print("\n--- Verificando :EstrategiaPredeterminada en el grafo ---")
        q_check_predet = f"""
            PREFIX trade: <{manager.ns_manager.trade}> 
            PREFIX rdf: <{RDF}>
            ASK {{ <{manager.ns_manager.trade.EstrategiaPredeterminada}> rdf:type trade:Estrategia . }}
            """
        res_check_predet = manager.ejecutar_sparql(q_check_predet)
        print(f":EstrategiaPredeterminada existe como tipo Estrategia: {list(res_check_predet)[0] if res_check_predet else 'Error ASK'}")

        print("\n--- Obteniendo estrategia predeterminada de datos_trading_muestra.ttl ---")
        estrategia_cargada = agente_estrategia.obtener_estrategia_activa("EstrategiaPredeterminada")
        if estrategia_cargada:
            print(f"Estrategia Cargada: {estrategia_cargada['nombre_display']}")
            print(f"  Par Monitoreado: {estrategia_cargada['par_mercado_label']} (<{estrategia_cargada['par_mercado_uri'].split('#')[-1] if estrategia_cargada['par_mercado_uri'] else 'N/A'}>)")
            print(f"  Nivel de Riesgo: {estrategia_cargada['nivel_riesgo']}")
            if estrategia_cargada['configuraciones_indicadores']:
                print(f"  Indicadores Configurados:")
                for cfg_ind in estrategia_cargada['configuraciones_indicadores']:
                    print(f"    - {cfg_ind['nombre_display']} (<{cfg_ind['nombre_local']}>)")
            else:
                print("  No hay indicadores configurados para esta estrategia.")
        else:
            print("No se pudo cargar la EstrategiaPredeterminada. Revisa los DEBUG prints y el archivo datos_trading_muestra.ttl")

        print("\n--- Definiendo una nueva estrategia (o actualizando si ya existe) ---")
        nombre_nueva_estrategia_local = "MiEstrategiaAgresivaBTC"
        uris_indicadores_para_nueva_estrategia = ["ConfigRSI14", "ConfigMACD12_26_9"]
        
        agente_estrategia.definir_o_actualizar_estrategia(
            nombre_estrategia_local=nombre_nueva_estrategia_local,
            nombre_display_estrategia="Estrategia Agresiva para Bitcoin",
            par_mercado_local="BTC_USDT", 
            uris_config_indicadores=uris_indicadores_para_nueva_estrategia, 
            nivel_riesgo="ALTO",
            horizonte_temporal="CORTO_PLAZO"
        )
        
        print(f"\n--- Contenido del grafo después de definir nueva estrategia ({len(manager.graph)} tripletas) ---")

        print("\n--- Verificando :MiEstrategiaAgresivaBTC en el grafo ---")
        q_check_nueva = f"""
            PREFIX trade: <{manager.ns_manager.trade}>
            PREFIX rdf: <{RDF}>
            ASK {{ <{manager.ns_manager.trade.MiEstrategiaAgresivaBTC}> rdf:type trade:Estrategia . }}
            """
        res_check_nueva = manager.ejecutar_sparql(q_check_nueva)
        print(f":MiEstrategiaAgresivaBTC existe como tipo Estrategia: {list(res_check_nueva)[0] if res_check_nueva else 'Error ASK'}")

        print(f"\n--- Obteniendo la nueva estrategia '{nombre_nueva_estrategia_local}' ---")
        nueva_estrategia_obtenida = agente_estrategia.obtener_estrategia_activa(nombre_nueva_estrategia_local)
        if nueva_estrategia_obtenida:
            print(f"Estrategia Obtenida: {nueva_estrategia_obtenida['nombre_display']}")
            print(f"  Par Monitoreado: {nueva_estrategia_obtenida['par_mercado_label']}")
            if nueva_estrategia_obtenida['configuraciones_indicadores']:
                print(f"  Indicadores Configurados:")
                for cfg_ind in nueva_estrategia_obtenida['configuraciones_indicadores']:
                     print(f"    - {cfg_ind['nombre_display']} (<{cfg_ind['nombre_local']}>)")
            else:
                print("  No hay indicadores configurados para la nueva estrategia.")
        else:
            print(f"No se pudo obtener la estrategia '{nombre_nueva_estrategia_local}'. Revisa los DEBUG prints.")
            
        print(f"\nVerifica el archivo de persistencia: {persist_f}")
        print("\nPrueba de AgentePerfilEstrategia completada.")
