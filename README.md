# Separador Vocal

Aplicación de escritorio para Windows que crea una estimación de voz principal, coros/residuo vocal y acompañamiento a partir de una mezcla. Incluye reproducción sincronizada de stems, controles de mezcla y transposición de pitch que conserva el tempo.

La interfaz se inspira en flujos comunes de estaciones de audio. Separador Vocal es un proyecto independiente y no usa código, marca ni servicios privados de Moises.ai. El procesamiento se ejecuta localmente.

## Funciones

- Importa WAV, MP3, FLAC y M4A desde el diálogo o arrastrando el archivo.
- Conserva el audio fuente en su ubicación y crea una sesión local con resultados y metadatos.
- Separa voz total y acompañamiento, y vuelve a procesar la voz para estimar voz principal y coros.
- Muestra formas de onda sincronizadas y una línea de reproducción común.
- Reproduce y pausa las pistas, permite buscar en la canción y ajustar el volumen de cada stem.
- Los botones **M** (Mute) y **S** (Solo) cambian la mezcla durante la reproducción.
- Cambia el pitch entre -12 y +12 semitonos con Rubber Band de FFmpeg. El tempo no se modifica y los WAV originales se conservan.
- Exporta copias WAV de los stems actuales a una carpeta elegida; la copia se realiza en segundo plano.
- Escribe el registro de los modelos y sus parámetros en la sesión.

La separación de voces es una estimación: doblajes, armonías, reverb y voces de timbre parecido pueden filtrarse entre voz principal y coros. La app no promete aislamiento perfecto.

Esta versión ofrece voz principal, coros/residuo vocal y acompañamiento. No genera todavía batería, bajo y otros como stems separados: el modelo de cuatro stems seleccionado debe tener condiciones de uso de sus pesos compatibles con el instalador y la distribución del proyecto.

## Instalación para uso

Descarga `SeparadorVocal-Setup.exe` desde la sección **Releases** del repositorio. El instalador no incluye modelos ni audio del usuario. Al abrir la app, instala los componentes de inferencia según los pasos de la sección siguiente.

Requisitos:

- Windows 10/11 de 64 bits.
- FFmpeg disponible en `PATH` para separación y cambio de pitch. Para cambio de pitch, la compilación debe incluir el filtro `rubberband`.
- Conexión a Internet solo para la descarga inicial de los modelos habilitados; luego el modelo se reutiliza desde la caché local.
- Memoria y espacio en disco suficientes para cargar y procesar la duración completa. El audio se conserva en el equipo.

## Ejecución desde el código

Necesitas Python 3.11, 3.12 o 3.13 de 64 bits y FFmpeg. En PowerShell, desde la carpeta del repositorio:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[desktop,separation-cpu]"
python -m vocal_splitter
```

Si PowerShell impide activar el entorno, ejecuta los comandos directamente con `\.venv\Scripts\python.exe`.

## Flujo de trabajo

1. Pulsa **Importar audio** o arrastra un archivo a la ventana.
2. Pulsa **Separar voz y coros**. La primera vez la app pide permiso para descargar los modelos indicados; se guardan en la caché de usuario y se valida su SHA-256.
3. Cuando termina, usa **▶ Reproducir**. Las pistas comparten la misma posición; pulsa sobre cualquier forma de onda para buscar.
4. Ajusta cada deslizador o pulsa **M** para silenciar y **S** para escuchar solo esa pista.
5. Elige de -12 a +12 semitonos y pulsa **Aplicar pitch**. El render se hace en segundo plano, mantiene el tempo y genera archivos derivados dentro de la sesión.

Las sesiones se crean bajo `Documentos\Separador Vocal` por defecto. Cambia la carpeta desde **Archivo → Carpeta de proyectos…**. Los resultados se guardan en la carpeta de sesión, dentro de `outputs`.

## Problemas frecuentes

### `No se encontró FFmpeg`

Instala FFmpeg y reinicia Separador Vocal. Comprueba `ffmpeg -version` en una nueva ventana de PowerShell y que `where.exe ffmpeg` devuelva una ruta.

### El cambio de pitch indica que falta `rubberband`

La app detecta el filtro antes de renderizar. Instala una distribución de FFmpeg que incluya Rubber Band. Los stems sin procesar permanecen disponibles si la compilación no tiene ese filtro.

### No hay dispositivo de salida o no se escucha

Comprueba el dispositivo predeterminado de Windows, que la salida no esté silenciada y que otra aplicación no lo tenga en modo exclusivo. El control de volumen del mezclador se aplica a cada stem.

### La separación se detiene o tarda demasiado

La separación usa CPU y memoria local. Prueba con un fragmento corto, cierra programas pesados y verifica el espacio libre. Los modelos se descargan una vez y se guardan en la caché de la app.

### Algunas voces aparecen en la pista de coros o al revés

El modelo distingue patrones acústicos, no roles musicales. Voces dobladas, coros cercanos, reverberación y armonías densas pueden cruzar entre stems.

## Desarrollo y empaquetado

```powershell
python -m pip install -e ".[desktop,separation-cpu]"
python -m compileall -q src
./packaging/build_windows.ps1
```

El script crea el ejecutable y el instalador en `dist/`. Los artefactos se publican como adjuntos de una Release; no se suben al historial Git.

## Modelos, licencias y privacidad

- El código de `python-audio-separator` está publicado bajo MIT. La licencia del motor no determina por sí sola los derechos de cada peso.
- El README de UVR solicita crédito a UVR, Anjok07 y aufr33 y pide respetar MIT para integrar sus modelos. La procedencia, catálogo y hashes de los dos perfiles se guardan en `src/vocal_splitter/infrastructure/separation/model_license_manifest.json`; no se empaquetan los pesos.
- La app descarga únicamente los perfiles enumerados en su manifiesto y muestra confirmación antes de la primera descarga. Revisa `docs/third-party-notices.md` antes de distribuir una versión o usarla comercialmente.
- Los modelos, FFmpeg y las grabaciones del usuario no forman parte del repositorio ni del instalador. Las canciones permanecen en el equipo; no hay subida a nube ni telemetría.
- El instalador se construyó con Inno Setup. Sus autores solicitan comprar una licencia comercial si el programa se usa en contexto comercial; revisa sus [condiciones actuales](https://jrsoftware.org/isorder.php) antes de una distribución comercial.

## Flujo Git

El desarrollo se integra en `develop`. El trabajo se hace en ramas de funcionalidad y con commits pequeños; `main` queda para que el mantenedor integre `develop` cuando lo decida.

## Licencia

El repositorio contiene código propio y referencias a dependencias de terceros. Consulta sus licencias y atribuciones en [docs/third-party-notices.md](docs/third-party-notices.md) antes de redistribuir.
