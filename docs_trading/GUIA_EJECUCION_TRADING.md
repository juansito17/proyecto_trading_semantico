# Guía de Ejecución: Asistente de Trading Semántico

## 1. Prerrequisitos

* Python 3.8 o superior.
* `pip` (gestor de paquetes de Python).

## 2. Configuración del Entorno

1.  **Obtener el Proyecto:** Coloca todos los archivos del proyecto en una carpeta (ej. `proyecto_trading_semantico/`) manteniendo la estructura de directorios especificada.
2.  **Crear Entorno Virtual:**
    En la terminal, dentro del directorio raíz del proyecto:
    ```bash
    python -m venv venv_trading
    ```
3.  **Activar Entorno Virtual:**
    * Windows: `venv_trading\Scripts\activate`
    * macOS/Linux: `source venv_trading/bin/activate`
4.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements_trading.txt
    ```

## 3. Archivos de Datos y Ontología

* Asegúrate que `datos_trading/ontologia_trading.ttl` y `datos_trading/datos_trading_muestra.ttl` estén presentes.
* `datos_trading_muestra.ttl` debe definir `:WLD_USDT`, `:EstrategiaPredeterminada` y las `:IndicadorTecnicoConfig` asociadas.
* Al iniciar, la app carga `datos_trading_muestra.ttl` si `datos_trading/datos_actualizados.ttl` no existe.

## 4. Ejecutar la Aplicación Web

1.  Con el entorno virtual activo, desde el directorio raíz del proyecto:
    ```bash
    python run_trading.py
    ```
2.  El servidor Flask iniciará en `http://127.0.0.1:5000/`.

## 5. Uso del Sistema

1.  **Acceder al Dashboard:** Abre `http://127.0.0.1:5000/` en tu navegador. Verás el dashboard para WLD/USDT.
2.  **Visualización Inicial:** Mostrará datos de `datos_trading_muestra.ttl` o del último estado guardado. La recomendación estará vacía si se eliminó de los datos de muestra.
3.  **Ejecutar Ciclo de Análisis:** Haz clic en "Ejecutar Ciclo de Análisis WLD". El `AgenteSenalesTrading` procesará los datos para WLD/USDT y actualizará el grafo RDF.
4.  **Ver Resultados:** El dashboard se recargará, mostrando los nuevos indicadores y la recomendación generada.
5.  **Persistencia:** Los cambios se guardan en `datos_trading/datos_actualizados.ttl`. Para reiniciar con datos de muestra, elimina este archivo antes de correr `run_trading.py`.

Esta guía permite ejecutar y probar el sistema enfocado en WLD/USDT.
