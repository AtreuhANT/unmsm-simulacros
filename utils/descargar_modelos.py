#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Script: descargar_modelos.py
Propósito: Descarga y verifica automáticamente los modelos de visión
           artificial de face-api.js y su librería en static/models/.
=============================================================================
Este script resuelve el problema:
"ERROR IA: No se pudieron cargar los modelos de visión artificial locales"
al garantizar que los archivos de pesos binarios (shards), los manifiestos JSON
y la librería face-api.min.js sean auténticos y no estén corruptos.

Modelos requeridos por el sistema (registro y examen):
  1. Tiny Face Detector (detección rápida de rostros en navegador)
  2. Face Landmark 68 Tiny (puntos faciales de 68 referencias)
  3. Face Recognition (vectorización biométrica de 128 descriptores)
  4. face-api.min.js (librería cliente principal)

Uso por consola:
  python utils/descargar_modelos.py               # Descarga requeridos faltantes o corruptos
  python utils/descargar_modelos.py --force       # Re-descarga todo obligatoriamente
  python utils/descargar_modelos.py --check       # Solo audita la integridad local
  python utils/descargar_modelos.py --all         # Descarga requeridos + modelos opcionales
=============================================================================
"""

import os
import sys
import json
import time
import hashlib
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# Configurar stdout para evitar fallos de codificación en consolas Windows (cp1252 / cmd / powershell)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# =============================================================================
# CATÁLOGO DE MODELOS Y VERIFICACIÓN SHA-256
# =============================================================================

MODEL_CATALOG = {
    # -------------------------------------------------------------------------
    # 1. LIBRERÍA CLIENTE FACE-API.JS
    # -------------------------------------------------------------------------
    "face-api.min.js": {
        "description": "Librería face-api.js minificada para el cliente",
        "relative_urls": [
            "dist/face-api.min.js"
        ],
        "absolute_urls": [
            "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/dist/face-api.min.js",
            "https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/dist/face-api.min.js",
            "https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js",
        ],
        "size": 663829,
        "sha256": "5d66ec95338d7fcc365ce15481b8599baf4b6e22c9a624b76d4ca821a669a659",
        "required": True,
        "type": "library"
    },

    # -------------------------------------------------------------------------
    # 2. TINY FACE DETECTOR (REQUERIDO)
    # -------------------------------------------------------------------------
    "tiny_face_detector_model-weights_manifest.json": {
        "description": "Manifiesto Tiny Face Detector",
        "relative_urls": ["weights/tiny_face_detector_model-weights_manifest.json"],
        "size": 2953,
        "sha256": "14c60659a31b6b7b1320077171b8f8adcb24ef0e62dde62ce603bcb49a1b49b5",
        "required": True,
        "type": "manifest"
    },
    "tiny_face_detector_model-shard1": {
        "description": "Pesos binarios Tiny Face Detector",
        "relative_urls": ["weights/tiny_face_detector_model-shard1"],
        "size": 193321,
        "sha256": "b7503ce7df31039b1c43316a9b865cab6a70dd748cc602d3fa28b551503c3871",
        "required": True,
        "type": "weights"
    },

    # -------------------------------------------------------------------------
    # 3. FACE LANDMARK 68 TINY NET (REQUERIDO)
    # -------------------------------------------------------------------------
    "face_landmark_68_tiny_model-weights_manifest.json": {
        "description": "Manifiesto Landmark 68 Tiny",
        "relative_urls": ["weights/face_landmark_68_tiny_model-weights_manifest.json"],
        "size": 4441,
        "sha256": "3c63b8984302c187b218d9ef5aa149ed8c2c7fa3fe54db078614692bc48d153c",
        "required": True,
        "type": "manifest"
    },
    "face_landmark_68_tiny_model-shard1": {
        "description": "Pesos binarios Landmark 68 Tiny",
        "relative_urls": ["weights/face_landmark_68_tiny_model-shard1"],
        "size": 77224,
        "sha256": "b98e9f2f7da76f8a6dda9741a36ed485b224b889d552de2b2c1bb16217f67bfc",
        "required": True,
        "type": "weights"
    },

    # -------------------------------------------------------------------------
    # 4. FACE RECOGNITION NET (REQUERIDO PARA ENROLAMIENTO Y SUPERVISIÓN)
    # -------------------------------------------------------------------------
    "face_recognition_model-weights_manifest.json": {
        "description": "Manifiesto Face Recognition Net",
        "relative_urls": ["weights/face_recognition_model-weights_manifest.json"],
        "size": 18303,
        "sha256": "6619f4126f845c1f7857f39cbd79565f375734f46e0dd25d9602f8dc21cda9f5",
        "required": True,
        "type": "manifest"
    },
    "face_recognition_model-shard1": {
        "description": "Pesos binarios Face Recognition (Parte 1/2)",
        "relative_urls": ["weights/face_recognition_model-shard1"],
        "size": 4194304,
        "sha256": "412566a2b8d814d84c60b8055ec5d3b3b2328ef7cd7853384e03ec3db7b053d8",
        "required": True,
        "type": "weights"
    },
    "face_recognition_model-shard2": {
        "description": "Pesos binarios Face Recognition (Parte 2/2)",
        "relative_urls": ["weights/face_recognition_model-shard2"],
        "size": 2249728,
        "sha256": "69350fdecd845c532e44dd8f7d0521c773505ef46b87cc34f46640a0cc334ecc",
        "required": True,
        "type": "weights"
    },

    # -------------------------------------------------------------------------
    # 5. MODELOS OPCIONALES / ADICIONALES (SE ACTIVAN CON --all)
    # -------------------------------------------------------------------------
    "face_landmark_68_model-weights_manifest.json": {
        "description": "Manifiesto Landmark 68 Estándar (Opcional)",
        "relative_urls": ["weights/face_landmark_68_model-weights_manifest.json"],
        "size": 7889,
        "sha256": "d30f6cc341009ea4f8223876959289b96576fc54a2615f92da9741ab9c5f0bbc",
        "required": False,
        "type": "manifest"
    },
    "face_landmark_68_model-shard1": {
        "description": "Pesos binarios Landmark 68 Estándar (Opcional)",
        "relative_urls": ["weights/face_landmark_68_model-shard1"],
        "size": 356840,
        "sha256": "4611ef65c87d836d03d684b30eec4d195d8b219fa1dd58fc58945831c6b9299b",
        "required": False,
        "type": "weights"
    },
    "ssd_mobilenetv1_model-weights_manifest.json": {
        "description": "Manifiesto SSD MobileNet V1 (Opcional)",
        "relative_urls": ["weights/ssd_mobilenetv1_model-weights_manifest.json"],
        "size": 26548,
        "sha256": "9b84918d1d8b2e988dc5d72c0d77e7cc0a3d433f2452516fcd88dca8051b552f",
        "required": False,
        "type": "manifest"
    },
    "ssd_mobilenetv1_model-shard1": {
        "description": "Pesos SSD MobileNet V1 Parte 1 (Opcional)",
        "relative_urls": ["weights/ssd_mobilenetv1_model-shard1"],
        "size": 4194304,
        "sha256": "6ff16f095b0371f24accb48aab82e595697baa821cf851167cbf9203d1d7ec9a",
        "required": False,
        "type": "weights"
    },
    "ssd_mobilenetv1_model-shard2": {
        "description": "Pesos SSD MobileNet V1 Parte 2 (Opcional)",
        "relative_urls": ["weights/ssd_mobilenetv1_model-shard2"],
        "size": 1422653,
        "sha256": "2539847e627c8c4a561e999170735e6c527deecc6fdba2959fc5312fb1ea1de3",
        "required": False,
        "type": "weights"
    },
    "face_expression_model-weights_manifest.json": {
        "description": "Manifiesto Expresiones Faciales (Opcional)",
        "relative_urls": ["weights/face_expression_model-weights_manifest.json"],
        "size": 6384,
        "sha256": "960cbe959fe0328965dd18662d839f197df6e27607da4f726cd0c826e47fc936",
        "required": False,
        "type": "manifest"
    },
    "face_expression_model-shard1": {
        "description": "Pesos Expresiones Faciales (Opcional)",
        "relative_urls": ["weights/face_expression_model-shard1"],
        "size": 329468,
        "sha256": "9a9840f2cf1f4c7eab95f197512569345c00d2426754d4608b92af30e0300f3d",
        "required": False,
        "type": "weights"
    },
    "age_gender_model-weights_manifest.json": {
        "description": "Manifiesto Edad y Género (Opcional)",
        "relative_urls": ["weights/age_gender_model-weights_manifest.json"],
        "size": 7774,
        "sha256": "780ca481c12f6501c63e3551caa4df9bc4a05ffc5357060079b75badfd350d86",
        "required": False,
        "type": "manifest"
    },
    "age_gender_model-shard1": {
        "description": "Pesos Edad y Género (Opcional)",
        "relative_urls": ["weights/age_gender_model-shard1"],
        "size": 429708,
        "sha256": "49f92bbc0afef2342c4385e4a2b0acb6d7a727c6f0aa539499719a81acf9abaa",
        "required": False,
        "type": "weights"
    }
}

# Servidores espejo (mirrors) para redundancia
MIRROR_BASES = [
    "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/",
    "https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def calcular_sha256(filepath: Path) -> str:
    """Calcula el hash SHA-256 de un archivo local en bloques de 64KB."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()

def formatear_tamano(bytes_num: int) -> str:
    """Convierte bytes a formato legible (KB / MB)."""
    if bytes_num < 1024:
        return f"{bytes_num} B"
    elif bytes_num < 1024 * 1024:
        return f"{bytes_num / 1024:.1f} KB"
    else:
        return f"{bytes_num / (1024 * 1024):.2f} MB"

def dibujar_progreso(descargado: int, total: int, filename: str):
    """Muestra una barra de progreso limpia en la misma línea."""
    ancho = 24
    if total > 0:
        porcentaje = min(1.0, descargado / total)
        llenos = int(ancho * porcentaje)
        barra = "=" * llenos + "-" * (ancho - llenos)
        texto = f"\r   [{barra}] {porcentaje*100:5.1f}% ({formatear_tamano(descargado)} / {formatear_tamano(total)}) {filename[:28]}"
    else:
        barra = "." * ancho
        texto = f"\r   [{barra}] {formatear_tamano(descargado)} {filename[:28]}"
    
    sys.stdout.write(texto)
    sys.stdout.flush()

def obtener_urls_candidatas(filename: str, info: dict) -> list:
    """Genera lista ordenada de URLs candidatas probando fuentes oficiales y espejos."""
    urls = []
    if "absolute_urls" in info:
        urls.extend(info["absolute_urls"])
    
    for rel in info.get("relative_urls", []):
        for base in MIRROR_BASES:
            urls.append(f"{base}{rel}")
    
    # Eliminar duplicados preservando orden
    vistos = set()
    unicas = []
    for u in urls:
        if u not in vistos:
            vistos.add(u)
            unicas.append(u)
    return unicas

def verificar_archivo_local(filepath: Path, info: dict) -> tuple:
    """
    Verifica si un archivo local existe y es válido.
    Retorna: (es_valido: bool, motivo: str)
    """
    if not filepath.exists():
        return False, "No existe"
    
    tamano_real = filepath.stat().st_size
    if tamano_real == 0:
        return False, "Archivo vacío (0 bytes)"
    
    # Si tenemos tamaño esperado y difiere significativamente
    if info.get("size") and tamano_real != info["size"]:
        return False, f"Tamaño incorrecto ({tamano_real} != {info['size']})"
    
    # Validación específica por tipo
    if info.get("type") == "library":
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(100)
            if not head.startswith("!function") and "faceapi" not in head:
                return False, "Cabecera JavaScript corrupta o binaria"
        except Exception:
            return False, "Error al leer contenido de la librería"
            
    elif info.get("type") == "manifest":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list) or not data or "weights" not in data[0]:
                return False, "Estructura JSON de manifiesto inválida"
        except Exception as e:
            return False, f"JSON no parseable ({e})"

    # Verificación estricta de hash SHA-256
    hash_esperado = info.get("sha256")
    if hash_esperado:
        hash_real = calcular_sha256(filepath)
        if hash_real != hash_esperado:
            return False, f"Hash SHA-256 no coincide ({hash_real[:8]}... != {hash_esperado[:8]}...)"
    
    return True, "OK (Auténtico y Válido)"

def descargar_archivo(urls: list, destino: Path, filename: str, info: dict, reintentos: int = 3) -> bool:
    """
    Descarga un archivo con barra de progreso y fallback entre servidores espejo.
    Descarga primero a un archivo temporal .tmp y luego lo renombra atómicamente.
    """
    tmp_path = destino.with_suffix(destino.suffix + ".tmp")
    tamano_esperado = info.get("size", 0)

    for url in urls:
        for intento in range(1, reintentos + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    total_bytes = int(resp.headers.get("Content-Length", tamano_esperado))
                    descargados = 0
                    
                    with open(tmp_path, "wb") as f_out:
                        while True:
                            bloque = resp.read(65536)
                            if not bloque:
                                break
                            f_out.write(bloque)
                            descargados += len(bloque)
                            dibujar_progreso(descargados, total_bytes, filename)
                
                # Salto de línea al terminar la barra
                sys.stdout.write("\n")
                sys.stdout.flush()

                # Reemplazo atómico
                if tmp_path.exists():
                    if destino.exists():
                        destino.unlink()
                    tmp_path.rename(destino)

                # Validar integridad del archivo recién descargado
                valido, motivo = verificar_archivo_local(destino, info)
                if valido:
                    return True
                else:
                    print(f"   [!] Advertencia: {filename} descargado no superó validación: {motivo}")
                    if destino.exists():
                        destino.unlink()
            
            except (urllib.error.URLError, TimeoutError, ConnectionResetError) as e:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                if intento < reintentos:
                    time.sleep(1.0)
                    continue
            except Exception as e:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                break
    
    return False

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def ejecutar_descarga(
    output_dir: Path = None, 
    incluir_todos: bool = False, 
    forzar: bool = False, 
    solo_verificar: bool = False
) -> bool:
    """
    Ejecuta el flujo de validación y descarga de modelos.
    """
    if output_dir is None:
        raiz_proyecto = Path(__file__).resolve().parent.parent
        output_dir = raiz_proyecto / "static" / "models"
    
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("   GESTOR DE MODELOS DE VISIÓN ARTIFICIAL (face-api.js) - UNMSM")
    print("=" * 72)
    print(f"-> Directorio destino: {output_dir}")
    print(f"-> Modo de operación:  {'Solo Verificación' if solo_verificar else ('Forzar descarga completa' if forzar else 'Descarga inteligente (repara corruptos)')}")
    print(f"-> Conjunto:           {'Todos los modelos (incluye opcionales)' if incluir_todos else 'Modelos requeridos para supervisión/enrolamiento'}")
    print("-" * 72)

    archivos_a_procesar = [
        (nombre, info) for nombre, info in MODEL_CATALOG.items()
        if info["required"] or incluir_todos
    ]

    total_archivos = len(archivos_a_procesar)
    archivos_ok = 0
    archivos_reparados = 0
    archivos_fallidos = 0
    bytes_totales_descargados = 0

    tiempo_inicio = time.time()

    for idx, (filename, info) in enumerate(archivos_a_procesar, start=1):
        target_path = output_dir / filename
        es_valido, motivo = verificar_archivo_local(target_path, info)

        print(f"\n[{idx}/{total_archivos}] {filename}")
        print(f"    Función: {info['description']} ({formatear_tamano(info['size'])})")

        if solo_verificar:
            if es_valido:
                print("    Estado:  [OK] Válido y Auténtico")
                archivos_ok += 1
            else:
                print(f"    Estado:  [ERROR] {motivo}")
                archivos_fallidos += 1
            continue

        if es_valido and not forzar:
            print("    Estado:  [OK] Ya existe y es auténtico. Omitiendo descarga.")
            archivos_ok += 1
            continue

        if not es_valido and target_path.exists():
            print(f"    Detectado archivo inválido o corrupto: {motivo}")
            print("    Iniciando re-descarga y reparación...")
        else:
            print("    Descargando archivo desde repositorio oficial...")

        urls = obtener_urls_candidatas(filename, info)
        exito = descargar_archivo(urls, target_path, filename, info)

        if exito:
            archivos_reparados += 1
            bytes_totales_descargados += info["size"]
            print("    Resultado: [CORRECTO] Descargado y verificado exitosamente.")
        else:
            archivos_fallidos += 1
            print("    Resultado: [FALLO] No se pudo descargar desde ninguna fuente.")

    tiempo_total = time.time() - tiempo_inicio

    print("\n" + "=" * 72)
    print("                     RESUMEN DE OPERACIÓN")
    print("=" * 72)
    print(f"  Tiempo transcurrido:       {tiempo_total:.2f} segundos")
    print(f"  Archivos verificados OK:   {archivos_ok}")
    print(f"  Archivos descargados/fijados: {archivos_reparados}")
    print(f"  Datos transferidos:        {formatear_tamano(bytes_totales_descargados)}")
    print(f"  Archivos con errores:      {archivos_fallidos}")
    print("=" * 72)

    if archivos_fallidos == 0:
        print("\n [ÉXITO TOTAL] Todos los modelos de visión artificial están listos.")
        print(" -> Ahora la pantalla de registro y el simulacro cargarán la IA sin errores.\n")
        return True
    else:
        print("\n [ATENCIÓN] Algunos modelos no pudieron descargarse.")
        print(" -> Revisa tu conexión a internet o ejecuta nuevamente con: python utils/descargar_modelos.py --force\n")
        return False

# =============================================================================
# ENTRADA DE LÍNEA DE COMANDOS
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descargador y auditor automático de modelos de face-api.js para el sistema UNMSM."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Descargar todos los modelos (incluyendo SSD MobileNet, 68 Landmarks completo, expresiones, etc.)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Forzar la re-descarga de todos los archivos incluso si ya existen localmente.",
    )
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Auditar la integridad y autenticidad de los modelos locales sin descargar nada.",
    )
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=None,
        help="Ruta personalizada para el directorio static/models.",
    )

    args = parser.parse_args()
    
    dir_salida = Path(args.dir).resolve() if args.dir else None
    exito = ejecutar_descarga(
        output_dir=dir_salida,
        incluir_todos=args.all,
        forzar=args.force,
        solo_verificar=args.check
    )

    sys.exit(0 if exito else 1)
