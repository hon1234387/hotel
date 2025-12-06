"""
Script para inicializar módulos y permisos por defecto en el sistema
"""
from app import create_app
from models import db, Module, Permission, RolePermission

app = create_app()

def seed_modules():
    """Crear módulos por defecto"""
    with app.app_context():
        # Verificar si ya existen los módulos
        if Module.query.first():
            print("✓ Los módulos ya están inicializados")
            return
        
        modules_data = [
            {
                'name': 'Huéspedes',
                'description': 'Gestión de huéspedes y registros',
                'icon': 'fas fa-users'
            },
            {
                'name': 'Habitaciones',
                'description': 'Gestión de habitaciones y estado',
                'icon': 'fas fa-door-open'
            },
            {
                'name': 'Reservas',
                'description': 'Gestión de reservas y check-in/check-out',
                'icon': 'fas fa-calendar-alt'
            },
            {
                'name': 'Pagos',
                'description': 'Gestión de pagos y facturas',
                'icon': 'fas fa-credit-card'
            },
            {
                'name': 'Servicios',
                'description': 'Servicios adicionales ofrecidos',
                'icon': 'fas fa-concierge-bell'
            },
            {
                'name': 'Mantenimiento',
                'description': 'Reporte y control de mantenimiento',
                'icon': 'fas fa-wrench'
            },
            {
                'name': 'Limpieza',
                'description': 'Asignación y seguimiento de limpieza',
                'icon': 'fas fa-broom'
            },
            {
                'name': 'Reportes',
                'description': 'Generación de reportes y análisis',
                'icon': 'fas fa-chart-bar'
            },
            {
                'name': 'Configuración',
                'description': 'Configuración del sistema',
                'icon': 'fas fa-cog'
            }
        ]
        
        modules = {}
        for data in modules_data:
            module = Module(
                name=data['name'],
                description=data['description'],
                icon=data['icon'],
                is_enabled=True
            )
            db.session.add(module)
            modules[data['name']] = module
        
        db.session.commit()
        print(f"✓ Se crearon {len(modules)} módulos")
        
        # Crear permisos por defecto para cada módulo
        permissions_data = [
            {'action': 'view', 'description': 'Ver'},
            {'action': 'create', 'description': 'Crear'},
            {'action': 'edit', 'description': 'Editar'},
            {'action': 'delete', 'description': 'Eliminar'},
            {'action': 'export', 'description': 'Exportar'},
        ]
        
        permission_count = 0
        for module in modules.values():
            for perm in permissions_data:
                permission = Permission(
                    name=f'{module.name.lower()}_{perm["action"]}',
                    description=f'{perm["description"]} {module.name.lower()}',
                    module_id=module.id
                )
                db.session.add(permission)
                permission_count += 1
        
        db.session.commit()
        print(f"✓ Se crearon {permission_count} permisos")
        
        # Asignar permisos a admin
        # Aquí podrías agregar lógica para asignar todos los permisos al rol admin
        print("\n✓ Sistema de módulos inicializado exitosamente")

if __name__ == '__main__':
    seed_modules()
