# Especificación: `export-library`

## Objetivo

Guardar copias utilizables de los stems procesados en una ubicación que el usuario elige.

## Comportamiento

- El botón **Exportar stems** exporta todos los stems que aparecen en el mezclador, incluidos los renders de pitch actuales.
- La persona elige una carpeta; la app crea una subcarpeta única `Separador Vocal - fecha-hora`.
- Escribe nombres descriptivos como `voz_principal.wav`, `coros.wav` y `acompanamiento.wav`.
- La copia corre en un worker Qt. Cada archivo se copia primero como temporal y se renombra al terminar. Si ocurre un error, la carpeta parcial creada por ese trabajo se elimina.
- El audio fuente y las salidas de sesión no se modifican.

## Límites

- Exporta WAV sin pérdida; elección de formato/profundidad y render de mezcla se dejan para otra versión.
- Comprueba espacio libre aproximado antes de copiar, pero el espacio puede cambiar durante la exportación.
