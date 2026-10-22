# Especificación: `vocal-separation`

## Objetivo

Procesar una mezcla de audio local y crear tres pistas WAV sincronizadas: **Voz principal**, **Coros** y **Acompañamiento**. El objetivo prioritario es que la pista de voz principal quede lo más limpia posible, permitiendo escucharla por separado en el siguiente módulo.

La función debe presentarse como separación asistida por IA, con resultados que pueden contener filtraciones. No prometerá aislamiento perfecto.

## Supuestos de esta especificación

1. Se implementará para Windows en Python 3.11–3.13 y el procesamiento seguirá ocurriendo localmente.
2. El primer enfoque será un flujo en dos etapas: (a) separar voz de acompañamiento; (b) volver a procesar la pista vocal para estimar voz líder y coros.
3. Se usará un adaptador sobre `python-audio-separator` para poder sustituir modelos sin acoplar el resto de la aplicación al motor.
4. El código de la biblioteca declara licencia MIT, pero los pesos de cada modelo pueden tener condiciones propias. No se incluirán ni descargarán pesos hasta registrar su origen y licencia.
5. La primera salida de separación será WAV PCM; formatos comprimidos y más herramientas se especificarán en módulos posteriores.

## Límite del módulo

Incluye ejecución de la separación, progreso y error de los trabajos, archivos de resultado con duración alineada y el estado que consumirá el reproductor. No incluye mixer, pitch shifting, limpieza con EQ, transcripción ni mastering.

## Stack y modelos candidatos

- Python 3.11–3.13, PySide6 y `python-audio-separator`.
- Motor intercambiable, con modos CPU y aceleración local cuando el entorno disponible lo permita.
- Primera etapa: un modelo público de separación voz/instrumental compatible con el adaptador.
- Segunda etapa: un modelo público UVR de tipo Karaoke aplicado solo al stem de voces. En la interfaz, su salida de voz se etiquetará como **Voz principal** y la salida residual como **Coros**.
- El modelo preciso se fijará después de comprobar rendimiento, resultados auditivos y licencia de sus pesos. Los pesos se almacenarán en la caché local y no en el repositorio.

La biblioteca documenta varios modelos públicos, separación en etapas y presets de voz/karaoke. Una discusión del repositorio de UVR describe volver a procesar el stem vocal con un modelo Karaoke para obtener voz líder y un residuo que contiene coros; esa referencia es una estrategia comunitaria, no una garantía del modelo.

## Comandos

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install "audio-separator"
python -m vocal_splitter
```

El pin exacto y las opciones de instalación del motor/modelos se establecerán tras validar compatibilidad con Python 3.13 y el hardware disponible.

## Estructura prevista

```text
src/vocal_splitter/
  application/separate_vocals.py       # Caso de uso y estados del trabajo
  domain/separation_job.py             # Estados y progreso
  domain/stem.py                       # Metadatos de cada pista generada
  infrastructure/separation/
    audio_separator_engine.py          # Adaptador del motor
    model_profile.py                   # Configuración y capacidades de modelos
    model_license_manifest.json        # Origen, licencia y suma de comprobación
  ui/separation_worker.py              # Ejecución fuera del hilo UI
```

Los nombres de archivo de salida serán `voz_principal.wav`, `coros.wav` y `acompanamiento.wav`. Intermedios, si se conservan para diagnóstico, quedarán bajo `processing/` dentro de la sesión.

## Flujo de trabajo

1. Recibir la sesión local creada por `audio-ingest`.
2. Comprobar que hay espacio temporal suficiente y que el motor/modelo está disponible; informar y solicitar descarga si es la primera ejecución.
3. Separar voz total y acompañamiento.
4. Procesar de nuevo la voz total para estimar voz líder y coros.
5. Validar que las pistas de salida se escribieron, pueden decodificarse y conservan el inicio y la duración de la canción.
6. Guardar resultados en la carpeta de sesión y devolverlos como stems al siguiente módulo.

## Estados y errores

- Estados visibles: `Preparando`, `Descargando modelo`, `Separando voz`, `Separando coros`, `Finalizando`, `Listo`, `Error`.
- Los errores de descarga, memoria insuficiente, audio no decodificable y archivo de modelo incompatible se mostrarán con una acción posible.
- El fallo de la segunda etapa conservará la voz total y el acompañamiento de la primera etapa; no se presentará una pista parcial como resultado final lead/coros.
- Cerrar la ventana no debe dejar un hilo Python ejecutándose en segundo plano sin indicarlo.

## Estrategia de calidad

- Comparar auditivamente los tres resultados en mezclas con voz solista, armonías, doblaje, duetos y coros densos, usando audio propio o con licencia permisiva.
- Preservar el offset temporal y la duración para que las pistas coincidan al reproducirse juntas.
- Mostrar una nota breve: las voces superpuestas o de timbre similar pueden mezclarse entre **Voz principal** y **Coros**; la persona debe escuchar el resultado antes de usarlo como pista final.
- La separación y el filtrado de artefactos no deben borrar consonantes o colas vocales a fin de perseguir una pista artificialmente silenciosa.

## Estilo de código

- El modelo de dominio usa términos propios del producto (`LeadVocal`, `BackingVocals`, `Instrumental`), no nombres internos de la biblioteca.
- El servicio de aplicación depende de una interfaz de separación, no del paquete concreto.
- El adaptador registra modelo, versión, parámetros, tiempo y rutas en la sesión.
- Los archivos se escriben a nombres temporales y solo se publican como salida final después de validar ambas etapas.

```python
class VocalSeparator(Protocol):
    def separate(self, source: Path, output_dir: Path) -> SeparationResult: ...
```

## Estrategia de verificación

- Importar una mezcla de referencia con autorización/licencia y revisar que se generen las tres pistas.
- Reproducir las pistas juntas en el siguiente módulo y confirmar que no hay desplazamiento temporal perceptible.
- Escuchar cada stem por separado en una selección de casos: voz solista, voz doblada, armonías y dueto.
- Interrumpir una descarga o provocar falta de espacio y confirmar mensajes recuperables y archivos parciales no publicados como resultados válidos.
- No usar pruebas automáticas con audio propietario; documentar los resultados auditivos de las muestras autorizadas.

## Límites

- Siempre: procesar solo el archivo que la persona importó; mantener audio y resultados en el equipo; conservar intacta la fuente; distinguir voz líder de coros con etiquetas claras; atribuir bibliotecas y modelos según sus licencias.
- Consultar primero: enviar audio a servicios remotos, entrenar o ajustar pesos con grabaciones de usuarios, incluir modelos o redistribuirlos dentro de un instalador.
- Nunca: copiar código, pesos, marcas o recursos privados de Moises.ai; afirmar que la separación lead/coros será perfecta; cambiar o sobrescribir el archivo fuente.

## Criterios de aceptación

- Una sesión válida genera tres archivos WAV: voz principal estimada, coros/residuo vocal y acompañamiento.
- Los tres stems empiezan en el mismo punto y tienen duración compatible con la mezcla original.
- La UI muestra estados diferenciados para cada etapa y un error recuperable si el proceso falla.
- Si la segunda etapa falla, la app conserva los resultados de primera etapa identificados como separación vocal/instrumental, sin etiquetarlos como lead/coros.
- Los modelos utilizados aparecen registrados en el manifiesto local con fuente y licencia revisadas.

## Preguntas abiertas

- Flujo de dos etapas y etiquetas **Voz principal**, **Coros** y **Acompañamiento**: aprobados por la persona usuaria.
- Validación inicial: empezar con pistas de licencia permisiva; revisar las condiciones de cada grabación antes de descargarla o usarla.

## Fuentes técnicas

- [python-audio-separator: modelos, API, aceleración y licencia](https://github.com/nomadkaraoke/python-audio-separator)
- [UVR: discusión sobre separación de voz líder y coros](https://github.com/Anjok07/ultimatevocalremovergui/discussions/1250)
- [Sanidha: audio multipista y licencia CC BY 4.0](https://ccml.gtcmt.gatech.edu/data/Sanidha/)
- [MUSDB18: composición de fuentes, licencias y acceso académico](https://sigsep.github.io/datasets/musdb.html)
