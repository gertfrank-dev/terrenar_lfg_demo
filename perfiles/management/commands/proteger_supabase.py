"""
Activa Row Level Security (RLS) en todas las tablas del esquema public.

Por qué: Supabase publica automáticamente las tablas de "public" como una API REST.
Sin RLS, cualquiera con la clave pública del proyecto podría leer los perfiles
directamente, saltándose la privacidad que controla Django.

Con RLS activado y sin reglas (policies), esa API no devuelve nada.
Django se conecta como dueño de las tablas, así que a él no le afecta.
En SQLite (desarrollo) no hace nada.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Activa RLS en todas las tablas de public (solo PostgreSQL)."

    def handle(self, *args, **opts):
        if connection.vendor != "postgresql":
            self.stdout.write("No es PostgreSQL: nada que proteger.")
            return
        with connection.cursor() as c:
            c.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND NOT rowsecurity"
            )
            tablas = [t for (t,) in c.fetchall()]
            for t in tablas:
                c.execute(f'ALTER TABLE public."{t}" ENABLE ROW LEVEL SECURITY')
        self.stdout.write(f"RLS activado en {len(tablas)} tablas.")
