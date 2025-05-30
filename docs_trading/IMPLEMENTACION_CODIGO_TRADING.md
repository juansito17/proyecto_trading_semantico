# Documentación de Implementación del Código: Asistente de Trading Semántico

## 1. Introducción
Este documento detalla la implementación de los componentes del Asistente Semántico de Decisiones de Trading. El sistema utiliza Python, rdflib para la gestión de datos RDF, y Flask para la interfaz web. Se enfoca en cómo los agentes interactúan con el grafo RDF para generar recomendaciones de trading para WLD/USDT.

## 2. Estructura del Código
- **agentes/**
  - agente_perfil_estrategia.py: AgentePerfilEstrategia
  - agente_senales_trading.py: AgenteSenalesTrading
- **rdf_utils/**
  - rdf_manager_trading.py: Clase RDFManagerTrading
- **interfaz_web_trading/**: Aplicación Flask (app_trading.py y plantillas)
- **datos_trading/**: Ontología (ontologia_trading.ttl) y datos de muestra
- **utils/**: Cálculo de indicadores (indicadores_tecnicos.py)
- **run_trading.py**: Script de inicio

## 3. Módulo RDF (rdf_utils/rdf_manager_trading.py)
RDFManagerTrading gestiona el grafo RDF:
- Carga ontologia_trading.ttl y datos (muestra o persistidos)
- Define prefijos (trade:, rdf:, xsd:)
- Provee métodos: guardar_datos(), ejecutar_sparql(consulta_str), agregar_tripleta(...), actualizar_precio_par_mercado(...)

## 4. Agentes Inteligentes (agentes/)

### 4.1. AgentePerfilEstrategia (agente_perfil_estrategia.py)
**Responsabilidad**: Gestionar la trade:Estrategia activa.

**Lógica**:
- definir_o_actualizar_estrategia(...): Crea/modifica una trade:Estrategia en RDF (par, indicadores, riesgo)
- obtener_estrategia_activa(...): Consulta SPARQL para recuperar la estrategia (ej. trade:EstrategiaPredeterminada)

### 4.2. AgenteSenalesTrading (agente_senales_trading.py)
**Responsabilidad**: Analizar el mercado (WLD/USDT) y generar recomendaciones.

**Ciclo de Operación** (ejecutar_ciclo_analisis):
1. Obtener Estrategia: Usa AgentePerfilEstrategia para obtener la trade:EstrategiaPredeterminada
2. Recolectar Datos: Usa utils.indicadores_tecnicos.obtener_datos_historicos_simulados() para WLD/USDT. Actualiza trade:precioActual en RDF
3. Calcular Indicadores: Para cada trade:IndicadorTecnicoConfig de la estrategia:
   - Consulta sus parámetros (ej. período) vía SPARQL
   - Calcula el indicador (SMA, RSI, MACD, BB)
   - Crea trade:ValorIndicador en RDF
4. Interpretar Señales (_interpretar_y_almacenar_senales):
   - Revisa los trade:ValorIndicador
   - Genera trade:SenalTecnica (ej. :PRECIO_SOBRE_SMA20) y las almacena en RDF
5. Generar Recomendación (_generar_y_almacenar_recomendacion):
   - Recupera tipos de trade:SenalTecnica activas
   - Aplica lógica simple (Python) para decidir (COMPRAR, VENDER, MANTENER)
   - Crea trade:RecomendacionTrading en RDF, enlazándola a señales y estrategia
6. Persistencia: Guarda cambios en el grafo

## 5. Módulo de Utilidades (utils/indicadores_tecnicos.py)
- Funciones Python para calcular SMA, RSI, MACD, Bandas de Bollinger
- obtener_datos_historicos_simulados() para datos de prueba

## 6. Interfaz Web (interfaz_web_trading/app_trading.py)
**Rutas**:
- / (redirige a /dashboard/WLD_USDT)
- /dashboard/WLD_USDT: Muestra estado de WLD/USDT (precio, indicadores, última recomendación) consultando el grafo RDF
- /ejecutar_ciclo (POST): Dispara agente_senales.ejecutar_ciclo_analisis() para la EstrategiaPredeterminada (WLD/USDT)

**Plantillas HTML**: base_trading.html, dashboard_trading.html, error_page_trading.html

## 7. Flujo de Datos General
1. Inicio: Flask carga ontología y datos
2. Dashboard: Muestra datos RDF actuales de WLD/USDT
3. Ciclo de Análisis: Usuario lo activa. AgenteSenalesTrading actualiza el grafo RDF con nuevos valores de indicadores, señales y una recomendación para WLD/USDT
4. Actualización: Dashboard refleja los cambios del grafo

Este flujo muestra cómo los agentes modifican la base de conocimiento semántica, y la interfaz la consume.