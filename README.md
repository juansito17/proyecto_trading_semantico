# Proyecto Final: Asistente Semántico de Decisiones de Trading para Criptomonedas

**Asignatura:** Web Semántica y Agentes Inteligentes (ING01243)
**Estudiante:** Juan Manuel Peña Usuga
**Profesor:** Juan Pablo Hoyos Salazar
**Fecha de Entrega:** (Especificar Fecha)

## 1. Introducción

Estimado profesor Juan Pablo,

Este proyecto, titulado "Asistente Semántico de Decisiones de Trading para Criptomonedas", ha sido desarrollado como respuesta a los requisitos del parcial final de la asignatura Web Semántica y Agentes Inteligentes. El objetivo principal es demostrar la comprensión y aplicación de los conceptos de agentes inteligentes y tecnologías del Web Semántico en un sistema funcional.

Aunque el enunciado del parcial se centra en un sistema de recomendación de contenido tradicional, he adaptado estos principios al dominio del trading de criptomonedas. En este contexto:
* El **"contenido"** a analizar es el estado del mercado de una criptomoneda (ej. WLD/USDT), representado por sus datos de precios, volúmenes e indicadores técnicos.
* Las **"preferencias del usuario"** se traducen en una **estrategia de trading** configurable, que define qué activo monitorear, qué indicadores son relevantes y el perfil de riesgo.
* Las **"recomendaciones personalizadas"** son las **sugerencias de acciones de trading** (COMPRAR, VENDER, MANTENER) generadas por el sistema, basadas en el análisis semántico de los datos del mercado y la estrategia definida.

A continuación, se detalla cómo el proyecto cumple con los objetivos y componentes solicitados.

## 2. Cumplimiento de los Objetivos del Parcial

### 2.1. Entender e Implementar Agentes Inteligentes
Se han implementado dos agentes principales que interactúan de forma autónoma (dentro de su ciclo de ejecución) para lograr los objetivos del sistema:

* **`AgentePerfilEstrategia`** (`agentes/agente_perfil_estrategia.py`):
    * Este agente cumple la función del "Agente de Perfil de Usuario" solicitado. En lugar de un perfil de usuario convencional, gestiona la **estrategia de trading** (`trade:Estrategia` en la ontología).
    * Define qué par de mercado se monitorea (ej. `:WLD_USDT`), qué configuraciones de indicadores técnicos (`trade:IndicadorTecnicoConfig`) son relevantes (ej. `:ConfigSMA20`, `:ConfigRSI14`), y otros parámetros como el nivel de riesgo.
    * La estrategia se almacena y se consulta desde el grafo RDF, permitiendo que las "preferencias" del sistema sean explícitas y semánticamente definidas.

* **`AgenteSenalesTrading`** (`agentes/agente_senales_trading.py`):
    * Este agente actúa como el "Agente de Recomendación".
    * Utiliza la estrategia activa (obtenida a través del `AgentePerfilEstrategia`) para guiar su análisis.
    * Procesa datos de mercado (simulados en esta versión), calcula indicadores técnicos (`trade:ValorIndicador`), interpreta señales básicas (`trade:SenalTecnica`), y almacena toda esta información como instancias en el grafo RDF.
    * Finalmente, genera una `trade:RecomendacionTrading` (COMPRAR, VENDER, MANTENER) para el par de mercado, basándose en la lógica implementada que considera las señales almacenadas en el grafo.

### 2.2. Aplicar Tecnologías del Web Semántico

* **Modelo de Datos RDF (`rdflib` y archivos `.ttl`):**
    * Toda la información relevante del dominio – estrategias, criptomonedas, pares de mercado, configuraciones de indicadores, valores calculados de indicadores, señales técnicas interpretadas y las recomendaciones de trading finales – se representa utilizando el modelo RDF.
    * La gestión del grafo (carga, consulta, adición de tripletas, persistencia) se centraliza en la clase `RDFManagerTrading` (`rdf_utils/rdf_manager_trading.py`).
    * Los datos iniciales y la ontología se cargan desde archivos Turtle (`datos_trading/ontologia_trading.ttl` y `datos_trading/datos_trading_muestra.ttl`), y el estado actualizado del grafo se persiste en `datos_trading/datos_actualizados.ttl`.

* **Ontologías OWL (`datos_trading/ontologia_trading.ttl`):**
    * Se ha diseñado y definido una ontología específica para este dominio (`ontologia_trading.ttl`).
    * Esta ontología formaliza las clases principales (ej. `trade:Estrategia`, `trade:ParMercado`, `trade:IndicadorTecnicoConfig`, `trade:ValorIndicador`, `trade:SenalTecnica`, `trade:RecomendacionTrading`) y las propiedades (tanto de datos como de objeto) que describen sus atributos y relaciones.
    * El diseño detallado se encuentra en `docs_trading/DISEÑO_ONTOLOGIA_TRADING.md`.

* **Consultas SPARQL:**
    * SPARQL es fundamental para la interacción de los agentes con el grafo RDF.
    * El `AgentePerfilEstrategia` utiliza SPARQL en su método `obtener_estrategia_activa` para recuperar la configuración de la estrategia.
    * El `AgenteSenalesTrading` utiliza SPARQL para obtener los parámetros de las configuraciones de indicadores antes de calcularlos.
    * La aplicación Flask (`interfaz_web_trading/app_trading.py`) usa SPARQL extensivamente para consultar el precio actual, los últimos valores de indicadores y la recomendación más reciente para mostrar en el dashboard.
    * Aunque la lógica de decisión final en `AgenteSenalesTrading` para combinar señales es actualmente Python simple, se basa en la recuperación de los tipos de señales (instancias de `trade:SenalTecnica`) que fueron previamente almacenadas en el grafo. Se discute en la documentación cómo esta lógica podría evolucionar para usar consultas SPARQL más complejas para un razonamiento más avanzado sobre patrones de señales.

### 2.3. Integrar Ambas Tecnologías
La integración es el núcleo del proyecto:
* El `AgentePerfilEstrategia` define las "reglas del juego" (la estrategia) en el grafo RDF.
* El `AgenteSenalesTrading` opera basándose en esta estrategia semántica:
    1.  Lee la estrategia del grafo (SPARQL).
    2.  Obtiene datos de mercado y calcula indicadores.
    3.  **Escribe** los resultados de estos cálculos (nuevas instancias de `trade:ValorIndicador`) de nuevo en el grafo RDF.
    4.  Interpreta estos valores y **escribe** `trade:SenalTecnica` en el grafo.
    5.  Finalmente, (conceptualmente) **consulta** estas señales y otros datos del grafo para tomar una decisión, que también se **escribe** como una `trade:RecomendacionTrading`.
* La aplicación Flask actúa como una ventana a este grafo RDF, mostrando la información actualizada por los agentes.

## 3. Descripción de la Implementación y Flujo del Sistema

1.  **Inicio:** La aplicación Flask (`run_trading.py` -> `interfaz_web_trading/app_trading.py`) inicializa el `RDFManagerTrading` (cargando ontología y datos) y los agentes.
2.  **Visualización:** El usuario accede al dashboard web. La aplicación Flask consulta el grafo RDF para mostrar:
    * El precio actual del par `WLD/USDT` (obtenido de `trade:ParMercado`).
    * Los últimos `trade:ValorIndicador` almacenados para ese par.
    * La `trade:RecomendacionTrading` más reciente para ese par.
3.  **Ejecución del Ciclo de Análisis (Disparado por el Usuario):**
    * Al hacer clic en "Ejecutar Ciclo de Análisis", se llama a `agente_senales.ejecutar_ciclo_analisis()`.
    * **El `AgenteSenalesTrading`:**
        * Consulta la `trade:EstrategiaPredeterminada` usando `AgentePerfilEstrategia`.
        * Obtiene datos de mercado simulados (de `utils/indicadores_tecnicos.py`).
        * Actualiza el `trade:precioActual` del par en el grafo.
        * Para cada `trade:IndicadorTecnicoConfig` en la estrategia:
            * Consulta los parámetros de la configuración del indicador (ej. período) desde el grafo.
            * Calcula el indicador usando funciones en `utils/indicadores_tecnicos.py`.
            * Crea una nueva instancia de `trade:ValorIndicador` en el grafo con el resultado.
        * Llama a `_interpretar_y_almacenar_senales()`:
            * Revisa los `trade:ValorIndicador` recién calculados.
            * Genera instancias de `trade:SenalTecnica` (ej. `:PRECIO_SOBRE_SMA20`) si se cumplen condiciones simples y las almacena en el grafo.
        * Llama a `_generar_y_almacenar_recomendacion()`:
            * Recupera los tipos de `trade:SenalTecnica` activas.
            * Aplica una lógica de decisión simple (actualmente en Python) para determinar una acción (COMPRAR, VENDER, MANTENER).
            * Crea una instancia de `trade:RecomendacionTrading` en el grafo.
        * Guarda todos los cambios en el grafo (`datos_actualizados.ttl`).
4.  **Actualización del Dashboard:** El usuario ve la información actualizada (nuevos indicadores, nueva recomendación) en la siguiente carga de la página.

## 4. Estructura del Proyecto

```
proyecto_trading_semantico/
├── agentes/
│   ├── __init__.py
│   ├── agente_perfil_estrategia.py
│   └── agente_senales_trading.py
├── datos_trading/
│   ├── ontologia_trading.ttl
│   └── datos_trading_muestra.ttl
├── interfaz_web_trading/
│   ├── __init__.py
│   ├── app_trading.py
│   └── templates/
│       ├── base_trading.html
│       ├── dashboard_trading.html
│       └── error_page_trading.html
├── rdf_utils/
│   ├── __init__.py
│   └── rdf_manager_trading.py
├── static_trading/
│   └── style_trading.css
├── utils/
│   ├── __init__.py
│   └── indicadores_tecnicos.py
├── docs_trading/
│   ├── README_trading.md
│   ├── DISEÑO_ONTOLOGIA_TRADING.md
│   ├── IMPLEMENTACION_CODIGO_TRADING.md
│   └── GUIA_EJECUCION_TRADING.md
├── requirements_trading.txt
└── run_trading.py
```

## 5. Tecnologías Utilizadas

* **Lenguaje de Programación:** Python 3.x
* **Agentes Inteligentes:** Implementación personalizada.
* **Web Semántico:** `rdflib` para RDF, OWL para la ontología, SPARQL para consultas.
* **Desarrollo Web:** Flask.
* **Análisis Técnico:** Funciones personalizadas en `utils/indicadores_tecnicos.py` utilizando `pandas` y `numpy`.

## 6. Guía de Ejecución Resumida

1.  Configurar un entorno virtual Python.
2.  Instalar dependencias: `pip install -r requirements_trading.txt`.
3.  Asegurar que los archivos de ontología y datos de muestra estén en `datos_trading/`.
4.  Ejecutar la aplicación: `python run_trading.py`.
5.  Acceder a `http://127.0.0.1:5000/` en un navegador.
    (Para más detalles, ver `docs_trading/GUIA_EJECUCION_TRADING.md`).

## 7. Conclusión

Considero que este proyecto cumple con los requisitos del parcial al implementar un sistema donde los agentes inteligentes operan sobre una base de conocimiento semánticamente estructurada. La adaptación del concepto de "recomendación de contenido" al dominio del trading demuestra flexibilidad en la aplicación de los principios del Web Semántico y los agentes. El sistema es funcional, permite la visualización de la información generada por los agentes y establece una base sólida para futuras expansiones, como lógicas de decisión más complejas basadas en SPARQL o la integración con fuentes de datos de mercado en tiempo real.

Agradezco la oportunidad de desarrollar este proyecto y aplicar los conocimientos adquiridos en la asignatura.

Atentamente,

Juan Manuel Peña Usuga
