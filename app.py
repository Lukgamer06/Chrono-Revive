import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import sys
import cv2
from PIL import Image, ImageFile
from concurrent.futures import ProcessPoolExecutor
import subprocess
import shutil
from datetime import datetime
from PIL import Image, ExifTags
import tempfile
from tqdm import tqdm

# Habilitar carga de imágenes truncadas para mayor robustez
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Extensiones de archivos soportados
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']

# Rutas para herramientas (ajustar para bundle)
def get_tool_path(tool_name):
    if hasattr(sys, '_MEIPASS'):
        # Ejecutando desde bundle
        base_dir = sys._MEIPASS
    else:
        # Ejecutando desde script
        base_dir = os.path.dirname(__file__)
    
    if tool_name == 'realesrgan':
        return os.path.join(base_dir, 'tools', 'realesrgan-ncnn-vulkan.exe')
    elif tool_name == 'ffmpeg':
        return os.path.join(base_dir, 'tools', 'ffmpeg.exe')
    elif tool_name == 'ffprobe':
        return os.path.join(base_dir, 'tools', 'ffprobe.exe')
    elif tool_name == 'magick':
        return os.path.join(base_dir, 'tools', 'magick.exe')
    return None

REALESRGAN = get_tool_path('realesrgan')

EXTS_IMG = {".jpg", ".jpeg", ".png", ".heic", ".bmp", ".gif"}
EXTS_VID = {".mp4", ".mov", ".avi", ".mkv", ".wmv"}
EXTS = EXTS_IMG | EXTS_VID

LOG_FILE = "errores_mejora.txt"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Bienvenido")
        self.root.geometry("600x500")
        # Mejorar escalado para pantallas de alta resolución
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        self.root.tk.call('tk', 'scaling', 2.0)  # Ajustar escalado

        # Variables
        self.origen_var = tk.StringVar()
        self.destino_var = tk.StringVar()
        self.orden_var = tk.StringVar(value="anio_mes")
        self.arreglar_var = tk.BooleanVar(value=True)
        self.organizar_var = tk.BooleanVar(value=True)
        self.mejorar_var = tk.BooleanVar(value=True)

        # Widgets
        tk.Label(root, text="Seleccionar carpeta de origen:", font=("Arial", 10)).pack(pady=5)
        frame_origen = tk.Frame(root)
        frame_origen.pack()
        tk.Entry(frame_origen, textvariable=self.origen_var, width=50, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_origen, text="Buscar", command=self.select_origen, font=("Arial", 10)).pack(side=tk.LEFT)

        tk.Label(root, text="Carpeta de destino (opcional):", font=("Arial", 10)).pack(pady=5)
        frame_destino = tk.Frame(root)
        frame_destino.pack()
        tk.Entry(frame_destino, textvariable=self.destino_var, width=50, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_destino, text="Buscar", command=self.select_destino, font=("Arial", 10)).pack(side=tk.LEFT)

        tk.Label(root, text="Tipo de orden:", font=("Arial", 10)).pack(pady=5)
        frame_orden = tk.Frame(root)
        frame_orden.pack()
        tk.Radiobutton(frame_orden, text="Solo por año", variable=self.orden_var, value="anio", font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_orden, text="Año y mes", variable=self.orden_var, value="anio_mes", font=("Arial", 10)).pack(side=tk.LEFT)

        tk.Label(root, text="Seleccionar pasos a ejecutar:", font=("Arial", 10)).pack(pady=10)
        frame_pasos = tk.Frame(root)
        frame_pasos.pack()
        tk.Checkbutton(frame_pasos, text="Arreglar archivos", variable=self.arreglar_var, font=("Arial", 10)).pack(anchor=tk.W)
        tk.Checkbutton(frame_pasos, text="Organizar por fecha", variable=self.organizar_var, font=("Arial", 10)).pack(anchor=tk.W)
        tk.Checkbutton(frame_pasos, text="Mejorar calidad", variable=self.mejorar_var, font=("Arial", 10)).pack(anchor=tk.W)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=10)

        self.status_label = tk.Label(root, text="", font=("Arial", 10))
        self.status_label.pack()

        tk.Button(root, text="Iniciar proceso", command=self.start_process, font=("Arial", 10)).pack(pady=10)

    def select_origen(self):
        folder = filedialog.askdirectory()
        if folder:
            self.origen_var.set(folder)

    def select_destino(self):
        folder = filedialog.askdirectory()
        if folder:
            self.destino_var.set(folder)

    def start_process(self):
        origen = self.origen_var.get()
        destino = self.destino_var.get() or os.path.join(os.path.dirname(origen), "Resultado")
        orden = self.orden_var.get()
        arreglar = self.arreglar_var.get()
        organizar = self.organizar_var.get()
        mejorar = self.mejorar_var.get()

        if not origen:
            messagebox.showerror("Error", "Selecciona la carpeta de origen")
            return

        if not (arreglar or organizar or mejorar):
            messagebox.showerror("Error", "Selecciona al menos un paso a ejecutar")
            return

        self.progress['value'] = 0
        self.status_label.config(text="Iniciando...")

        # Ejecutar en hilo separado para no bloquear GUI
        import threading
        threading.Thread(target=self.run_process, args=(origen, destino, orden, arreglar, organizar, mejorar)).start()

    def run_process(self, origen, destino, orden, arreglar, organizar, mejorar):
        try:
            pasos = [arreglar, organizar, mejorar]
            num_pasos = sum(pasos)
            progreso_paso = 100 / num_pasos if num_pasos > 0 else 100
            current_progress = 0

            current_dir = origen

            if arreglar:
                self.status_label.config(text="Arreglando...")
                repaired_dir = self.repair_files(current_dir)
                current_dir = repaired_dir
                current_progress += progreso_paso
                self.progress['value'] = current_progress

            if organizar:
                self.status_label.config(text="Organizandolos...")
                fecha_dir = self.organize_files(current_dir, orden)
                current_dir = fecha_dir
                current_progress += progreso_paso
                self.progress['value'] = current_progress

            if mejorar:
                self.status_label.config(text="Mejorando la calidad...")
                final_dir = self.enhance_files(current_dir, destino)
                current_dir = final_dir
                current_progress += progreso_paso
                self.progress['value'] = current_progress

            self.progress['value'] = 100
            self.status_label.config(text=f"Completado. Carpeta final: {current_dir}")
            messagebox.showinfo("Completado", f"El proceso ha terminado. La carpeta final está en:\n{current_dir}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def repair_files(self, folder_path):
        repaired_dir = os.path.join(folder_path, "Reparados")
        os.makedirs(repaired_dir, exist_ok=True)

        images = []
        videos = []
        for root, dirs, files in os.walk(folder_path):
            if "Reparados" in dirs:
                dirs.remove("Reparados")
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    images.append(file_path)
                elif ext in VIDEO_EXTENSIONS:
                    videos.append(file_path)

        total = len(images) + len(videos)
        current = 0

        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(repair_image, img, repaired_dir) for img in images]
            for future in futures:
                future.result()
                current += 1
                # Progreso interno del paso, pero no actualizar global aquí

            futures = [executor.submit(repair_video, vid, repaired_dir) for vid in videos]
            for future in futures:
                future.result()
                current += 1
                # Progreso interno

        return repaired_dir

    def organize_files(self, origen, orden):
        destino = os.path.join(os.path.dirname(origen), "Fecha")
        os.makedirs(destino, exist_ok=True)

        files = []
        for raiz, _, archivos in os.walk(origen):
            for archivo in archivos:
                ext = os.path.splitext(archivo.lower())[1]
                if ext not in EXTS:
                    continue
                ruta = os.path.join(raiz, archivo)
                fecha = get_best_date(ruta)
                files.append((ruta, fecha, archivo))

        for ruta, fecha, archivo in files:
            anio = str(fecha.year)
            if orden == "anio_mes":
                mes = f"{fecha.year}-{fecha.month:02d}"
                folder = os.path.join(destino, anio, mes)
            else:
                folder = os.path.join(destino, anio)

            os.makedirs(folder, exist_ok=True)
            destino_final = os.path.join(folder, archivo)
            if os.path.exists(destino_final):
                base, ext = os.path.splitext(archivo)
                destino_final = os.path.join(folder, f"{base}_dup{ext}")
            shutil.move(ruta, destino_final)

        return destino

    def enhance_files(self, input_folder, output_folder):
        os.makedirs(output_folder, exist_ok=True)

        tasks = []
        for root, _, files in os.walk(input_folder):
            for f in files:
                ext = "." + f.lower().split(".")[-1]
                input_path = os.path.join(root, f)
                relative = os.path.relpath(input_path, input_folder)
                output_path = os.path.join(output_folder, relative)
                base, ext2 = os.path.splitext(output_path)
                output_path = base + "_mejorado" + ext2

                if ext in EXTS_IMG:
                    tasks.append(("img", input_path, output_path))
                elif ext in EXTS_VID:
                    tasks.append(("video", input_path, output_path))

        for ttype, input_path, output_path in tasks:
            if ttype == "img":
                process_image(input_path, output_path)
            else:
                process_video(input_path, output_path)

        return output_folder

# Funciones auxiliares (copiadas del notebook)

def check_ffmpeg():
    ffmpeg_path = get_tool_path('ffmpeg')
    if ffmpeg_path and os.path.exists(ffmpeg_path):
        try:
            result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    return False

def check_imagemagick():
    magick_path = get_tool_path('magick')
    if magick_path and os.path.exists(magick_path):
        try:
            result = subprocess.run([magick_path, '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    return False

def repair_image(file_path, output_dir):
    output_path = os.path.join(output_dir, os.path.basename(file_path))
    try:
        with Image.open(file_path) as img:
            img.save(output_path, quality=95)
    except:
        if check_imagemagick():
            cmd = [get_tool_path('magick'), 'convert', file_path, output_path]
            subprocess.run(cmd)

def repair_video(file_path, output_dir):
    output_path = os.path.join(output_dir, os.path.basename(file_path))
    if check_ffmpeg():
        cmd = [get_tool_path('ffmpeg'), '-i', file_path, '-c', 'copy', '-y', output_path]
        subprocess.run(cmd)

def get_exif_date(path):
    try:
        img = Image.open(path)
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                name = ExifTags.TAGS.get(tag, tag)
                if name in ("DateTimeOriginal", "DateTimeDigitized"):
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except:
        pass
    return None

def get_video_date_ffmpeg(path):
    try:
        cmd = [get_tool_path('ffprobe'), "-v", "quiet", "-print_format", "json", "-show_entries", "format_tags=creation_time", path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        import json
        data = json.loads(result.stdout)
        ts = data.get("format", {}).get("tags", {}).get("creation_time")
        if ts:
            ts = ts.replace("Z", "+00:00")
            return datetime.fromisoformat(ts)
    except:
        pass
    return None

def get_file_date(path):
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts)

def get_best_date(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in EXTS_IMG:
        d = get_exif_date(path)
        if d:
            return d
    if ext in EXTS_VID:
        d = get_video_date_ffmpeg(path)
        if d:
            return d
    return get_file_date(path)

def is_thumbnail(path, min_size=500):
    img = cv2.imread(path)
    if img is None:
        return True
    h, w = img.shape[:2]
    return w < min_size or h < min_size

def enhance_with_retries(input_path, output_path, retries=3):
    for attempt in range(retries):
        try:
            cmd = [REALESRGAN, "-i", input_path, "-o", output_path, "-n", "realesrgan-x4plus", "-s", "4"]
            subprocess.run(cmd)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                return True
        except:
            pass
    return False

def process_image(input_path, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if is_thumbnail(input_path):
        os.remove(input_path)
        return
    if not enhance_with_retries(input_path, output_path):
        shutil.copy2(input_path, output_path)

def process_video(input_path, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    temp_dir = tempfile.mkdtemp()
    frames_dir = os.path.join(temp_dir, "frames")
    enhanced_dir = os.path.join(temp_dir, "enhanced")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(enhanced_dir, exist_ok=True)

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(os.path.join(frames_dir, f"{i:06d}.png"), frame)

    cap.release()

    frame_files = sorted(os.listdir(frames_dir))
    for f in frame_files:
        inp = os.path.join(frames_dir, f)
        out = os.path.join(enhanced_dir, f)
        enhance_with_retries(inp, out)

    first_frame = cv2.imread(os.path.join(enhanced_dir, frame_files[0]))
    h, w = first_frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    for f in frame_files:
        frame = cv2.imread(os.path.join(enhanced_dir, f))
        video_out.write(frame)

    video_out.release()
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()