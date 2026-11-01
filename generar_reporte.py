import csv
import json
from functools import lru_cache
from pathlib import Path

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextToPath
import numpy as np

from src.histograma import cdf, histograma
from main import leer

RAIZ = Path(__file__).resolve().parent
plt.rcParams.update({'font.family': 'STIXGeneral', 'mathtext.fontset': 'stix',
                     'pdf.fonttype': 42, 'font.size': 10})
ANCHO, ALTO = 612, 792
MARGEN, COLUMNA = 45, 252


@lru_cache(maxsize=4096)
def medir(texto, tamano=10, negrita=False):
    fuente = FontProperties(family='STIXGeneral', size=tamano,
                           weight='bold' if negrita else 'normal')
    return TextToPath().get_text_width_height_descent(texto, fuente, False)[0]


def envolver(texto, ancho, tamano=10, negrita=False):
    lineas, linea = [], ''
    for palabra in texto.split():
        if medir(palabra, tamano, negrita) > ancho:
            partes, parte = [], ''
            for caracter in palabra:
                if medir(parte + caracter, tamano, negrita) > ancho:
                    partes.append(parte)
                    parte = ''
                parte += caracter
            palabras = partes + [parte]
        else:
            palabras = [palabra]
        for fragmento in palabras:
            candidata = (linea + ' ' + fragmento).strip()
            if linea and medir(candidata, tamano, negrita) > ancho:
                lineas.append(linea)
                linea = fragmento
            else:
                linea = candidata
    if linea:
        lineas.append(linea)
    return lineas


def texto(figura, x, y, contenido, tamano=10, **opciones):
    return figura.text(x / ANCHO, y / ALTO, contenido, fontsize=tamano,
                       va='baseline', **opciones)


def linea(figura, x, y, contenido, ancho, justificar=False, tamano=10, negrita=False):
    palabras = contenido.split()
    estilo = {'fontweight': 'bold' if negrita else 'normal'}
    if not justificar or len(palabras) < 2:
        texto(figura, x, y, contenido, tamano, **estilo)
        return
    espacio = (ancho - sum(medir(p, tamano, negrita) for p in palabras)) / (len(palabras) - 1)
    for palabra in palabras:
        texto(figura, x, y, palabra, tamano, **estilo)
        x += medir(palabra, tamano, negrita) + espacio


class Articulo:
    def __init__(self, pdf):
        self.pdf = pdf
        self.figura = None
        self.columna = 0
        self.y = 738
        self.tope = 738

    def nueva(self, titulo=False):
        self.cerrar()
        self.figura = plt.figure(figsize=(8.5, 11), facecolor='white')
        self.columna, self.y = 0, 738
        if titulo:
            texto(self.figura, 306, 742, 'Especificación de histograma en imágenes', 23, ha='center')
            texto(self.figura, 306, 715, 'Isaac Pérez Pérez', 11, ha='center')
            texto(self.figura, 306, 700, 'Licenciatura en Ingeniería de Datos e Inteligencia Artificial', 10, ha='center')
            texto(self.figura, 306, 687, 'Universidad de Guanajuato', 10, ha='center')
            texto(self.figura, 306, 674, 'Visión por Computadora · Tarea 4', 10, ha='center')
            self.y = 647
        self.tope = self.y

    def cerrar(self):
        if self.figura is not None:
            self.pdf.savefig(self.figura)
            plt.close(self.figura)
            self.figura = None

    def espacio(self, altura):
        if self.y - altura < 54:
            if self.columna == 0:
                self.columna, self.y = 1, self.tope
            else:
                self.nueva()

    def parrafo(self, contenido, tamano=10, negrita=False):
        lineas = envolver(contenido, COLUMNA, tamano, negrita)
        paso = tamano * 1.14
        self.espacio(min(3, len(lineas)) * paso)
        for i, contenido_linea in enumerate(lineas):
            self.espacio(paso)
            x = MARGEN + self.columna * 270
            linea(self.figura, x, self.y, contenido_linea, COLUMNA,
                  justificar=i < len(lineas)-1, tamano=tamano, negrita=negrita)
            self.y -= paso
        self.y -= 5

    def seccion(self, nombre):
        self.espacio(45)
        self.y -= 8
        x = MARGEN + self.columna * 270 + COLUMNA / 2
        texto(self.figura, x, self.y, nombre, 10, ha='center')
        self.y -= 19

    def subtitulo(self, nombre):
        self.espacio(40)
        texto(self.figura, MARGEN + self.columna * 270, self.y, nombre, 10, fontstyle='italic')
        self.y -= 16

    def ecuacion(self, formula, numero):
        self.espacio(36)
        x = MARGEN + self.columna * 270
        texto(self.figura, x + 115, self.y - 5, formula, 11, ha='center')
        texto(self.figura, x + COLUMNA, self.y - 5, f'({numero})', 10, ha='right')
        self.y -= 32


def panel(figura, fuente, referencia, resultado, superior, caption):
    imagenes = [fuente, referencia, resultado]
    rejilla = figura.add_gridspec(3, 3, left=0.09, right=0.94,
                                 top=superior / ALTO, bottom=(superior-284) / ALTO,
                                 height_ratios=[2.2, 1, 1], hspace=0.46, wspace=0.27)
    maximo, histogramas = 0, []
    for imagen in imagenes:
        canales = [imagen] if imagen.ndim == 2 else [imagen[:, :, i] for i in range(3)]
        probabilidades = [histograma(c) / c.size for c in canales]
        histogramas.append((canales, probabilidades))
        maximo = max(maximo, max(p.max() for p in probabilidades))
    for j, (imagen, nombre) in enumerate(zip(imagenes, ['Fuente', 'Referencia', 'Resultado'])):
        eje = figura.add_subplot(rejilla[0, j])
        eje.imshow(imagen if imagen.ndim == 2 else cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB),
                   cmap='gray' if imagen.ndim == 2 else None, vmin=0, vmax=255)
        eje.set_title(nombre, fontsize=9, pad=3)
        eje.axis('off')
        canales, probabilidades = histogramas[j]
        for fila in [1, 2]:
            eje = figura.add_subplot(rejilla[fila, j])
            for i, (canal, probabilidad) in enumerate(zip(canales, probabilidades)):
                color = '#222222' if len(canales) == 1 else ['#235db8', '#22824c', '#c73131'][i]
                eje.plot(probabilidad if fila == 1 else cdf(canal), color=color, lw=0.65)
            eje.set_xlim(0, 255)
            eje.set_ylim(0, maximo*1.08 if fila == 1 else 1.02)
            eje.set_xticks([0, 128, 255])
            eje.tick_params(labelsize=7, pad=1, length=2)
            eje.grid(alpha=0.2, linewidth=0.4)
            if fila == 2:
                eje.set_xlabel('Intensidad', fontsize=8, labelpad=0)
            if j == 0:
                eje.set_ylabel('Frecuencia' if fila == 1 else 'CDF', fontsize=8, labelpad=2)
    for i, fila in enumerate(envolver(caption, 522, 8)):
        texto(figura, 45, superior - 307 - i*9.2, fila, 8)


def main():
    casos = json.loads((RAIZ/'experimentos.json').read_text(encoding='utf-8'))
    with (RAIZ/'resultados/metricas.csv').open(encoding='utf-8') as f:
        metricas = list(csv.DictReader(f))
    ruta = RAIZ/'reporte/T4_Especificacion_Histograma.pdf'
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(ruta, metadata={'Title': 'Especificación de histograma en imágenes',
                                  'Author': 'Isaac Pérez Pérez'}) as pdf:
        a = Articulo(pdf)
        a.nueva(titulo=True)
        a.parrafo('Resumen—Se implementó la especificación de histograma mediante funciones de distribución acumulada y una tabla de correspondencias de 256 niveles. Se evaluaron tres pares de fotografías y una referencia bimodal controlada, en escala de grises y por canales BGR independientes. Los 16 canales evaluados redujeron la distancia entre las distribuciones de salida y referencia. Sin embargo, se observaron pérdida de gradación tonal y colores artificiales. El ajuste estadístico no garantiza una mejor apariencia ni la conservación del significado visual.', tamano=9, negrita=True)
        a.parrafo('Palabras clave—Histograma, CDF, procesamiento de imágenes, transferencia tonal, BGR.', tamano=9, negrita=True)
        a.seccion('I. INTRODUCCIÓN')
        a.parrafo('La especificación de histograma transforma las intensidades de una imagen fuente para aproximar su distribución a la de una referencia [1]. La operación permite modificar el aspecto tonal sin trasladar píxeles. A diferencia de una transformación de contraste fija, la correspondencia depende de las distribuciones de ambas imágenes.')
        a.parrafo('El objetivo de esta práctica es implementar el procedimiento desde cero, comprobarlo con imágenes distintas y explicar sus limitaciones. Se analiza el efecto de una referencia bimodal, la diferencia entre gris y BGR independiente, y su relación con la ecualización clásica. Las Fig. 1–8 muestran los ocho experimentos; la Tabla I resume su ajuste estadístico.')
        a.seccion('II. MÉTODO')
        a.subtitulo('A. Histograma, CDF y correspondencia')
        a.parrafo('Para una imagen de N píxeles y niveles k entre 0 y 255, h(k) es el conteo de píxeles de intensidad k. La frecuencia relativa y su distribución acumulada se definen como:')
        a.ecuacion(r'$p(k)=h(k)/N,\quad F(k)=\sum_{i=0}^{k}p(i).$', 1)
        a.parrafo('La CDF es no decreciente y termina en uno. Se emplea la inversa generalizada discreta de la referencia:')
        a.ecuacion(r'$T(k)=\min\{j:F_{ref}(j)\geq F_{f}(k)\}.$', 2)
        a.parrafo('La salida se obtiene por I_s(x,y)=T(I_f(x,y)). El código usa np.bincount y np.cumsum para los conteos y acumuladas. La tabla se construye con np.searchsorted(..., side="left"), que selecciona el primer nivel cuya CDF alcanza la probabilidad de la fuente [2]. No se utiliza una función de emparejamiento ya implementada.')
        a.parrafo('La correspondencia es monótona, pero no necesariamente invertible: puede reunir varios niveles fuente en un solo nivel de salida. Una intensidad que agrupa muchos píxeles recibe un único destino. Su masa no se puede repartir con esta tabla; por eso el histograma final no tiene que ser idéntico al de referencia. Una fuente constante, por ejemplo, permanece constante.')
        a.subtitulo('B. Datos y protocolo experimental')
        a.parrafo('Se usaron cuatro fotografías públicas del catálogo de scikit-image [3]: cohete (640 × 427), café (600 × 400), astronauta (512 × 512) y gato (451 × 300), expresadas como ancho × alto. Los pares fueron cohete→café, astronauta→gato y café→cohete. No se recortaron ni redimensionaron las imágenes para calcular los histogramas. Las frecuencias relativas permiten comparar tamaños distintos.')
        a.parrafo('El cuarto caso usa la astronauta y una referencia sintética de 256 × 256. Con semilla 2026 se generan dos grupos de 32 768 muestras normales, con medias 48 y 204 y desviación 8. Se redondean, limitan a [20,76] y [176,232], mezclan y replican en B, G y R. La referencia presenta dos bandas separadas y no representa una fotografía.')
        a.parrafo('Cada par se procesa en BGR independiente y en gris. En gris se convierten primero tanto la fuente como la referencia; convertir después la salida BGR es una operación distinta. La salida conserva la forma de la fuente. El cambio BGR→RGB solo se usa para visualizar correctamente los colores.')
        a.subtitulo('C. Verificación y medidas de distribución')
        a.parrafo('Pasaron diez pruebas unitarias que comprueban conteos y CDF, identidad con huecos, mapeo conocido, entradas constantes, monotonía y búsqueda exhaustiva, tamaños diferentes, canales independientes, entradas inválidas y control bimodal/ecualización. La ejecución utiliza Python 3.12.14, NumPy 2.3.5, OpenCV 5.0.0 y Matplotlib 3.10.8; no requiere GPU ni scikit-image como dependencia.')
        a.parrafo('Se calculan dos distancias descriptivas entre la fuente o salida A y la referencia R:')
        a.ecuacion(r'$W_1^{norm}=\frac{1}{255}\sum_{k=0}^{254}|F_A(k)-F_R(k)|,$', 3)
        a.ecuacion(r'$D_{KS}=\max_{0\leq k\leq255}|F_A(k)-F_R(k)|.$', 4)
        a.parrafo('Ambas están entre cero y uno; valores menores indican distribuciones más cercanas. KS se usa sin prueba de hipótesis. Estas medidas no evalúan naturalidad o reconocimiento de objetos. No corresponde calcular RMSE píxel a píxel entre fotografías de escenas distintas.')
        a.cerrar()

        nombres = ['Cohete con referencia de café', 'Astronauta con referencia de gato',
                   'Café con referencia de cohete', 'Astronauta con referencia bimodal sintética']
        for i, caso in enumerate(casos):
            figura = plt.figure(figsize=(8.5, 11), facecolor='white')
            fuente, referencia = leer(RAIZ/caso['fuente']), leer(RAIZ/caso['referencia'])
            for j, modo in enumerate(['bgr', 'gris']):
                f, r = fuente, referencia
                if modo == 'gris':
                    f = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                    r = cv2.cvtColor(r, cv2.COLOR_BGR2GRAY)
                resultado = cv2.imread(str(RAIZ/f"resultados/{caso['nombre']}_{modo}.png"),
                                       cv2.IMREAD_GRAYSCALE if modo == 'gris' else cv2.IMREAD_COLOR)
                caption = (f'Fig. {i*2+j+1}. {nombres[i]}, {"BGR independiente" if modo == "bgr" else "escala de grises"}. '
                           'Arriba: comparación visual. Centro: histogramas normalizados. Abajo: CDF. '
                           + ('Curvas azul, verde y roja: canales B, G y R.' if modo == 'bgr' else 'Se convierten ambas entradas antes del emparejamiento.'))
                panel(figura, f, r, resultado, 738 - j*345, caption)
            pdf.savefig(figura)
            plt.close(figura)

        a = Articulo(pdf)
        a.nueva()
        a.seccion('III. RESULTADOS')
        a.parrafo('La Tabla I muestra W1 normalizada antes y después. Para BGR se promedian sus tres canales; en gris se reporta la única distribución. Las 16 comparaciones por canal redujeron W1. Las distancias KS individuales se conservan en resultados/metricas.csv y no deben interpretarse como una validación perceptual.')
        a.espacio(160)
        x = MARGEN+a.columna*270
        texto(a.figura, x+126, a.y, 'TABLA I', 8, ha='center')
        texto(a.figura, x+126, a.y-12, 'DISTANCIA W1 NORMALIZADA', 8, ha='center')
        a.y -= 28
        for dx, cabecera in [(0,'Caso'),(45,'Modo'),(105,'Antes'),(183,'Después')]:
            texto(a.figura,x+dx,a.y,cabecera,9,fontweight='bold')
        a.y -= 14
        for i, caso in enumerate(casos):
            for modo in ['bgr','gris']:
                filas = [r for r in metricas if r['caso']==caso['nombre'] and r['modo']==modo]
                valores = [str(i+1),modo.upper()] + [f'{np.mean([float(r[c]) for r in filas]):.5f}' for c in ['w1_antes','w1_despues']]
                for dx, valor in zip([0,45,105,183],valores):
                    texto(a.figura,x+dx,a.y,valor,9)
                a.y -= 12
        a.y -= 10
        a.parrafo('En el primer caso (Fig. 1–2), el cohete adquiere una dominante cálida al usar la fotografía del café. En el segundo (Fig. 3–4), el retrato adopta tonos más apagados y cálidos. La fuente contiene numerosos píxeles negros, que forman un salto en la CDF de salida; en gris, KS después es 0.10865. La tabla no puede dividir esa masa entre distintos niveles.')
        a.parrafo('Al invertir el par café/cohete (Fig. 5–6), el café adquiere una dominante azulada y una distribución más oscura. El procedimiento no es simétrico ni necesariamente reversible. En el control bimodal (Fig. 7–8), la salida se concentra en dos bandas; los canales independientes generan colores artificiales y se reduce la gradación tonal del retrato.')
        a.seccion('IV. DISCUSIÓN DE LAS PREGUNTAS')
        a.subtitulo('A. Referencia bimodal y conservación semántica')
        a.parrafo('Una referencia bimodal concentra intensidades alrededor de dos grupos. La transformación aproxima esa distribución y puede separar las zonas oscuras de las claras, con pérdida de tonos intermedios. En la Fig. 8 todavía se reconoce a la persona, pero se pierden gradaciones del rostro y del traje. La posición de los píxeles se conserva; su significado visual no está garantizado. Pueden desaparecer texturas, bordes débiles o colores relevantes. El método no reconoce objetos y la observación visual no sustituye una evaluación semántica automática.')
        a.subtitulo('B. Escala de grises frente a BGR independiente')
        a.parrafo('En gris se empareja una sola distribución de brillo y se descarta el color. En BGR se procesan tres distribuciones marginales por separado [1]. Esto no iguala la distribución conjunta de colores ni mantiene necesariamente las relaciones originales entre canales. Por ello una CDF cercana puede acompañarse de un resultado poco natural.')
        a.parrafo('El control de la Fig. 7 lo muestra claramente: la referencia tiene B=G=R, pero la fuente tiene CDF distintas por canal. Las tres tablas de correspondencia son diferentes, por lo que un píxel fuente puede recibir tres intensidades distintas y seguir siendo coloreado. Una referencia gris no obliga a obtener una salida gris cuando el procesamiento es independiente.')
        a.subtitulo('C. Relación con la ecualización clásica')
        a.parrafo('La ecualización transforma las intensidades mediante la CDF de la fuente para extender el rango y aproximarse a una distribución uniforme [4]. La especificación añade la inversa de una CDF objetivo. En el caso continuo, elegir una referencia uniforme conduce a la ecualización. En imágenes discretas, los empates y la cuantización impiden garantizar uniformidad exacta.')
        a.parrafo('La función ecualizar del proyecto usa round(255 F(k)), sin restar CDF_min. Puede diferir de cv2.equalizeHist. Esta diferencia de convención no cambia la relación conceptual entre ambos métodos y se declara para no atribuir equivalencia numérica exacta a implementaciones distintas.')
        a.seccion('V. CONCLUSIONES')
        a.parrafo('La implementación aproxima las distribuciones de referencia en los cuatro casos y mantiene el tamaño de cada fuente. Los histogramas y CDF comprueban el cambio estadístico, mientras las comparaciones visuales muestran sus límites. Una referencia bimodal puede eliminar gradación; el procesamiento BGR puede alterar colores relevantes. La conservación semántica no está garantizada por una mejora de W1 o KS. Las conclusiones se limitan a estos cuatro pares seleccionados.')
        a.parrafo('El proyecto incluye los originales y sus hashes. Puede reproducirse sin red con python main.py y python generar_reporte.py, tras instalar requirements.txt. Las fotografías se atribuyen a NASA (astronauta), Rachel Michetti (café), Stefan van der Walt (gato) y SpaceX (cohete), con sus condiciones registradas en datos/fuentes.csv [3].')
        a.seccion('REFERENCIAS')
        referencias = [
            '[1] scikit-image contributors, “Histogram matching,” scikit-image 0.22.0 documentation. [En línea]. Disponible: https://scikit-image.org/docs/0.22.x/auto_examples/color_exposure/plot_histogram_matching.html. [Consultado: 31-oct-2026].',
            '[2] NumPy developers, “numpy.searchsorted,” NumPy documentation. [En línea]. Disponible: https://numpy.org/doc/stable/reference/generated/numpy.searchsorted.html. [Consultado: 31-oct-2026].',
            '[3] scikit-image contributors, “skimage/data/_fetchers.py,” scikit-image, v0.19.3, GitHub. [En línea]. Disponible: https://github.com/scikit-image/scikit-image/blob/v0.19.3/skimage/data/_fetchers.py. [Consultado: 31-oct-2026].',
            '[4] A. Huamán, “Histogram Equalization,” OpenCV 4.11.0 documentation. [En línea]. Disponible: https://docs.opencv.org/4.11.0/d4/d1b/tutorial_histogram_equalization.html. [Consultado: 31-oct-2026].']
        for referencia in referencias:
            a.parrafo(referencia, tamano=8)
        a.cerrar()
    print(ruta)


if __name__ == '__main__':
    main()
