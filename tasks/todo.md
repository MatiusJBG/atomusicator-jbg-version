# Tareas: `audio-ingest`

- [x] **Tarea 1: Crear la base de la aplicación de escritorio**
  - Aceptación: el paquete `vocal_splitter` inicia una ventana PySide6 vacía y la configuración de desarrollo permite instalar la aplicación.
  - Verificar: construir el wheel y abrir/cerrar la ventana; ambos pasos se completaron en el entorno local.
  - Archivos previstos: `pyproject.toml`, `src/vocal_splitter/__init__.py`, `src/vocal_splitter/__main__.py`, `src/vocal_splitter/ui/main_window.py`.

- [x] **Tarea 2: Definir el modelo de audio y lectura de metadatos**
  - Aceptación: `AudioAsset` representa ruta, duración, frecuencia, canales y tamaño; el lector reconoce WAV, MP3, FLAC y M4A y reporta fallos concretos.
  - Verificar: WAV con metadatos reales se importó manualmente. No había ejemplos MP3/FLAC/M4A disponibles; esos formatos usan Mutagen y quedan pendientes de comprobación con archivos reales.
  - Archivos previstos: `src/vocal_splitter/domain/audio_asset.py`, `src/vocal_splitter/infrastructure/audio/metadata_reader.py`, `src/vocal_splitter/infrastructure/audio/errors.py`.

- [x] **Tarea 3: Implementar el servicio de importación y las sesiones**
  - Aceptación: importa un archivo validado, crea una sesión con metadatos y referencia el original sin modificarlo.
  - Verificar: importación manual creó `session.json`; el tamaño del original coincidió antes y después.
  - Archivos previstos: `src/vocal_splitter/application/import_audio.py`, `src/vocal_splitter/domain/audio_session.py`, `src/vocal_splitter/infrastructure/projects/session_store.py`.

- [x] **Tarea 4: Integrar selección de archivo y arrastrar/soltar**
  - Aceptación: la ventana permite importar desde diálogo o soltar el archivo; muestra nombre, duración y propiedades; lectura larga no congela la ventana.
  - Verificar: el flujo del botón completó en segundo plano, mostró metadatos y restauró el botón. El diálogo y arrastrar/soltar no se ejercitaron manualmente.
  - Archivos previstos: `src/vocal_splitter/ui/main_window.py`, `src/vocal_splitter/ui/import_worker.py`, `src/vocal_splitter/application/import_audio.py`.

- [x] **Tarea 5: Añadir preferencia de ubicación de proyectos y manejo final de errores**
  - Aceptación: la ubicación inicial es `Documentos\\Separador Vocal`, el usuario puede elegir otra carpeta y una ruta inaccesible produce un aviso recuperable.
  - Verificar: la preferencia y el diálogo están implementados; no se ejercitaron manualmente en esta vuelta.
  - Archivos previstos: `src/vocal_splitter/application/project_settings.py`, `src/vocal_splitter/infrastructure/projects/session_store.py`, `src/vocal_splitter/ui/settings_dialog.py`, `src/vocal_splitter/ui/main_window.py`.
