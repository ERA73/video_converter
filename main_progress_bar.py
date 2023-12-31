import os
from tkinter import Tk, Button, Label, Listbox, StringVar, OptionMenu, filedialog, messagebox, Checkbutton
from moviepy.editor import VideoFileClip, AudioFileClip
from threading import Thread

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

        self.progress_label = Label(master, text="")
        self.progress_label.grid(row=3, column=0, columnspan=5, pady=10)

    def browse_files(self):
        file_paths = filedialog.askopenfilenames(title="Seleccionar archivos", filetypes=[("Archivos de video y audio", "*.mp4;*.avi;*.mkv;*.mp3")])
        self.file_listbox.delete(0, "end")

        for file_path in file_paths:
            self.file_listbox.insert("end", file_path)

    def start_conversion(self):
        if not self.file_listbox.get(0):
            messagebox.showwarning("Advertencia", "Selecciona al menos un archivo.")
            return

        output_format = self.output_format.get()
        use_nvenc = self.nvenc_var.get()

        for index, file_path in enumerate(self.file_listbox.get(0, "end")):
            output_name = self.generate_output_name(file_path, output_format)
            output_path = os.path.join(os.path.dirname(file_path), output_name)

            t = Thread(target=self.convert_file, args=(file_path, output_path, output_format, use_nvenc, index, len(self.file_listbox.get(0, "end"))))
            t.start()

    def convert_file(self, input_path, output_path, output_format, use_nvenc, index, total_files):
        try:
            if output_format == "MP3":
                audio_clip = AudioFileClip(input_path)
                audio_clip.write_audiofile(output_path)
            elif output_format == "MP4":
                if use_nvenc == "yes":
                    video_clip = VideoFileClip(input_path, codec="libx264", audio_codec="aac", threads=4)
                else:
                    video_clip = VideoFileClip(input_path, audio_codec="aac", threads=4)
                video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4)
        except Exception as e:
            messagebox.showerror("Error", f"Error en la conversión del archivo {input_path}: {str(e)}")

        progress_percentage = ((index + 1) / total_files) * 100
        self.master.after(0, self.update_progress, index + 1, total_files, progress_percentage)

    def update_progress(self, completed_files, total_files, progress_percentage):
        progress_text = f"Progreso: {completed_files}/{total_files} ({progress_percentage:.2f}%)"
        self.progress_label.config(text=progress_text)

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
