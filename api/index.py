import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Agregar la carpeta raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app
    logger.info("App importada exitosamente")
except Exception as e:
    logger.error(f"Error importando app: {e}", exc_info=True)
    raise

# Exportar para Vercel
handler = app
