# run_trading.py
import os
import sys

# --- Modificación para permitir la ejecución desde la raíz del proyecto ---
# Esto es importante si app_trading.py está en un subdirectorio como interfaz_web_trading
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# Si run_trading.py está en la raíz y app_trading.py en interfaz_web_trading,
# no necesitamos modificar sys.path aquí para el import de app,
# pero es bueno tenerlo si la estructura cambia o si hay otros módulos raíz.
# Lo que sí es importante es que Flask pueda encontrar las plantillas y estáticos.
# if current_script_dir not in sys.path:
# sys.path.insert(0, current_script_dir)
# --- Fin de la modificación ---

from interfaz_web_trading.app_trading import app # Importa la instancia de la app Flask

if __name__ == '__main__':
    # Asegurarse que el directorio de datos exista para persistencia
    # Esto es importante si RDFManager intenta guardar datos al iniciar o durante la ejecución.
    project_root_dir_for_run = os.path.abspath(os.path.dirname(__file__)) # Raíz del proyecto
    datos_dir = os.path.join(project_root_dir_for_run, 'datos_trading')
    if not os.path.exists(datos_dir):
        try:
            os.makedirs(datos_dir)
            print(f"Directorio '{datos_dir}' creado por run_trading.py.")
        except OSError as e:
            print(f"Error al crear el directorio '{datos_dir}': {e}")

    # Configuración del host y puerto
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000)) # Puerto por defecto 5000
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']

    print(f"Iniciando Asistente de Trading Semántico en http://{host}:{port}/")
    print(f"Modo Debug: {debug_mode}")
    
    # Pasar use_reloader=False si estás teniendo problemas con múltiples inicializaciones de agentes
    # o si el debugger de Flask causa problemas con hilos/procesos de los agentes (si los tuvieras).
    # Para este proyecto simple, el reloader debería estar bien.
    app.run(host=host, port=port, debug=debug_mode)
