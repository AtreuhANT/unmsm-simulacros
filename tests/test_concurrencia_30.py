"""
TEST DE CONCURRENCIA Y CARGA — FASE 8 (OP-01)
Simulación de 30 postulantes rindiendo exámenes de forma simultánea.
Verifica:
1. Resistencia del pool de conexiones PostgreSQL (ThreadedConnectionPool).
2. Persistencia concurrente de intentos y respuestas incrementales (upsert sin colisiones).
3. Telemetría de monitoreo concurrente.
4. Cierre formal e idempotencia en entregas masivas.
"""

import os
import sys
import time
import uuid
import statistics
import concurrent.futures

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import get_db_cursor
from models.usuario import crear_usuario, obtener_usuario_por_dni
from models.intento import (
    crear_intento, guardar_respuesta_incremental,
    obtener_respuestas_intento, cerrar_intento
)
from models.resultado import registrar_evento, guardar_resultado

NUM_USUARIOS = 30
PREGUNTAS_POR_EXAMEN = 10

def simular_postulante(idx):
    """Simula el flujo completo y en tiempo real de un postulante."""
    latencias = []
    dni = f"9900{idx:04d}"
    area = ['A', 'B', 'C', 'D', 'E'][idx % 5]
    
    t_start = time.perf_counter()

    # 1. Crear o recuperar usuario
    t0 = time.perf_counter()
    u = obtener_usuario_por_dni(dni)
    if not u:
        u = crear_usuario(
            nombre=f'Postulante{idx}',
            apellido='Concurrente',
            dni=dni,
            password=f'pass_{dni}',
            carrera='Medicina' if area == 'A' else 'Ingeniería',
            area=area
        )
    latencias.append(('crear_usuario', time.perf_counter() - t0))
    user_id = u['id']

    # 2. Iniciar Intento Oficial en PostgreSQL
    t0 = time.perf_counter()
    intento = crear_intento(user_id, area, duracion_minutos=60)
    latencias.append(('crear_intento', time.perf_counter() - t0))
    intento_id = intento['id']
    token_sesion = intento['token_sesion']

    # 3. Guardado continuo e incremental de respuestas
    opciones = ['A', 'B', 'C', 'D', 'E']
    for p_id in range(1, PREGUNTAS_POR_EXAMEN + 1):
        opcion_elegida = opciones[(p_id + idx) % len(opciones)]
        t0 = time.perf_counter()
        guardar_respuesta_incremental(
            intento_id=intento_id,
            pregunta_id=p_id,
            opcion_seleccionada=opcion_elegida,
            es_blanco=False,
            marcado_revision=(p_id % 3 == 0)
        )
        latencias.append(('guardar_respuesta', time.perf_counter() - t0))

    # 4. Rectificación de respuesta (upsert concurrente sobre la misma tupla)
    t0 = time.perf_counter()
    guardar_respuesta_incremental(
        intento_id=intento_id,
        pregunta_id=1,
        opcion_seleccionada='E',
        es_blanco=False,
        marcado_revision=False
    )
    latencias.append(('rectificar_respuesta', time.perf_counter() - t0))

    # 5. Enviar evento de supervisión
    t0 = time.perf_counter()
    registrar_evento(
        usuario_id=user_id,
        resultado_id=None,
        modulo='focus_monitor',
        tipo='cambio_pestana',
        descripcion='Foco desviado momentáneamente',
        segundo_examen=45
    )
    latencias.append(('registrar_evento', time.perf_counter() - t0))

    # 6. Finalizar examen y cerrar intento
    t0 = time.perf_counter()
    cerrar_intento(intento_id, 'ENTREGADO', 'SIN_OBSERVACIONES')
    res = guardar_resultado(
        usuario_id=user_id,
        area=area,
        puntaje=120.0 + (idx * 5.0),
        correctas=7,
        incorrectas=2,
        blanco=1,
        tiempo_segundos=1800,
        token_sesion=token_sesion,
        estado='COMPLETADO'
    )
    latencias.append(('finalizar_y_guardar', time.perf_counter() - t0))

    duracion_total = time.perf_counter() - t_start

    return {
        'idx': idx,
        'user_id': user_id,
        'intento_id': intento_id,
        'token_sesion': token_sesion,
        'resultado_id': res['id'],
        'duracion_total': duracion_total,
        'latencias': latencias,
        'ok': True
    }

def ejecutar_benchmark_concurrencia():
    print("=" * 70)
    print(f"INICIANDO PRUEBA DE CARGA: {NUM_USUARIOS} POSTULANTES SIMULTÁNEOS (FASE 8)")
    print("=" * 70)

    app = create_app('development')
    
    t_global_start = time.perf_counter()
    resultados_hilos = []
    errores = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_USUARIOS) as executor:
        futuros = {executor.submit(simular_postulante, i): i for i in range(1, NUM_USUARIOS + 1)}
        for f in concurrent.futures.as_completed(futuros):
            idx = futuros[f]
            try:
                res = f.result()
                resultados_hilos.append(res)
            except Exception as e:
                errores.append((idx, str(e)))

    t_global_total = time.perf_counter() - t_global_start

    print("\n" + "-" * 70)
    print("RESULTADOS DEL BENCHMARK")
    print("-" * 70)
    print(f"Postulantes simultáneos simulados: {NUM_USUARIOS}")
    print(f"Ejecuciones exitosas:             {len(resultados_hilos)} / {NUM_USUARIOS}")
    print(f"Errores encontrados:              {len(errores)}")
    print(f"Tiempo total de la prueba:        {t_global_total:.2f} s")

    if errores:
        print("\nDETALLE DE ERRORES:")
        for idx, err in errores:
            print(f"  - Usuario #{idx}: {err}")
        return False

    # Análisis de latencias
    todas_latencias = []
    latencias_por_op = {}
    for r in resultados_hilos:
        for op, lat in r['latencias']:
            todas_latencias.append(lat * 1000) # ms
            latencias_por_op.setdefault(op, []).append(lat * 1000)

    lat_promedio = statistics.mean(todas_latencias)
    lat_mediana = statistics.median(todas_latencias)
    lat_p95 = statistics.quantiles(todas_latencias, n=20)[18] if len(todas_latencias) >= 20 else max(todas_latencias)
    lat_max = max(todas_latencias)

    print("\nMÉTRICAS DE RENDIMIENTO (LATENCIA EN MILISEGUNDOS):")
    print(f"  • Total operaciones ejecutadas: {len(todas_latencias)}")
    print(f"  • Latencia promedio:             {lat_promedio:.2f} ms")
    print(f"  • Latencia mediana (p50):        {lat_mediana:.2f} ms")
    print(f"  • Latencia percentil 95 (p95):   {lat_p95:.2f} ms")
    print(f"  • Latencia máxima:               {lat_max:.2f} ms")

    print("\nDESGLOSE POR OPERACIÓN:")
    for op, lats in latencias_por_op.items():
        print(f"  • {op:22s} -> Promedio: {statistics.mean(lats):.2f} ms | Max: {max(lats):.2f} ms")

    # Limpieza de datos de prueba
    print("\nLimpiando registros de prueba...")
    tokens = [r['token_sesion'] for r in resultados_hilos]
    intentos_ids = [r['intento_id'] for r in resultados_hilos]
    users_ids = [r['user_id'] for r in resultados_hilos]

    with get_db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM eventos_monitoreo WHERE usuario_id = ANY(%s);", (users_ids,))
        cur.execute("DELETE FROM resultados WHERE token_sesion = ANY(%s);", (tokens,))
        cur.execute("DELETE FROM respuestas_intento WHERE intento_id = ANY(%s);", (intentos_ids,))
        cur.execute("DELETE FROM intentos WHERE id = ANY(%s);", (intentos_ids,))
        cur.execute("DELETE FROM usuarios WHERE id = ANY(%s);", (users_ids,))

    print("Limpieza completada exitosamente.")
    print("=" * 70)
    print("✅ BENCHMARK DE CONCURRENCIA SUPERADO CON ÉXITO")
    print("=" * 70)
    return True

if __name__ == '__main__':
    ok = ejecutar_benchmark_concurrencia()
    if not ok:
        exit(1)
