# T4: Especificación de histograma

## Objetivo

Implementar desde cero la especificación de histograma y comprender su efecto en la distribución de intensidades y el aspecto visual de una imagen. Se trabaja con imágenes a color, una fuente y una referencia, con características tonales diferentes.

## Entrega

1. Código en Python.
2. Reporte PDF con:
   - Investigación del proceso.
   - Comparación fuente, referencia y resultado lado a lado, validada con distintas imágenes.
   - Histogramas y CDF de las tres imágenes.
   - Respuestas: efecto de una referencia bimodal y conservación semántica; gris frente a BGR independiente y colores extraños; relación con ecualización clásica.
   - Bibliografía en formato IEEE.

Solo se permiten OpenCV, NumPy, Matplotlib y la biblioteca estándar de Python. Se pide evitar comprimir la entrega; si resulta necesario comprimir el código, el reporte debe quedar fuera del archivo comprimido.

## Criterios concretos de este trabajo

- Tres pares fotográficos y un control bimodal; la consigna no fija un número mínimo de pares.
- Mismo algoritmo y configuración para todos los pares.
- Comparación BGR/gris, histogramas normalizados y CDF.
- Tratamiento explícito de entradas constantes, empates, tamaños diferentes y cuantización.
- Diez pruebas unitarias y métricas de distribución como comprobación complementaria.
- El PDF utiliza Matplotlib, sin añadir una biblioteca externa para documentos.
