import csv
import json
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

RAIZ = Path(__file__).resolve().parent
AZUL = '#203b60'


def pagina(titulo, numero):
    figura = plt.figure(figsize=(11.69, 8.27), facecolor='white')
    figura.text(0.055, 0.93, titulo, fontsize=21, color=AZUL, fontweight='bold')
    figura.text(0.055, 0.035, 'Visión por Computadora | T4 | Isaac Pérez Pérez', fontsize=9, color='#555555')
    figura.text(0.94, 0.035, str(numero), fontsize=9, ha='right', color='#555555')
    return figura


def columna(figura, bloques, x, y=0.845, ancho=64):
    for subtitulo, texto in bloques:
        figura.text(x, y, subtitulo, fontsize=12, fontweight='bold', color=AZUL, va='top')
        y -= 0.038
        for parrafo in texto.split('\n'):
            lineas = textwrap.wrap(parrafo, width=ancho, break_long_words=True, break_on_hyphens=False)
            figura.text(x, y, '\n'.join(lineas), fontsize=10.6, linespacing=1.4, va='top')
            y -= max(1, len(lineas)) * 0.0245 + 0.015
        y -= 0.018
    if y < 0.075:
        raise ValueError(f'Texto demasiado largo para la página: {y:.3f}')


def guardar(pdf, figura):
    pdf.savefig(figura)
    plt.close(figura)


def main():
    with (RAIZ / 'resultados/metricas.csv').open(encoding='utf-8') as archivo:
        filas = list(csv.DictReader(archivo))
    casos = json.loads((RAIZ / 'experimentos.json').read_text(encoding='utf-8'))
    ruta = RAIZ / 'reporte/T4_Especificacion_Histograma.pdf'
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(ruta, metadata={'Title': 'T4: Especificación de histograma',
                                  'Author': 'Isaac Pérez Pérez'}) as pdf:
        figura = pagina('T4: Especificación de histograma', 1)
        columna(figura, [
            ('Objetivo', 'Implementar la especificación de histograma desde cero y analizar cómo cambia la distribución de intensidades y la apariencia de una imagen. Se comparan escala de grises y procesamiento independiente de los canales B, G y R.'),
            ('¿En qué consiste?', 'Se transforma una imagen fuente para aproximar la distribución de intensidades de una referencia. La correspondencia se calcula a partir de las funciones de distribución acumulada (CDF). La técnica modifica los valores de los píxeles, sin cambiar sus posiciones [1].'),
            ('Histograma y CDF', 'Para un nivel k entre 0 y 255, h(k) cuenta los píxeles que tienen ese valor. Si N es el número de píxeles, p(k) = h(k)/N. La CDF es F(k) = suma de p(i), para i desde 0 hasta k. Es creciente en sentido no estricto y termina en 1.')
        ], 0.055)
        columna(figura, [
            ('Correspondencia discreta utilizada', 'T(k) = mínimo j tal que F_ref(j) >= F_fuente(k).\nLa salida en una posición (x, y) se calcula como I_salida(x, y) = T(I_fuente(x, y)). Se construye una tabla de 256 valores y se aplica mediante indexación de NumPy.'),
            ('Decisiones de implementación', 'Se usa la inversa generalizada discreta con el primer nivel que alcanza la probabilidad fuente. La búsqueda es np.searchsorted(..., side="left") [3]. No se interpola ni se usa una función que resuelva el emparejamiento completo. Los canales se procesan con el mismo criterio.'),
            ('Límite del método', 'Con imágenes discretas, muchos píxeles de igual intensidad reciben un único valor. Su masa no se puede dividir entre varios niveles mediante esta tabla. Por eso no se garantiza un histograma idéntico, ni control exacto de la iluminación o del significado visual.')
        ], 0.535)
        guardar(pdf, figura)

        figura = pagina('Diseño de los experimentos', 2)
        columna(figura, [
            ('Imágenes y casos', '1. Cohete como fuente y café como referencia.\n2. Astronauta como fuente y gato como referencia.\n3. Café como fuente y cohete como referencia.\n4. Astronauta y referencia bimodal controlada.\nLas fotografías se conservan sin recortar ni redimensionar. Sus tamaños pueden ser distintos porque se comparan frecuencias relativas, no píxeles correspondientes.'),
            ('Referencia bimodal', 'Se generan 65 536 valores con semilla 2026: la mitad alrededor de 48 y la otra mitad alrededor de 204, con desviación 8. Se redondean, limitan a [20, 76] y [176, 232], y mezclan. Los tres canales reciben los mismos valores. La imagen es sintética y se usa como control, no como fotografía.'),
            ('Comparación justa', 'Cada par se evalúa en BGR independiente y en gris. Para gris se convierten primero tanto la fuente como la referencia con OpenCV. No se compara convertir después del procesamiento BGR: esas operaciones no son equivalentes.')
        ], 0.055)
        columna(figura, [
            ('Medidas descriptivas', 'W1 normalizada = suma de |F_salida(k) - F_ref(k)|, para k de 0 a 254, dividida entre 255. Su rango es [0, 1]. KS = máximo de esa diferencia absoluta. Un valor menor indica mayor cercanía de distribuciones. Se guardan antes y después en metricas.csv. KS se usa como distancia, sin prueba de hipótesis.'),
            ('Verificación del código', 'Pasaron 10 pruebas unitarias: conteos y CDF, identidad, mapeo conocido, referencia constante, fuente constante, monotonía y comparación con búsqueda exhaustiva, tamaños distintos, canales independientes, entradas inválidas y control bimodal/ecualización.'),
            ('Ejecución y procedencia', 'Python 3.12.14, NumPy 2.3.5, OpenCV 5.0.0 y Matplotlib 3.10.8. No se necesita GPU. Las fotos proceden de los datos públicos de scikit-image [4]; no se instala ni se importa esa biblioteca. El código del proyecto utiliza solo las tres bibliotecas permitidas y módulos estándar de Python.')
        ], 0.535)
        guardar(pdf, figura)

        notas = {
            '01_cohete_cafe': {
                'bgr': 'La escena adquiere una dominante cálida: el cielo cambia de azul a naranja. Los histogramas se aproximan a la referencia, aunque aparecen niveles vacíos y picos por el mapeo discreto.',
                'gris': 'Se mantiene la disposición del cohete y las torres, pero cambia su contraste. Al eliminar el color se estudia una sola distribución de brillo.'},
            '02_astronauta_gato': {
                'bgr': 'El retrato adopta tonos más apagados y cálidos. Los negros de la fuente concentran muchos píxeles en un solo nivel de salida; no se pueden repartir para copiar exactamente el histograma del gato.',
                'gris': 'El rostro sigue siendo reconocible, pero el contraste y los tonos oscuros cambian. La CDF de salida conserva un salto apreciable debido a los píxeles que compartían una intensidad fuente.'},
            '03_cafe_cohete': {
                'bgr': 'El café adquiere una dominante azulada y se comprime su rango tonal. Invertir fuente y referencia produce otro resultado; el proceso no es simétrico ni necesariamente reversible.',
                'gris': 'El resultado concentra intensidades en la zona oscura, como la referencia del cohete. El cambio de histograma no crea los objetos ni la iluminación física de la escena de referencia.'},
            '04_astronauta_bimodal': {
                'bgr': 'Surgen dos grupos tonales por canal y colores artificiales. Aunque la referencia tiene B = G = R, las tablas de los canales fuente son distintas, por lo que la salida no tiene que ser gris.',
                'gris': 'La distribución se divide en dos bandas separadas. Se reconoce el retrato, pero se pierde gradación tonal. La masa de píxeles negros de la fuente genera un pico y evita copiar exactamente la referencia.'}
        }
        numero = 3
        for caso in casos:
            nombre = caso['nombre']
            for modo in ['bgr', 'gris']:
                imagen = plt.imread(RAIZ / f'resultados/{nombre}_{modo}_comparacion.png')
                figura = plt.figure(figsize=(11.69, 8.27), facecolor='white')
                eje = figura.add_axes([0.025, 0.13, 0.95, 0.85])
                eje.imshow(imagen)
                eje.axis('off')
                texto = '\n'.join(textwrap.wrap(notas[nombre][modo], width=150))
                figura.text(0.055, 0.105, texto, va='top', fontsize=10, linespacing=1.4)
                figura.text(0.055, 0.025, 'Cada columna usa el mismo eje de intensidades; histogramas normalizados. B: azul, G: verde, R: rojo.', fontsize=8, color='#555555')
                figura.text(0.95, 0.025, str(numero), ha='right', fontsize=9)
                guardar(pdf, figura)
                numero += 1

        figura = pagina('Resultados y respuestas', numero)
        tabla_datos = []
        for caso in casos:
            for modo in ['bgr', 'gris']:
                seleccion = [f for f in filas if f['caso'] == caso['nombre'] and f['modo'] == modo]
                antes = np.mean([float(f['w1_antes']) for f in seleccion])
                despues = np.mean([float(f['w1_despues']) for f in seleccion])
                tabla_datos.append([caso['nombre'][:2], modo.upper(), f'{antes:.5f}', f'{despues:.5f}'])
        eje = figura.add_axes([0.055, 0.56, 0.43, 0.27])
        eje.axis('off')
        tabla = eje.table(cellText=tabla_datos, colLabels=['Caso', 'Modo', 'W1 antes', 'W1 después'], loc='center', cellLoc='center')
        tabla.auto_set_font_size(False)
        tabla.set_fontsize(10)
        tabla.scale(1, 1.55)
        for (fila, col), celda in tabla.get_celld().items():
            celda.set_edgecolor('#dddddd')
            if fila == 0:
                celda.set_facecolor(AZUL)
                celda.set_text_props(color='white')
        columna(figura, [
            ('Interpretación', 'En BGR la tabla muestra el promedio de los tres canales; en gris, la única distancia. Los 16 canales evaluados redujeron W1. Esto mide ajuste de distribuciones, no calidad perceptual ni conservación semántica. No corresponde calcular RMSE entre fotos de escenas distintas.'),
            ('1. Referencia bimodal y semántica', 'La salida tiende a concentrarse en dos grupos de intensidades. Se conservan las posiciones de los píxeles y pueden reconocerse objetos, pero no se garantiza su significado: colores relevantes, texturas o bordes débiles pueden perderse. El algoritmo no reconoce objetos.')
        ], 0.055, y=0.48)
        columna(figura, [
            ('2. Gris frente a BGR independiente', 'En gris solo se empareja una distribución; no se conserva información de color. En BGR se emparejan tres distribuciones marginales por separado [1]. Esto no obliga a que coincida la distribución conjunta de colores de la referencia. Las relaciones entre canales cambian y pueden aparecer tonos poco naturales, como en el control bimodal.\nAdemás, convertir a gris el resultado BGR no equivale a emparejar imágenes previamente convertidas a gris.'),
            ('3. Relación con la ecualización', 'La ecualización usa la CDF de la fuente para extender las intensidades y aproximarse a una distribución uniforme [2]. La especificación incorpora además la inversa de la CDF deseada. En el caso continuo, una referencia uniforme conduce a la ecualización.\nEn 8 bits no hay garantía de uniformidad exacta. La función ecualizar del proyecto usa round(255 F(k)); no resta CDF_min. Por ello puede diferir de implementaciones como cv2.equalizeHist.'),
            ('Conclusión', 'La especificación permite trasladar distribuciones tonales, pero un mejor ajuste estadístico no garantiza una imagen más natural. La elección de referencia y el procesamiento de color determinan gran parte del resultado.')
        ], 0.535)
        guardar(pdf, figura)

        figura = pagina('Reproducción y bibliografía', numero + 1)
        columna(figura, [
            ('Cómo reproducir', 'Desde la carpeta del proyecto:\npython -m pip install -r requirements.txt\npython -m unittest discover -s tests -v\npython main.py\npython generar_reporte.py\nLas fotografías ya están incluidas. La ejecución no descarga archivos. main.py genera las salidas PNG, las comparaciones y metricas.csv; generar_reporte.py usa esos archivos para crear este PDF.'),
            ('Archivos y licencias', 'datos/fuentes.csv registra procedencia y atribución. datos/manifest.json contiene hashes SHA-256 de las cinco entradas. Astronauta: NASA, dominio público; café: Rachel Michetti, CC0; gato: Stefan van der Walt, CC0; cohete: SpaceX, dominio público, según el catálogo consultado [4].'),
            ('Alcance de la evaluación', 'Los resultados corresponden a cuatro casos seleccionados y no prueban que el algoritmo mejore toda imagen. La conservación semántica se discutió visualmente, sin un experimento de clasificación ni una medida automática de reconocimiento.')
        ], 0.055)
        columna(figura, [
            ('Referencias (formato IEEE)', '[1] scikit-image contributors, "Histogram matching," scikit-image 0.22.0 documentation. [En línea]. Disponible: https://scikit-image.org/docs/0.22.x/auto_examples/color_exposure/plot_histogram_matching.html. [Consultado: 31-oct-2026].\n[2] A. Huamán, "Histogram Equalization," OpenCV 4.11.0 documentation. [En línea]. Disponible: https://docs.opencv.org/4.11.0/d4/d1b/tutorial_histogram_equalization.html. [Consultado: 31-oct-2026].\n[3] NumPy developers, "numpy.searchsorted," NumPy documentation. [En línea]. Disponible: https://numpy.org/doc/stable/reference/generated/numpy.searchsorted.html. [Consultado: 31-oct-2026].\n[4] scikit-image contributors, "skimage/data/_fetchers.py," scikit-image, versión v0.19.3, GitHub. [En línea]. Disponible: https://github.com/scikit-image/scikit-image/blob/v0.19.3/skimage/data/_fetchers.py. [Consultado: 31-oct-2026].')
        ], 0.535, ancho=65)
        guardar(pdf, figura)
    print(f'Reporte generado: {ruta}')


if __name__ == '__main__':
    main()
