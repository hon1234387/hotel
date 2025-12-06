import sys
import os

# Agregar la carpeta raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Exportar para Vercel
handler = app
