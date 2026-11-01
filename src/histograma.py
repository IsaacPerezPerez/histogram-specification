import numpy as np


def validar_canal(canal):
    if canal.dtype != np.uint8 or canal.ndim != 2 or canal.size == 0:
        raise ValueError('Se requiere un canal uint8 de dos dimensiones no vacío.')


def histograma(canal):
    validar_canal(canal)
    return np.bincount(canal.ravel(), minlength=256)


def cdf(canal):
    return np.cumsum(histograma(canal), dtype=np.float64) / canal.size


def crear_lut(fuente, referencia):
    acumulada_fuente = cdf(fuente)
    acumulada_referencia = cdf(referencia)
    # Inversa discreta: primer nivel cuya CDF alcanza la probabilidad fuente.
    tabla = np.searchsorted(acumulada_referencia, acumulada_fuente, side='left')
    return np.clip(tabla, 0, 255).astype(np.uint8)


def especificar_canal(fuente, referencia):
    return crear_lut(fuente, referencia)[fuente]


def especificar_bgr(fuente, referencia):
    for imagen in (fuente, referencia):
        if imagen.ndim != 3 or imagen.shape[2] != 3:
            raise ValueError('Se requiere una imagen BGR de tres canales.')
    canales = [especificar_canal(fuente[:, :, i], referencia[:, :, i])
               for i in range(3)]
    return np.stack(canales, axis=2)


def ecualizar(canal):
    validar_canal(canal)
    tabla = np.rint(255 * cdf(canal)).astype(np.uint8)
    return tabla[canal]


def distancia_cdf(canal, referencia):
    diferencia = np.abs(cdf(canal) - cdf(referencia))
    return float(diferencia[:-1].sum() / 255), float(diferencia.max())
