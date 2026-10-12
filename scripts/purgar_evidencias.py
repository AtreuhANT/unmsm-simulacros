"""Elimina fotografías expiradas; ejecutar a diario con --execute."""

import argparse
from uuid import UUID

from models.database import get_db_cursor
from models.evidencia_celular import DIRECTORIO


def purgar(ejecutar=False):
    with get_db_cursor(commit=ejecutar) as cur:
        cur.execute("SELECT id, archivo FROM evidencias_celular "
                    "WHERE expira_en <= CURRENT_TIMESTAMP ORDER BY id LIMIT 100 FOR UPDATE SKIP LOCKED")
        filas = cur.fetchall()
        if not ejecutar:
            return len(filas)
        for fila in filas:
            archivo = fila['archivo']
            if len(archivo) != 36 or not archivo.endswith('.bin'):
                raise ValueError('Nombre de evidencia inesperado; se detiene la purga')
            UUID(archivo[:-4])
            (DIRECTORIO / archivo).unlink(missing_ok=True)
            cur.execute('DELETE FROM evidencias_celular WHERE id = %s', (fila['id'],))
        return len(filas)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Eliminar hasta 100 evidencias expiradas')
    args = parser.parse_args()
    total = purgar(args.execute)
    print(f'{total} evidencias expiradas ' + ('eliminadas' if args.execute else 'pendientes de purga'))
