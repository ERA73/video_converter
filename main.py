import os
import re
import time
import signal
import subprocess
from tkinter import Tk, Button, Label, Listbox, StringVar, OptionMenu, filedialog, messagebox, Checkbutton, Toplevel, ttk
from threading import Thread
import queue
import shutil

class FileConverter:
    def __init__(self, master):
        self.master = master
        master.title("Video/Audio Converter")

        self.file_list_label = Label(master, text="Archivos Seleccionados:")
        self.file_list_label.grid(row=0, column=0, columnspan=5, pady=10)

        self.file_listbox = Listbox(master, selectmode="extended", height=5)
        self.file_listbox.grid(row=1, column=0, columnspan=4, pady=10)

        self.browse_button = Button(master, text="Browser", command=self.browse_files)
        self.browse_button.grid(row=1, column=4, pady=10)

        self.format_label = Label(master, text="Formato de Salida:")
        self.format_label.grid(row=2, column=0, pady=10)

        self.output_format = StringVar()
        self.output_format.set("MP3")

        self.format_menu = OptionMenu(master, self.output_format, "MP3", "MP4")
        self.format_menu.grid(row=2, column=1, pady=10)

        self.nvenc_var = StringVar()
        self.nvenc_checkbutton = Checkbutton(master, text="Usar NVENC", variable=self.nvenc_var, onvalue="yes", offvalue="no")
        self.nvenc_checkbutton.grid(row=2, column=2, pady=10)

        self.start_button = Button(master, text="Iniciar Conversión", command=self.start_conversion)
        self.start_button.grid(row=2, column=3, pady=10)

        self.cancel_button = Button(master, text="Cancelar", command=self.cancel_conversion)
        self.cancel_button.grid(row=2, column=4, pady=10)
        self.cancelled = False

        self.process = []

        # Ventana emergente para mostrar el progreso
        self.progress_window = Toplevel(self.master)
        self.progress_window.title("Progreso de Conversión")

        self.progress_label = Label(self.progress_window, text="Progreso de Conversión:")
        self.progress_label.grid(row=0, column=0, pady=5)

        self.progress_bars = {}

        # Queue para comunicar el progreso entre hilos
        self.progress_queue = queue.Queue()

    def browse_files(self):
        file_paths = filedialog.askopenfilenames(title="Seleccionar archivos", filetypes=[("Archivos de video y audio", "*.mp4;*.avi;*.mkv;*.mp3")])
        self.file_listbox.delete(0, "end")

        for file_path in file_paths:
            self.file_listbox.insert("end", file_path)

    def start_conversion(self):
        if not self.file_listbox.get(0):
            messagebox.showwarning("Advertencia", "Selecciona al menos un archivo.")
            return

        self.cancelled = False
        output_format = self.output_format.get()
        use_nvenc = self.nvenc_var.get()

        for file_path in self.file_listbox.get(0, "end"):
            output_name = self.generate_output_name(file_path, output_format)
            output_path = os.path.join(os.path.dirname(file_path), output_name)

            thread = Thread(target=self.convert_file, args=(file_path, output_path, output_format, use_nvenc))
            thread.start()

    def convert_file(self, input_path, output_path, output_format, use_nvenc):
        try:
            total_frames = self.get_total_frames(input_path)
            processed_frames = 0
            estimated_duration = self.get_estimated_duration(input_path)
            flags = [
                "-v", "quiet", 
                "-progress", "pipe:0", 
                "-stats",
            ]
            if output_format == "MP3":
                ffmpeg_cmd = ["ffmpeg", "-i", input_path, "-vn", "-acodec", "libmp3lame", *flags, output_path]
            elif output_format == "MP4":
                if use_nvenc == "yes" and shutil.which("ffmpeg-nvenc"):
                    ffmpeg_cmd = ["ffmpeg", "-i", input_path, "-c:v", "h264_nvenc", "-c:a", "aac", *flags, output_path]
                else:
                    ffmpeg_cmd = ["ffmpeg", "-i", input_path, "-c:v", "libx264", "-c:a", "aac", *flags, output_path]

            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                text=True,
                shell=False
            )

            # Crear una etiqueta para mostrar el nombre del archivo
            filename_label = Label(self.progress_window, text=os.path.basename(input_path))
            filename_label.grid(row=len(self.progress_bars)+1, column=0, pady=5, sticky="w")

            # Crear una barra de progreso para este archivo
            self.progress_bars[input_path] = ttk.Progressbar(self.progress_window, length=300, mode="determinate")
            self.progress_bars[input_path].grid(row=len(self.progress_bars), column=1, pady=5)

            while True:
                line = process.stdout.readline()
                if 'frame=' in line:
                    match = re.search(r'frame=\s*(\d+)', line)
                    if match:
                        processed_frames = int(match.group(1))
                        progress = (processed_frames / total_frames) * 100
                        self.progress_bars[input_path]["value"] = progress
                        self.progress_window.update()
                else:
                    match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                    if match:
                        try:
                            current_time = match.group(1)[:8]
                            elapsed_time = time.strptime(current_time, "%H:%M:%S")
                            elapsed_time = elapsed_time.tm_hour * 3600 + elapsed_time.tm_min * 60 + elapsed_time.tm_sec
                            progress = (elapsed_time / estimated_duration) * 100
                            self.progress_bars[input_path]["value"] = progress
                            self.progress_window.update()
                        except Exception as e:
                            print(f"Error en el manejo del tiempo: {e}")

                if not line:
                    break

            process.communicate()

            # Informar que la conversión ha terminado
            self.progress_queue.put((input_path, 100))
            print(f"File: {output_path} is Ready!!!")

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error en la conversión del archivo {input_path}: {e.output}")
            # Informar que la conversión ha fallado
            self.progress_queue.put((input_path, -1))
            # Eliminar la barra de progreso y la etiqueta correspondientes a este archivo
            self.progress_bars[input_path].destroy()
            del self.progress_bars[input_path]
            filename_label.destroy()

    def check_progress(self):
        while True:
            if self.cancelled or all(not thread.is_alive() for thread in self.process):
                break

            time.sleep(0.5)

        # Eliminar todas las barras de progreso restantes
        for progress_bar in self.progress_bars.values():
            progress_bar.destroy()

        self.progress_bars.clear()

        # Mostrar mensajes finales
        while not self.progress_queue.empty():
            input_path, progress = self.progress_queue.get()
            if progress == 100:
                messagebox.showinfo("Información", f"Conversión del archivo {input_path} completada.")
            elif progress == -1:
                messagebox.showerror("Error", f"Error en la conversión del archivo {input_path}.")

    def cancel_conversion(self):
        self.cancelled = True
        for process in self.process:
            os.kill(process.pid, signal.SIGTERM)
        
        # Esperar a que todos los hilos finalicen antes de cerrar la ventana de progreso
        for thread in self.process:
            thread.join()

        self.progress_window.destroy()
        messagebox.showinfo("Información", "Proceso de conversión cancelado.")

    def get_total_frames(self, input_file):
        ffprobe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=nb_frames',
            '-of', 'default=nokey=1:noprint_wrappers=1',
            input_file
        ]

        result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, universal_newlines=True)
        total_frames = int(result.stdout.strip())
        return total_frames
    
    def get_audio_duration(self, audio_file):
        ffprobe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_file
        ]

        result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, universal_newlines=True)
        duration = float(result.stdout.strip())
        return duration
    
    def get_estimated_duration(self, input_audio):
        ffprobe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_audio
        ]

        result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, universal_newlines=True)
        duration = float(result.stdout.strip())
        return duration

    def generate_output_name(self, input_path, output_format):
        base_name, _ = os.path.splitext(os.path.basename(input_path))
        output_name = f"{base_name}.{output_format.lower()}"
        counter = 1

        while os.path.exists(os.path.join(os.path.dirname(input_path), output_name)):
            output_name = f"{base_name}_{counter}.{output_format.lower()}"
            counter += 1

        return output_name


if __name__ == "__main__":
    root = Tk()
    app = FileConverter(root)
    root.mainloop()
