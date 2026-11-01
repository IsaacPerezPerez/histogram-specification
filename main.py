import argparse
import csv
import hashlib
import json
from pathlib import Path

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from src.histograma import cdf, distancia_cdf, especificar_bgr, especificar_canal, histograma

RAIZ = Path(__file__).resolve().parent
COLORES = ['#2463b5', '#23834b', '#cb3333']


def leer(ruta):
    imagen = cv2.imdecode(np.fromfile(ruta, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if imagen is None:
        raise ValueError(f'No se pudo leer: {ruta}')
    if imagen.dtype != np.uint8 or imagen.ndim != 3 or imagen.shape[2] != 3:
        raise ValueError(f'La entrada debe ser BGR uint8 sin transparencia: {ruta}')
    return imagen


def guardar(ruta, imagen):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ok, datos = cv2.imencode(ruta.suffix, imagen)
    if not ok:
        raise ValueError(f'No se pudo guardar: {ruta}')
    datos.tofile(ruta)


def preparar_control():
    generador = np.random.default_rng(2026)
    oscuros = np.clip(np.rint(generador.normal(48, 8, 32768)), 20, 76)
    claros = np.clip(np.rint(generador.normal(204, 8, 32768)), 176, 232)
    niveles = np.concatenate([oscuros, claros]).astype(np.uint8)
    generador.shuffle(niveles)
    imagen = np.repeat(niveles.reshape(256, 256, 1), 3, axis=2)
    guardar(RAIZ / 'datos/control/bimodal.png', imagen)


def comparar(fuente, referencia, resultado, titulo, destino):
    imagenes = [fuente, referencia, resultado]
    figura, ejes = plt.subplots(3, 3, figsize=(11.69, 8.27),
                               gridspec_kw={'height_ratios': [2.15, 1, 1]})
    figura.suptitle(titulo, fontsize=16, fontweight='bold')
    maximo = 0
    for columna, (imagen, nombre) in enumerate(zip(imagenes, ['Fuente', 'Referencia', 'Resultado'])):
        gris = imagen.ndim == 2
        visible = imagen if gris else cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        ejes[0, columna].imshow(visible, cmap='gray' if gris else None, vmin=0, vmax=255)
        ejes[0, columna].set_title(f'{nombre} ({imagen.shape[1]} × {imagen.shape[0]})')
        ejes[0, columna].axis('off')
        canales = [imagen] if gris else [imagen[:, :, i] for i in range(3)]
        for i, canal in enumerate(canales):
            color = '#333333' if gris else COLORES[i]
            etiqueta = 'Gris' if gris else ['B', 'G', 'R'][i]
            probabilidad = histograma(canal) / canal.size
            maximo = max(maximo, probabilidad.max())
            ejes[1, columna].plot(probabilidad, color=color, label=etiqueta, linewidth=0.8)
            ejes[2, columna].plot(cdf(canal), color=color, linewidth=1)
        ejes[1, columna].legend(fontsize=8, loc='upper right')
        for fila in [1, 2]:
            ejes[fila, columna].set_xlim(0, 255)
            ejes[fila, columna].set_xlabel('Intensidad (0-255)', fontsize=9)
            ejes[fila, columna].grid(alpha=0.2)
            ejes[fila, columna].tick_params(labelsize=8)
        ejes[2, columna].set_ylim(0, 1.02)
    for eje in ejes[1]:
        eje.set_ylim(0, maximo * 1.08)
    ejes[1, 0].set_ylabel('Frecuencia relativa')
    ejes[2, 0].set_ylabel('CDF')
    figura.tight_layout(rect=(0, 0, 1, 0.95))
    figura.savefig(destino, dpi=160)
    return figura


def ejecutar_par(fuente, referencia, salida, nombre):
    salida.mkdir(parents=True, exist_ok=True)
    filas = []
    for modo in ['bgr', 'gris']:
        if modo == 'gris':
            original = cv2.cvtColor(fuente, cv2.COLOR_BGR2GRAY)
            objetivo = cv2.cvtColor(referencia, cv2.COLOR_BGR2GRAY)
            resultado = especificar_canal(original, objetivo)
            canales = [('Gris', original, objetivo, resultado)]
        else:
            original, objetivo = fuente, referencia
            resultado = especificar_bgr(fuente, referencia)
            canales = [(etiqueta, original[:, :, i], objetivo[:, :, i], resultado[:, :, i])
                       for i, etiqueta in enumerate(['B', 'G', 'R'])]
        guardar(salida / f'{nombre}_{modo}.png', resultado)
        figura = comparar(original, objetivo, resultado, f'{nombre} - {modo.upper()}',
                          salida / f'{nombre}_{modo}_comparacion.png')
        plt.close(figura)
        for etiqueta, canal_fuente, canal_ref, canal_salida in canales:
            antes, ks_antes = distancia_cdf(canal_fuente, canal_ref)
            despues, ks_despues = distancia_cdf(canal_salida, canal_ref)
            filas.append({'caso': nombre, 'modo': modo, 'canal': etiqueta,
                          'w1_antes': antes, 'w1_despues': despues,
                          'ks_antes': ks_antes, 'ks_despues': ks_despues})
    return filas


def escribir_metricas(filas, destino):
    with destino.open('w', newline='', encoding='utf-8') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]), lineterminator='\n')
        escritor.writeheader()
        escritor.writerows(filas)


def main():
    parser = argparse.ArgumentParser(description='Especificación de histograma en BGR y gris.')
    parser.add_argument('--fuente', type=Path)
    parser.add_argument('--referencia', type=Path)
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args()
    if bool(args.fuente) != bool(args.referencia):
        parser.error('Indica tanto --fuente como --referencia.')
    salida = args.salida or RAIZ / 'resultados'
    salida.mkdir(parents=True, exist_ok=True)
    if args.fuente:
        filas = ejecutar_par(leer(args.fuente), leer(args.referencia), salida, 'personalizado')
    else:
        preparar_control()
        casos = json.loads((RAIZ / 'experimentos.json').read_text(encoding='utf-8'))
        filas = []
        for caso in casos:
            filas.extend(ejecutar_par(leer(RAIZ / caso['fuente']), leer(RAIZ / caso['referencia']),
                                     salida, caso['nombre']))
        manifiesto = {str(p.relative_to(RAIZ)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted((RAIZ / 'datos').rglob('*'))
                      if p.suffix.lower() in ['.jpg', '.png']}
        (RAIZ / 'datos/manifest.json').write_text(json.dumps(manifiesto, indent=2) + '\n')
        versiones = {'python': __import__('platform').python_version(), 'opencv': cv2.__version__,
                     'numpy': np.__version__, 'matplotlib': matplotlib.__version__}
        (salida / 'entorno.json').write_text(json.dumps(versiones, indent=2) + '\n')
    escribir_metricas(filas, salida / 'metricas.csv')
    print(f'Resultados guardados en {salida}')


if __name__ == '__main__':
    main()
