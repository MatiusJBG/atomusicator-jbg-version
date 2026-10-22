# Separador Vocal 0.3.1

Esta versión corrige el arranque de la aplicación de Windows cuando otras herramientas instalan sus propias DLL de Python o del runtime de C++.

## Correcciones

- El runtime de PyInstaller fija las carpetas DLL incluidas con Qt/PySide6 y carga por ruta absoluta las bibliotecas C++ que necesita Qt.
- El empaquetado ignora las carpetas de runtime externas del entorno de compilación y fija copias compatibles de `MSVCP140.dll` y `VCRUNTIME140.dll`.
- Se evita que componentes de MySQL, Java u otras aplicaciones sustituyan dependencias de Qt en tiempo de arranque.

## Instalación

Desinstala cualquier versión anterior desde **Configuración → Aplicaciones → Aplicaciones instaladas**, cierra otras ventanas de Separador Vocal y ejecuta `SeparadorVocal-Setup.exe`. El primer arranque puede tardar unos segundos mientras Windows extrae los componentes locales.
