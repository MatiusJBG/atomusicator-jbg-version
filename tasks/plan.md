# Plan técnico: `audio-ingest`

## Alcance

Implementar la importación local de audio para la aplicación de escritorio Windows, según [SPEC-audio-ingest.md](../SPEC-audio-ingest.md). Este plan no incluye los modelos de separación ni la reproducción de audio.

## Componentes y dependencias

| Componente | Responsabilidad | Depende de |
|---|---|---|
| Dominio `AudioAsset` | Representar origen, duración, canales, frecuencia y tamaño con validaciones independientes de la interfaz. | — |
| Lector de audio | Detectar formato y obtener metadatos mediante bibliotecas locales; producir errores de formato/decodificación explícitos. | Dominio |
| Servicio de importación | Validar el archivo, preparar una sesión segura y mantener una referencia al original sin alterarlo. | Dominio, lector |
| UI de importación | Diálogo de archivo, zona de arrastre, resumen del audio y presentación de errores. | Servicio |
| Configuración de proyectos | Resolver la ruta inicial configurable `Documentos\Separador Vocal` y crear carpetas de sesión. | Servicio |

## Secuencia propuesta

1. Crear el esqueleto Python/PySide6 y la estructura `src/vocal_splitter`.
2. Definir el tipo de dominio `AudioAsset` y los errores esperados de importación.
3. Implementar lectura y validación de WAV, MP3, FLAC y M4A; mantener el decodificador detrás de una interfaz para poder sustituirlo.
4. Implementar creación de sesión y almacenamiento de metadatos, conservando el original como solo lectura.
5. Integrar diálogo y arrastrar/soltar con trabajo fuera del hilo de UI, estados de carga y mensajes recuperables.
6. Añadir configuración editable para ubicación de proyectos y una primera ejecución con la carpeta predeterminada.

## Riesgos y decisiones

- **Decodificación M4A:** puede requerir FFmpeg según el códec; detectar la ausencia del decodificador y explicar cómo resolverla.
- **Interfaz bloqueada:** lectura de archivos grandes debe ejecutarse fuera del hilo UI; el diseño debe permitir cancelación y descartar resultados tardíos.
- **Archivos dañados o extensiones falsas:** validar el contenido decodificable, no solo la extensión.
- **Espacio de disco:** la importación no debe duplicar innecesariamente el archivo original; inicialmente la sesión mantendrá su ruta y guardará resultados en una carpeta derivada.
- **Carpeta por defecto:** usar `Documentos\Separador Vocal`, configurable desde la aplicación; si la ruta no puede crearse, pedir una ubicación válida.

## Puntos de revisión

- La validación del dominio no importa módulos Qt.
- Los cuatro formatos aceptados se reconocen y sus metadatos quedan normalizados.
- La UI permanece receptiva durante la lectura y muestra estados/error de forma recuperable.
- La sesión queda enlazada al archivo fuente original, que no se modifica.

## Fuera de alcance en esta iteración

- Separación lead/coros, efectos, stems instrumentales, pitch, mezcla y exportación.
- Descarga de música por URL, cuentas, nube o telemetría.
- Instalador de producción y empaquetado final; se resolverán después de validar el flujo local.
