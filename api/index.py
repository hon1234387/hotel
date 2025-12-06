import sys
import os
from pathlib import Path

# Agregar la carpeta raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Establecer variables de entorno
os.environ.setdefault('FLASK_ENV', os.environ.get('FLASK_ENV', 'production'))

from app import app

# Para Vercel, necesitamos exportar la aplicación Flask directamente
# Vercel llama a la función WSGI (que Flask proporciona automáticamente)

