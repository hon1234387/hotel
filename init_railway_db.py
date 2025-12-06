#!/usr/bin/env python
"""Script para inicializar la base de datos en Railway"""
import os
import sys
from app import create_app, db

# Usar la configuración de producción
app = create_app('production')

with app.app_context():
    print("Creando tablas...")
    db.create_all()
    print("✅ Base de datos inicializada correctamente")
