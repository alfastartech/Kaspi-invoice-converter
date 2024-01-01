import poppler
import tkinter as tk
from tkinter import filedialog
from pdf2image import convert_from_bytes
from PIL import Image
import zipfile
from tkinter import ttk

def crop_and_save(image, output_folder, pdf_filename, page_number):
    width, height = image.size
    # Определите координаты и размер верхней левой части (например, 50% по ширине и 50% по высоте)
    left = 0
    top = 0
    right = width * 0.5
    bottom = height * 0.5
    cropped_image = image.crop((left, top, right, bottom))
    cropped_image.save(f"{output_folder}/{pdf_filename}_page_{page_number}.jpg", "JPEG")

def convert_pdf_to_jpg(pdf_data, output_folder, pdf_filename, progress_var, action_label):
    images = convert_from_bytes(pdf_data)
    total_pages = len(images)
    for i, image in enumerate(images):
        crop_and_save(image, output_folder, pdf_filename, i + 1)
        progress = (i + 1) / total_pages * 100
        progress_var.set(progress)
        action_label.config(text=f"Конвертация страницы {i + 1} из {total_pages}")

def process_pdf_archive(archive_file, output_folder, progress_var, action_label):
    with zipfile.ZipFile(archive_file, 'r') as zip_file:
        for file_info in zip_file.infolist():
            if file_info.filename.endswith(".pdf"):
                pdf_data = zip_file.read(file_info)
                pdf_filename = file_info.filename.replace(".pdf", "")
                convert_pdf_to_jpg(pdf_data, output_folder, pdf_filename, progress_var, action_label)

def browse_archive():
    archive_file = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
    if archive_file:
        output_folder = filedialog.askdirectory()
        if output_folder:
            progress_var = tk.DoubleVar()
            progress = ttk.Progressbar(app, length=200, mode="determinate", variable=progress_var)
            progress.pack(pady=10)
            action_label = tk.Label(app, text="")
            action_label.pack()
            process_pdf_archive(archive_file, output_folder, progress_var, action_label)
            result_label.config(text="Конвертация завершена")

app = tk.Tk()
app.title("PDF to JPG Converter for PDF Archives")
app.geometry("500x500")

# Добавляем водяной знак
watermark_label = tk.Label(app, text="𝒜𝓁𝒻𝒶", font=("Arial", 24))
watermark_label.pack()

browse_button = tk.Button(app, text="Выбрать архив с PDF-файлами", command=browse_archive)
browse_button.pack(pady=10)

result_label = tk.Label(app, text="")
result_label.pack(pady=10)

# Надпись внизу интерфейса
bottom_label = tk.Label(app, text="Сделано для Akeso с любовью")
bottom_label.pack(side="bottom")

app.mainloop()
