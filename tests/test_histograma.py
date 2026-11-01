import unittest

import numpy as np

from src.histograma import cdf, crear_lut, distancia_cdf, ecualizar, especificar_bgr, especificar_canal, histograma


class PruebasHistograma(unittest.TestCase):
    def test_conteo_y_cdf(self):
        imagen = np.array([[0, 0, 128, 255]], dtype=np.uint8)
        self.assertEqual(histograma(imagen).sum(), 4)
        self.assertEqual(cdf(imagen)[0], 0.5)
        self.assertEqual(cdf(imagen)[-1], 1.0)

    def test_identidad_con_huecos(self):
        imagen = np.array([[4, 4, 50], [90, 200, 200]], dtype=np.uint8)
        np.testing.assert_array_equal(especificar_canal(imagen, imagen), imagen)

    def test_mapeo_conocido(self):
        fuente = np.array([[0, 0, 100, 255]], dtype=np.uint8)
        referencia = np.array([[10, 10, 80, 200]], dtype=np.uint8)
        esperado = np.array([[10, 10, 80, 200]], dtype=np.uint8)
        np.testing.assert_array_equal(especificar_canal(fuente, referencia), esperado)

    def test_referencia_constante(self):
        fuente = np.arange(256, dtype=np.uint8).reshape(16, 16)
        resultado = especificar_canal(fuente, np.full((2, 3), 70, dtype=np.uint8))
        self.assertTrue(np.all(resultado == 70))

    def test_fuente_constante_no_se_divide(self):
        fuente = np.full((3, 4), 50, dtype=np.uint8)
        referencia = np.array([[20, 220]], dtype=np.uint8)
        self.assertTrue(np.all(especificar_canal(fuente, referencia) == 220))

    def test_lut_monotona_y_oraculo(self):
        rng = np.random.default_rng(2)
        fuente = rng.integers(0, 256, (20, 30), dtype=np.uint8)
        referencia = rng.integers(10, 230, (8, 9), dtype=np.uint8)
        tabla = crear_lut(fuente, referencia)
        esperado = [next(j for j in range(256) if cdf(referencia)[j] >= p)
                    for p in cdf(fuente)]
        np.testing.assert_array_equal(tabla, esperado)
        self.assertTrue(np.all(np.diff(tabla.astype(int)) >= 0))

    def test_tamanos_distintos(self):
        fuente = np.array([[0, 0, 255, 255]], dtype=np.uint8)
        referencia = np.array([[40, 220]], dtype=np.uint8)
        resultado = especificar_canal(fuente, referencia)
        self.assertEqual(resultado.shape, fuente.shape)
        self.assertEqual(resultado.dtype, np.uint8)
        self.assertEqual(distancia_cdf(resultado, referencia), (0.0, 0.0))

    def test_canales_independientes(self):
        fuente = np.zeros((3, 4, 3), dtype=np.uint8)
        referencia = np.full((2, 2, 3), [20, 100, 230], dtype=np.uint8)
        resultado = especificar_bgr(fuente, referencia)
        np.testing.assert_array_equal(resultado, np.full_like(fuente, [20, 100, 230]))

    def test_rechaza_entradas_invalidas(self):
        for imagen in [np.array([], dtype=np.uint8), np.zeros((2, 2)), np.zeros((0, 3), dtype=np.uint8)]:
            with self.assertRaises(ValueError):
                cdf(imagen)
        with self.assertRaises(ValueError):
            especificar_bgr(np.zeros((3, 3), dtype=np.uint8), np.zeros((3, 3), dtype=np.uint8))

    def test_bimodal_y_relacion_ecualizacion(self):
        fuente = np.arange(256, dtype=np.uint8).reshape(16, 16)
        referencia = np.array([[40, 220]], dtype=np.uint8)
        resultado = especificar_canal(fuente, referencia)
        np.testing.assert_array_equal(np.unique(resultado, return_counts=True)[1], [128, 128])
        uniforme = especificar_canal(fuente, fuente)
        self.assertLessEqual(np.max(np.abs(uniforme.astype(int) - ecualizar(fuente).astype(int))), 1)


if __name__ == '__main__':
    unittest.main()
