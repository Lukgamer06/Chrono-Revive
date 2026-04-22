# Media Organizer

Una aplicación para organizar y mejorar archivos multimedia (fotos y videos).

## Características

- **Reparar archivos corruptos**: Usa FFmpeg y ImageMagick para reparar imágenes y videos dañados.
- **Organizar por fecha**: Organiza los archivos en carpetas por año y mes basándose en metadatos EXIF o de video.
- **Mejorar calidad**: Utiliza Real-ESRGAN para mejorar la calidad de imágenes y videos.
- **Interfaz gráfica**: Fácil de usar con una interfaz intuitiva.

## Instalación

1. Descarga el instalador: `Installer.exe` desde la sección de releases.
2. Ejecuta `Installer.exe` (puede requerir permisos de administrador).
3. El instalador descargará automáticamente las herramientas necesarias y creará un acceso directo en el escritorio.

## Uso

1. Abre la aplicación desde el acceso directo en el escritorio.
2. Selecciona la carpeta de origen (donde están los archivos multimedia).
3. Opcionalmente, elige una carpeta de destino.
4. Selecciona el tipo de orden (solo año o año y mes).
5. Elige qué pasos ejecutar: reparar, organizar, mejorar.
6. Haz clic en "Iniciar proceso" y espera a que termine.

## Requisitos

- Windows 10 o superior
- Conexión a internet para la instalación inicial (descarga de herramientas)

## Desarrollo

Para contribuir o modificar:

1. Clona el repositorio.
2. Instala dependencias: `pip install -r requirements.txt`
3. Ejecuta `python app.py` para probar la app.
4. Para generar el instalador: `python Installer.py` (requiere PyInstaller y otras dependencias).

## Licencia

Este proyecto es de código abierto. Consulta el archivo LICENSE para más detalles.