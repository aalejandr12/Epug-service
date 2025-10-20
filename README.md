# epug  Convertidor CBR a EPUB (portada desde primera página)

Este repositorio contiene epug.py, un script en Python que convierte archivos .cbr a .epub. 
Toma todas las páginas del CBR y, en el EPUB final, usa la primera como portada y la elimina del interior.

## Requisitos
- Windows con [7-Zip](https://www.7-zip.org/) instalado.
  - Ajusta la constante SEVEN_ZIP al inicio del script si tu 7z.exe está en otra ruta.
- Python 3.10+ (recomendado 3.11+)
- Paquetes Python:
  - Pillow
  - ebooklib
  - 
atsort

Puedes instalarlos con:

`powershell
python -m pip install -r requirements.txt
`

## Uso
1) Coloca tus archivos .cbr dentro de una carpeta.
2) Ejecuta el script indicando la carpeta, o déjalo que te la pida:

`powershell
# Indicando carpeta explícita
python .\epug.py "C:\ruta\a\mi\carpeta"

# O sin argumentos y pega la ruta cuando te la solicite
python .\epug.py
`

El script creará en la misma carpeta un EPUB "final" por cada CBR encontrado. 
Opcionalmente también puede crear un EPUB "base" (con todas las páginas sin separar portada) si activas KEEP_BASE = True en el script.

## Notas
- Formatos de imagen soportados: .jpg/.jpeg, .png, .webp.
- Asegúrate de tener espacio suficiente en disco: se usan carpetas temporales al extraer y generar EPUBs.
- Errores comunes:
  - 7-Zip no encontrado: edita SEVEN_ZIP en epug.py con la ruta correcta a 7z.exe.
  - Sin imágenes dentro del CBR: revisa el archivo o su compresión.

## Estructura
`
Kimetsu-20251019T041319Z-1-001/
 epug.py          # Script principal
 requirements.txt # Dependencias Python
 README.md        # Este archivo
 Kimetsu/         # (si existe) Carpeta con recursos/archivos del usuario
`

## Licencia
MIT
