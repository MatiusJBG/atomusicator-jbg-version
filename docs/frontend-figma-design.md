# Implementación del frontend Figma

Referencia inspeccionada el 22 de octubre de 2026 desde el prototipo del usuario:
https://www.figma.com/proto/LEsBCCWofVKIux1FylFRmJ/Untitled?node-id=3-13060

## Pantallas observadas

1. `3:13060`, Separador Vocal · Mezclador DAW: frame de 1440 × 900; navegación lateral de proyectos, mezclador, exportación y configuración. Cabecera con proyecto y acciones. Cinco carriles contiguos con controles a la izquierda, formas de onda a la derecha y regla temporal común. Transporte, pitch y master en la franja inferior.
2. `3:13600`, Separador Vocal · Exportar stems: diálogo centrado sobre el mezclador, tarjetas WAV/FLAC/MP3, frecuencia, profundidad, canales, selección de pistas, normalización, carpeta y acciones.
3. `3:14224`, Pitch · Aplicación en curso: panel con semitonos, formantes, deslizador de -12 a +12, indicador de progreso y aviso de conservación de originales.

## Dirección visual

Fondo observado en el editor: `#0B0F14`. Paleta de implementación basada en la referencia: panel `#131B23`, borde `#29343F`, texto `#E5EDF3`, secundario `#8A9AA8`, acento turquesa `#2DD4BF`. Pistas rosa, violeta, ámbar, azul y verde. Tipografía sans serif de sistema, datos temporales monoespaciados. Alineación izquierda y controles compactos; radios pequeños y divisores entre carriles.

El mezclador es el elemento central. No introducir dashboards comerciales, cuentas, métricas musicales inventadas ni servicios en nube. Mostrar nombre y frecuencia reales del archivo en lugar de los datos de muestra del prototipo. Conservar la ventana nativa de Windows.

## Implementación y aceptación

- Extraer primero el estilo de la ventana sin alterar comportamiento, con pruebas de caracterización de controles.
- Implementar componentes Qt de carril, regla temporal, medidor y panel de pitch; navegación y estados vacíos, procesando, error y resultado.
- Conectar los controles nuevos de panorama y master al mezclador, con límites de pico existentes y pruebas de salida de audio.
- Dar al exportador selección de pistas y opciones reales WAV/FLAC/MP3, frecuencia, profundidad y canales. Trabajo en segundo plano, salida en carpeta nueva y limpieza ante error.
- Mostrar progreso real por pistas completadas al aplicar pitch y permitir conservar formantes mediante Rubber Band. Conservar originales y reproducción sincronizada.
- Comprobar interfaz a 1440 × 900 y al mínimo de ventana, navegación por teclado y prevención de acciones incompatibles durante tareas activas.
- Ejecutar `./.venv/Scripts/python.exe -m unittest discover -s tests -v`, `./.venv/Scripts/python.exe -m compileall -q src` y revisar capturas Qt.

Commits separados para extracción de estilo, corrección de exportación, capacidades de mezcla, exportación/pitch y cada conjunto visual. Integración futura hacia `develop`.
