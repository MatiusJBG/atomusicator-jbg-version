# Especificación: `audio-ingest`

## Objetivo

Permitir que una persona importe una mezcla de audio local a la aplicación de escritorio para iniciar después la separación de voz principal, coros y acompañamiento. La importación debe validar el archivo, mostrar su información básica y preparar una sesión de trabajo sin modificar el original.

## Supuestos de esta especificación

1. La primera plataforma será Windows de escritorio y todo el procesamiento de audio ocurrirá en el equipo.
2. La aplicación requiere Python 3.11 o superior, hasta Python 3.13, y PySide6; los controles de audio/IA se ejecutarán fuera del hilo de la interfaz. El entorno disponible aquí trae Python 3.13.7, que usaré para la ejecución local.
3. La primera entrega importará archivos locales WAV, MP3, FLAC y M4A. No descargará canciones desde URL.
4. El archivo original permanecerá intacto. La aplicación guardará proyectos y resultados en una carpeta elegida por el usuario o en la carpeta de proyectos de la aplicación.
5. Las separaciones dependerán de modelos descargables de terceros y de la memoria/capacidad del equipo; este módulo solo prepara y valida entradas.

## Límite del módulo

Incluye selección por diálogo, arrastrar y soltar, validación, lectura de duración/canales/frecuencia y creación de una sesión. No incluye separación, reproducción, edición de pitch ni exportación final.

## Stack propuesto

- Python 3.11–3.13
- PySide6 para la interfaz nativa de escritorio
- `mutagen` para lectura local de metadatos; el motor de separación se encargará de decodificar muestras y podrá usar FFmpeg cuando sea necesario para M4A
- `pytest` para pruebas unitarias; `pytest-qt` para interacciones de interfaz
- Gestión de dependencias mediante `pyproject.toml`

## Comandos

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m vocal_splitter
```

## Estructura prevista del proyecto

```text
src/vocal_splitter/
  __main__.py                 # Arranque de escritorio
  application/import_audio.py # Flujo de importación
  domain/audio_asset.py       # Metadatos y reglas del audio importado
  infrastructure/audio/       # Lectura de formatos/metadatos
  ui/main_window.py           # Ventana, diálogo y zona de arrastre
tests/
  unit/
  ui/
```

## Requisitos funcionales

1. La persona puede elegir un archivo mediante el diálogo de Windows o arrastrarlo a la ventana.
2. La aplicación acepta WAV, MP3, FLAC y M4A y rechaza extensiones o datos no decodificables con un mensaje comprensible.
3. La aplicación muestra nombre, duración, frecuencia de muestreo, cantidad de canales y tamaño del archivo antes de iniciar la separación.
4. La importación crea una sesión con identificador y rutas separadas para el original y los resultados derivados.
5. La validación y lectura de metadatos no bloquean la interfaz.
6. Si falta un decodificador opcional o hay un error de lectura, se explica qué ocurrió y se permite volver a elegir el archivo.

## Estilo de código

- `snake_case` para módulos, funciones y variables; `PascalCase` para tipos.
- Las reglas de dominio no dependerán de PySide6.
- Los errores esperados se representarán como resultados tipados o excepciones específicas, no como `except Exception` silenciosos.
- Ejemplo:

```python
@dataclass(frozen=True)
class AudioAsset:
    source_path: Path
    duration_seconds: float
    sample_rate_hz: int
    channels: int
```

## Estrategia de verificación

- Pruebas unitarias de extensiones, archivos dañados, metadatos, rutas de proyecto y preservación del original.
- Pruebas de interfaz para importar por diálogo/arrastre, mostrar metadatos y recuperar errores sin congelar la ventana.
- Archivos de audio de prueba pequeños, sintéticos o con licencia permisiva.

## Límites

- Siempre: conservar intacto el archivo fuente; validar antes de pasar audio a los módulos posteriores; mantener la interfaz receptiva.
- Consultar primero: cambiar la plataforma objetivo, enviar audio a un servicio externo, añadir cuentas/sincronización o guardar proyectos fuera del equipo.
- Nunca: descargar audio desde enlaces no autorizados; incluir modelos o medios sin revisar sus licencias; guardar datos de usuario fuera de las ubicaciones elegidas.

## Criterios de aceptación

- Un WAV, MP3, FLAC o M4A válido se importa y presenta metadatos correctos.
- Un archivo inválido o no compatible no bloquea ni cierra la aplicación y produce un mensaje útil.
- Tras importar, se crea una sesión de trabajo y el original sigue sin cambios.
- La interfaz responde mientras se valida un archivo.

## Preguntas abiertas

- ¿Te parece bien usar Python 3.11 y PySide6 para la aplicación de escritorio?
- ¿Quieres guardar los proyectos en una carpeta elegida por ti o usar una carpeta fija dentro de Documentos?
