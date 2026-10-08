import unittest
from pathlib import Path
from utils.descargar_modelos import MODEL_CATALOG, verificar_archivo_local

class TestModelosVision(unittest.TestCase):
    """Pruebas de integridad y catálogo de modelos de visión artificial (face-api.js)."""

    def setUp(self):
        self.raiz = Path(__file__).resolve().parent.parent
        self.models_dir = self.raiz / "static" / "models"

    def test_catalogo_contiene_modelos_requeridos(self):
        """Verifica que el catálogo incluya los 3 modelos necesarios y la librería cliente."""
        requeridos = [nombre for nombre, info in MODEL_CATALOG.items() if info["required"]]
        esperados = [
            "face-api.min.js",
            "tiny_face_detector_model-weights_manifest.json",
            "tiny_face_detector_model-shard1",
            "face_landmark_68_tiny_model-weights_manifest.json",
            "face_landmark_68_tiny_model-shard1",
            "face_recognition_model-weights_manifest.json",
            "face_recognition_model-shard1",
            "face_recognition_model-shard2",
        ]
        for esp in esperados:
            self.assertIn(esp, requeridos, f"Falta {esp} en los modelos requeridos del catálogo")

    def test_archivos_locales_existen_y_son_autenticos(self):
        """Verifica que todos los archivos requeridos en static/models sean auténticos."""
        for nombre, info in MODEL_CATALOG.items():
            if info["required"]:
                ruta = self.models_dir / nombre
                self.assertTrue(ruta.exists(), f"El archivo {nombre} no existe en {self.models_dir}")
                valido, motivo = verificar_archivo_local(ruta, info)
                self.assertTrue(valido, f"El archivo {nombre} falló la verificación: {motivo}")

if __name__ == "__main__":
    unittest.main()
