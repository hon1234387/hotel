#!/usr/bin/env python3
"""
Script para configurar el número de WhatsApp del hotel

Uso: python configure_whatsapp.py
     o: python configure_whatsapp.py 573001234567
"""

import os
import sys
import re

def clean_phone(phone):
    """Limpia el número de teléfono removiendo caracteres especiales"""
    # Remover todo excepto dígitos
    cleaned = re.sub(r'\D', '', phone)
    return cleaned

def update_file(filepath, old_pattern, new_pattern):
    """Actualiza un archivo con el nuevo patrón"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Contar cuántas veces aparece el patrón
        count = content.count(old_pattern)
        
        if count == 0:
            print(f"  ⚠️  No se encontró el patrón en {filepath}")
            return False
        
        # Reemplazar
        new_content = content.replace(old_pattern, new_pattern)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ Actualizado: {filepath} ({count} cambios)")
        return True
    
    except Exception as e:
        print(f"  ❌ Error en {filepath}: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  CONFIGURADOR DE WHATSAPP PARA RESERVAS")
    print("="*60 + "\n")
    
    # Obtener número de teléfono
    if len(sys.argv) > 1:
        phone = sys.argv[1]
    else:
        phone = input("📱 Ingresa tu número de WhatsApp (con código de país):\n   Ej: 573001234567, +57 300 123 4567, etc.\n   > ").strip()
    
    # Validar y limpiar
    phone = clean_phone(phone)
    
    if not phone or len(phone) < 10:
        print("\n❌ Número inválido. Debe tener al menos 10 dígitos.")
        sys.exit(1)
    
    print(f"\n✅ Número procesado: +{phone}")
    
    # Confirmación
    confirm = input(f"\n¿Confirmas usar el número +{phone}? (s/n): ").strip().lower()
    if confirm != 's':
        print("\n❌ Operación cancelada.")
        sys.exit(1)
    
    print("\n🔄 Actualizando archivos...\n")
    
    # Archivos y patrones a actualizar
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    updates = [
        # En booking_link.html - Chat directo (dos lugares)
        (
            os.path.join(base_dir, 'templates/whatsapp/booking_link.html'),
            'https://wa.me/573001234567?text=Hola',
            f'https://wa.me/{phone}?text=Hola'
        ),
        (
            os.path.join(base_dir, 'templates/whatsapp/booking_link.html'),
            'https://wa.me/573001234567',
            f'https://wa.me/{phone}'
        ),
    ]
    
    # Aplicar actualizaciones
    success_count = 0
    for filepath, old_pattern, new_pattern in updates:
        if os.path.exists(filepath):
            if update_file(filepath, old_pattern, new_pattern):
                success_count += 1
        else:
            print(f"  ⚠️  Archivo no encontrado: {filepath}")
    
    # Mensaje final
    print("\n" + "="*60)
    if success_count == len([u for u in updates if os.path.exists(u[0])]):
        print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print(f"\n📱 Número de WhatsApp: +{phone}")
        print("\n🚀 Ahora puedes:")
        print("   1. Iniciar el servidor: python app.py")
        print("   2. Ir a http://localhost:5000/whatsapp/booking-link")
        print("   3. Probar el formulario de reservas")
    else:
        print("⚠️  CONFIGURACIÓN PARCIAL")
        print("   Algunos archivos no se pudieron actualizar.")
    
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
