# Contexto para el rediseño del frontend

## Fuentes

- Chat del proyecto: «Identificar Moises.ai» (`01a161d8-908a-75d2-9b0b-d7da67aaefe9`), consultado el 22 de octubre de 2026.
- Prototipo solicitado: https://www.figma.com/proto/LEsBCCWofVKIux1FylFRmJ?node-id=0-1&t=vqVLCW4ifh5o6hs2-6
- Base del repositorio: `develop`, commit `8452399`, versión 0.4.0.
- Rama de trabajo: `codex/frontend-figma-refactor`.

## Producto y comportamiento que se debe conservar

Separador Vocal es una aplicación de escritorio Windows en Python y PySide6. El rediseño se implementará en la interfaz Qt existente. El procesamiento de audio y los proyectos permanecen locales.

El usuario confirmó en el chat anterior que el pitch y las funciones existentes funcionaban correctamente. Después pidió exactamente cinco stems: voz principal, coros, batería, bajo e instrumental. La versión 0.4.0 incorporó esas cinco pistas y fue integrada en `develop` mediante el PR #5.

El rediseño debe conservar:

- Importación WAV, MP3, FLAC y M4A, mediante diálogo y arrastrar y soltar.
- Separación en segundo plano, progreso, errores y resultados parciales.
- Cinco carriles con formas de onda y cursor sincronizados.
- Reproducción, pausa, búsqueda, volumen individual, mute y solo en tiempo real.
- Pitch de -12 a +12 semitonos, conservando tempo y archivos originales.
- Exportación local en segundo plano y configuración de la carpeta de proyectos.
- Confirmación existente para descargar modelos y manejo del cierre durante tareas activas.

## Superficie actual

- `src/vocal_splitter/ui/main_window.py`: ventana, importación, estado de procesamiento y coordinación de workers.
- `src/vocal_splitter/ui/audio_workbench.py`: carriles, formas de onda, transporte, mezcla, pitch y exportación.
- `src/vocal_splitter/ui/settings_dialog.py`: configuración local.

## Flujo Git

Trabajar en ramas desde `develop`, con commits atómicos por responsabilidad. Separar extracciones de estructura de cambios visuales y de cambios de comportamiento. Verificar cada paso antes de confirmar el commit. La integración se dirige a `develop`; el usuario reserva la integración en `main`.

## Estado de la referencia visual

El enlace de Figma muestra «¿Desea consultar este archivo? Regístrese o Inicie sesión» en el navegador. No se han podido inspeccionar los dashboards, sus interacciones, colores, tipografías ni recursos. Por ello este documento no atribuye al prototipo decisiones visuales no observadas.

Antes de implementar la réplica se necesita acceso al archivo mediante una sesión autorizada de Figma, un enlace consultable o una exportación de las pantallas. Tras obtenerlo, registrar el inventario de pantallas y estados, tokens visuales, correspondencia con los controles Qt y criterios de comparación visual. Adaptar las funciones de la referencia al producto local sin añadir servicios ficticios.

## Secuencia de implementación

1. Completar el inventario visual del prototipo y su correspondencia con las funciones existentes.
2. Separar estilos y componentes compartidos de la coordinación de tareas, con pruebas de caracterización donde hagan falta.
3. Implementar la navegación y cada pantalla observada en cambios independientes.
4. Comprobar estados vacíos, carga, error y resultado; accesibilidad por teclado y tamaños de ventana admitidos.
5. Ejecutar las pruebas y revisar capturas de la interfaz contra las pantallas de referencia antes de integrar.
