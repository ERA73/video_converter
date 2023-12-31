import os
import re
import time
import signal
import subprocess
from tkinter import Tk, Button, Label, Listbox, StringVar, OptionMenu, filedialog, messagebox, Checkbutton
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

        threads = []

        for file_path in self.file_listbox.get(0, "end"):
            output_name = self.generate_output_name(file_path, output_format)
            output_path = os.path.join(os.path.dirname(file_path), output_name)

            thread = Thread(target=self.convert_file, args=(file_path, output_path, output_format, use_nvenc))
            threads.append(thread)

        # Iniciar los hilos
        for thread in threads:
            thread.start()

        # Crear un hilo separado para verificar el progreso
        progress_thread = Thread(target=self.check_progress, args=(threads,))
        progress_thread.start()

    def convert_file(self, input_path, output_path, output_format, use_nvenc):
        try:
            total_frames = self.get_total_frames(input_path)
            processed_frames = 0
            total_duration = self.get_audio_duration(input_path)
            start_time = time.time()
            estimated_duration = self.get_estimated_duration(input_path)
            flags = [
                "-v", "quiet", 
                # "-v", "warning", 
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
                shell=True
            )

            self.process.append(process)

            while True:
                line = process.stdout.readline()
                if 'frame=' in line:
                    match = re.search(r'frame=\s*(\d+)', line)
                    if match:
                        processed_frames = int(match.group(1))
                        progress = (processed_frames / total_frames) * 100
                        print(f"\r\rProgreso: {progress:.2f}%", end="")
                else:
                    match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                    if match:
                        try:
                            current_time = match.group(1)[:8]
                            elapsed_time = time.strptime(current_time, "%H:%M:%S")  # Convierte el tiempo a una estructura de tiempo
                            elapsed_time = elapsed_time.tm_hour*3600 + elapsed_time.tm_min*60 + elapsed_time.tm_sec
                            progress = (elapsed_time / estimated_duration) * 100
                            print(f"Progreso: {progress:.2f}%")
                        except:
                            print(match)


                    # line = line.replace('\n', '')
                    # print(f"\r\r{line}")
                if not line: break

            process.communicate()

            # Informar que la conversión ha terminado
            self.progress_queue.put((input_path, 100))
            print(f"File: {output_path} is Ready!!!")

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error en la conversión del archivo {input_path}: {e.output}")
            # Informar que la conversión ha fallado
            self.progress_queue.put((input_path, -1))

    def check_progress(self, threads):

        # Mostrar mensajes finales
        while not self.progress_queue.empty():
            input_path, progress = self.progress_queue.get()
            if progress == 100:
                messagebox.showinfo("Información", f"Conversión del archivo {input_path} completada.")
            elif progress == -1:
                messagebox.showerror("Error", f"Error en la conversión del archivo {input_path}.")

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
        print(duration)
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
        print(duration)
        return duration

    def generate_output_name(self, input_path, output_format):
        base_name, _ = os.path.splitext(os.path.basename(input_path))
        output_name = f"{base_name}.{output_format.lower()}"
        counter = 1

        while os.path.exists(os.path.join(os.path.dirname(input_path), output_name)):
            output_name = f"{base_name}_{counter}.{output_format.lower()}"
            counter += 1

        return output_name

    def cancel_conversion(self):
        self.cancelled = True
        for process in self.process:
            os.kill(process.pid, signal.SIGTERM)
        messagebox.showinfo("Información", "Proceso de conversión cancelado.")

if __name__ == "__main__":
    root = Tk()
    app = FileConverter(root)
    root.mainloop()
