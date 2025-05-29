# rdf_utils/rdf_manager_trading.py
import os
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
from datetime import datetime
import pandas as pd # Necesario para algunos tipos de datos de indicadores

class RDFManagerTrading:
    def __init__(self, ontologia_path="datos_trading/ontologia_trading.ttl",
                 datos_muestra_path="datos_trading/datos_trading_muestra.ttl",
                 persist_path="datos_trading/datos_actualizados.ttl"):
        """
        Inicializa el gestor RDF para el asistente de trading.
        Carga la ontología y los datos (persistidos o de muestra).

        Args:
            ontologia_path (str): Ruta al archivo de la ontología (.ttl).
            datos_muestra_path (str): Ruta a los datos RDF de muestra (.ttl).
            persist_path (str): Ruta donde se guardarán/cargarán los datos actualizados.
        """
        self.graph = Graph()
        self.ontologia_path = ontologia_path
        self.datos_muestra_path = datos_muestra_path
        self.persist_path = persist_path

        # Definir namespaces
        self.ns_trade = Namespace("http://www.example.org/trading#")
        self.graph.bind("trade", self.ns_trade)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)

        # Acceso más fácil a los namespaces para los agentes
        self.ns_manager = NamespaceHelper(self.graph)

        self._cargar_ontologia()
        self._cargar_datos()
        
        print(f"RDFManagerTrading inicializado. Grafo con {len(self.graph)} tripletas.")

    def _cargar_ontologia(self):
        if self.ontologia_path and os.path.exists(self.ontologia_path):
            try:
                self.graph.parse(self.ontologia_path, format="turtle")
                print(f"Ontología cargada desde {self.ontologia_path}")
            except Exception as e:
                print(f"Error crítico al cargar la ontología desde {self.ontologia_path}: {e}")
        else:
            print(f"Advertencia: Archivo de ontología no encontrado en {self.ontologia_path}. El sistema puede no funcionar correctamente.")

    def _cargar_datos(self):
        # Priorizar datos persistidos
        if self.persist_path and os.path.exists(self.persist_path):
            try:
                self.graph.parse(self.persist_path, format="turtle")
                print(f"Datos cargados desde el archivo de persistencia: {self.persist_path}")
                return # Salir si se cargaron los datos persistidos
            except Exception as e:
                print(f"Error al cargar datos desde {self.persist_path}: {e}. Intentando cargar datos de muestra.")
        
        # Si no hay persistidos o falló la carga, cargar datos de muestra
        if self.datos_muestra_path and os.path.exists(self.datos_muestra_path):
            try:
                self.graph.parse(self.datos_muestra_path, format="turtle")
                print(f"Datos de muestra cargados desde {self.datos_muestra_path}")
            except Exception as e:
                print(f"Error crítico al cargar datos de muestra desde {self.datos_muestra_path}: {e}")
        else:
            print(f"Advertencia: No se encontraron datos persistidos en {self.persist_path} ni datos de muestra en {self.datos_muestra_path}.")

    def guardar_datos(self, ruta_archivo=None):
        """
        Guarda el estado actual del grafo RDF en un archivo Turtle.
        Si no se especifica ruta_archivo, usa self.persist_path.
        """
        path_to_save = ruta_archivo if ruta_archivo else self.persist_path
        if not path_to_save:
            print("Error: No se especificó una ruta para guardar los datos y no hay ruta de persistencia configurada.")
            return
            
        os.makedirs(os.path.dirname(path_to_save), exist_ok=True)

        try:
            self.graph.serialize(destination=path_to_save, format="turtle")
            print(f"Grafo RDF guardado en {path_to_save} con {len(self.graph)} tripletas.")
        except Exception as e:
            print(f"Error al guardar el grafo RDF en {path_to_save}: {e}")

    def ejecutar_sparql(self, consulta_str):
        """
        Ejecuta una consulta SPARQL sobre el grafo.
        """
        try:
            # print(f"DEBUG SPARQL:\n{consulta_str}\n") # Descomentar para depurar consultas
            resultados = self.graph.query(consulta_str)
            return resultados
        except Exception as e:
            print(f"Error crítico al ejecutar la consulta SPARQL: {e}\nConsulta:\n{consulta_str}")
            return None # Devolver None en caso de error para manejo posterior

    def agregar_tripleta(self, sujeto_uri, predicado_uri, objeto_uri_o_literal):
        """
        Añade una tripleta al grafo.
        """
        try:
            self.graph.add((sujeto_uri, predicado_uri, objeto_uri_o_literal))
        except Exception as e:
            print(f"Error al añadir tripleta ({sujeto_uri}, {predicado_uri}, {objeto_uri_o_literal}): {e}")

    def obtener_uri(self, nombre_entidad: str, ns_prefix: str = "trade") -> URIRef:
        """
        Crea una URI completa para una entidad usando el namespace 'trade' por defecto.
        """
        if ns_prefix == "trade":
            return self.ns_trade[nombre_entidad]
        # Podrías añadir más namespaces si fuera necesario
        return Namespace(f"http://www.example.org/{ns_prefix}#")[nombre_entidad]

    def actualizar_precio_par_mercado(self, par_mercado_uri: URIRef, nuevo_precio: float, timestamp: datetime = None):
        """
        Actualiza la propiedad :precioActual de un :ParMercado.
        Elimina el precio anterior antes de añadir el nuevo.
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Eliminar el precio actual anterior para este par de mercado
        self.graph.remove((par_mercado_uri, self.ns_trade.precioActual, None))
        
        # Añadir el nuevo precio actual
        self.agregar_tripleta(par_mercado_uri, self.ns_trade.precioActual, Literal(nuevo_precio, datatype=XSD.decimal))
        
        # Opcional: Podríamos añadir un historial de precios si fuera necesario,
        # creando instancias de :HistoricoPrecio, pero para :precioActual solo mantenemos el último.
        print(f"Precio actualizado para <{par_mercado_uri.split('#')[-1]}> a {nuevo_precio} en {timestamp.isoformat()}")


class NamespaceHelper:
    """Clase auxiliar para un acceso más limpio a los namespaces y URIs comunes."""
    def __init__(self, graph: Graph):
        self.trade = Namespace("http://www.example.org/trading#")
        self.rdf = RDF
        self.rdfs = RDFS
        self.owl = OWL
        self.xsd = XSD
        
        # Bind para serialización bonita (ya hecho en RDFManagerTrading, pero no hace daño repetirlo aquí para claridad)
        graph.bind("trade", self.trade)
        graph.bind("rdf", self.rdf)
        graph.bind("rdfs", self.rdfs)
        graph.bind("owl", self.owl)
        graph.bind("xsd", self.xsd)

    def get_uri(self, local_name: str) -> URIRef:
        """Devuelve una URI completa para el namespace 'trade'."""
        return self.trade[local_name]

# Bloque de prueba
if __name__ == '__main__':
    print("Probando RDFManagerTrading...")
    
    # Asegúrate de que las rutas sean correctas si ejecutas este script directamente.
    # Estas rutas asumen que el script se ejecuta desde la raíz del proyecto.
    # Si ejecutas `python rdf_utils/rdf_manager_trading.py`, ajusta las rutas:
    current_dir = os.path.dirname(__file__)
    base_dir = os.path.join(current_dir, '..') # Sube un nivel para estar en la raíz del proyecto
    
    ontologia_f = os.path.join(base_dir, 'datos_trading', 'ontologia_trading.ttl')
    datos_muestra_f = os.path.join(base_dir, 'datos_trading', 'datos_trading_muestra.ttl')
    persist_f = os.path.join(base_dir, 'datos_trading', 'test_rdf_manager_persist.ttl')

    if not os.path.exists(ontologia_f):
        print(f"ERROR: Archivo de ontología no encontrado en {ontologia_f}")
    if not os.path.exists(datos_muestra_f):
        print(f"ERROR: Archivo de datos de muestra no encontrado en {datos_muestra_f}")

    manager = RDFManagerTrading(
        ontologia_path=ontologia_f,
        datos_muestra_path=datos_muestra_f,
        persist_path=persist_f
    )
    
    print(f"\nTotal de tripletas después de la carga inicial: {len(manager.graph)}")

    print("\n--- Consultando la Estrategia Predeterminada ---")
    query_estrategia = f"""
        PREFIX trade: <{manager.ns_trade}>
        SELECT ?nombreEstrategia ?parMonitoreado ?riesgo
        WHERE {{
            trade:EstrategiaPredeterminada rdf:type trade:Estrategia ;
                                         trade:nombreEstrategia ?nombreEstrategia ;
                                         trade:monitoreaPar ?parUri ;
                                         trade:nivelRiesgoPreferido ?riesgo .
            ?parUri trade:tieneActivoBase/trade:simboloCripto ?simboloBase ;
                    trade:tieneActivoCotizacion/trade:simboloCripto ?simboloCot .
            BIND(CONCAT(?simboloBase, "/", ?simboloCot) AS ?parMonitoreado)
        }}
    """
    resultados_estrategia = manager.ejecutar_sparql(query_estrategia)
    if resultados_estrategia:
        for fila in resultados_estrategia:
            print(f"Estrategia: {fila['nombreEstrategia']}, Monitorea: {fila['parMonitoreado']}, Riesgo: {fila['riesgo']}")

    print("\n--- Actualizando precio de WLD_USDT ---")
    wld_usdt_uri = manager.ns_trade.WLD_USDT
    manager.actualizar_precio_par_mercado(wld_usdt_uri, 3.55) # Nuevo precio

    query_precio_wld = f"""
        PREFIX trade: <{manager.ns_trade}>
        SELECT ?precio
        WHERE {{
            trade:WLD_USDT trade:precioActual ?precio .
        }}
    """
    resultados_precio = manager.ejecutar_sparql(query_precio_wld)
    if resultados_precio:
        for fila in resultados_precio:
            print(f"Nuevo precio de WLD_USDT: {fila['precio']}")
            assert fila['precio'] == Literal(3.55, datatype=XSD.decimal), "La actualización del precio falló"

    print("\n--- Guardando datos ---")
    manager.guardar_datos() # Guarda en persist_f ('test_rdf_manager_persist.ttl')
    
    print("\n--- Cargando de nuevo para verificar persistencia ---")
    manager_recargado = RDFManagerTrading(
        ontologia_path=ontologia_f,
        datos_muestra_path=datos_muestra_f, # No debería usar este si persist_f existe
        persist_path=persist_f
    )
    print(f"Total de tripletas después de recargar: {len(manager_recargado.graph)}")
    
    resultados_precio_recargado = manager_recargado.ejecutar_sparql(query_precio_wld)
    if resultados_precio_recargado:
        for fila in resultados_precio_recargado:
            print(f"Precio de WLD_USDT después de recargar: {fila['precio']}")
            assert fila['precio'] == Literal(3.55, datatype=XSD.decimal), "La persistencia del precio falló"

    print("\nPrueba de RDFManagerTrading completada.")
