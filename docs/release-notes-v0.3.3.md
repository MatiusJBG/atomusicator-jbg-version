# Separador Vocal 0.3.3

## Correcciones

- Resuelve el enlace simbólico `WinGet\Links\ffmpeg.exe` y configura el `PATH` con la carpeta real del ejecutable antes de importar el motor. Esto evita que el error de Windows 448 se confunda con un problema de escritura.
- Ejecuta `ffmpeg -version` como comprobación previa y muestra un error específico si Windows no puede abrir el binario.
- Guarda sesiones y resultados por defecto en `%LOCALAPPDATA%\Separador Vocal\Separador Vocal\projects`; los archivos permanecen en el equipo y Documentos/OneDrive no se usa como destino predeterminado.
- Detecta preferencias guardadas con una ruta inválida/no escribible, vuelve a AppData local y registra el motivo para evitar repetir el fallo al importar o separar.
- El instalador mantiene como destino predeterminado Archivos de programa, requiere elevación y bloquea la raíz de cualquier unidad como destino.

## Verificación

- 11 pruebas unitarias para resolución de enlaces WinGet, precedencia del `PATH`, ejecución real de FFmpeg, escritura local, migración de una ruta guardada inválida, rechazo de destinos no locales/raíz y configuración de permisos/destino del instalador.
- Smoke test del ejecutable empaquetado: autodiagnóstico local, ejecución real de FFmpeg e inicio de la ventana Qt.
- Prueba manual de separación de dos etapas sobre un fragmento local de 12 segundos: generó los tres stems dentro de AppData local.

## Actualización

Cierra Separador Vocal e instala `SeparadorVocal-Setup.exe` desde [Releases](https://github.com/MatiusJBG/atomusicator-jbg-version/releases). Los proyectos guardados bajo Documentos en versiones anteriores no se borran; abre esa carpeta desde el Explorador si necesitas conservarlos o exportar sus stems.
