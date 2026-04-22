import os
import requests
import zipfile
import subprocess
import shutil
import winshell
from win32com.client import Dispatch

# URLs de descarga
TOOLS = {
    'ffmpeg': {
        'url': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
        'extract': ['ffmpeg.exe', 'ffprobe.exe'],
        'path_in_zip': 'ffmpeg-*-essentials_build/bin/'
    },
    'imagemagick': {
        'url': 'https://imagemagick.org/archive/binaries/ImageMagick-7.1.1-41-Q16-x64-static.zip',
        'extract': ['magick.exe'],
        'path_in_zip': 'ImageMagick-*-Q16-x64-static/'
    },
    'realesrgan': {
        'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip',
        'extract': ['realesrgan-ncnn-vulkan.exe'],
        'path_in_zip': 'realesrgan-ncnn-vulkan-*/'
    }
}

def download_and_extract(tool_name, info):
    print(f"Descargando {tool_name}...")
    response = requests.get(info['url'])
    zip_path = f"{tool_name}.zip"
    with open(zip_path, 'wb') as f:
        f.write(response.content)
    
    print(f"Extrayendo {tool_name}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Encontrar el directorio base
        base_dir = None
        for name in zip_ref.namelist():
            if name.endswith('/'):
                base_dir = name
                break
        if not base_dir:
            print(f"No se encontró directorio base para {tool_name}")
            return
        
        for file in info['extract']:
            source = base_dir + file
            zip_ref.extract(source, 'temp_tools')
            dest = os.path.join('tools', file)
            os.makedirs('tools', exist_ok=True)
            shutil.move(os.path.join('temp_tools', source), dest)
    
    os.remove(zip_path)
    shutil.rmtree('temp_tools', ignore_errors=True)

def create_shortcut(target, shortcut_path):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.save()

def main():
    print("Iniciando instalación...")
    
    # Crear carpeta tools
    os.makedirs('tools', exist_ok=True)
    
    # Descargar y extraer herramientas
    for tool, info in TOOLS.items():
        download_and_extract(tool, info)
    
    print("Herramientas descargadas. Generando aplicación...")
    
    # Ejecutar PyInstaller
    cmd = [
        'pyinstaller',
        '--onedir',
        '--windowed',
        '--add-data', 'tools;tools',
        'app.py'
    ]
    subprocess.run(cmd)
    
    print("Aplicación generada. Instalando...")
    
    # Instalar en Program Files
    install_dir = r"C:\Program Files\USBApp"
    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)
    shutil.copytree('dist/app', install_dir)
    
    # Crear acceso directo en escritorio
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, "USB App.lnk")
    exe_path = os.path.join(install_dir, "app.exe")
    create_shortcut(exe_path, shortcut_path)
    
    print("Instalación completa. Acceso directo creado en el escritorio.")
    print(f"Aplicación instalada en: {install_dir}")

if __name__ == "__main__":
    main()
