import os
import zipfile
import tkinter as tk
from tkinter import filedialog, ttk
from pdf2image import convert_from_bytes
from PIL import Image
from datetime import datetime
from tqdm import tqdm
import shutil

def crop_and_save(image, output_folder, pdf_filename, page_number):
    # Определение координат области для обрезки изображения
    width, height = image.size
    left, top, right, bottom = 0, 0, width * 0.5, height * 0.5
    cropped_image = image.crop((left, top, right, bottom))

    # Создание папки для сохранения обрезанных изображений
    os.makedirs(output_folder, exist_ok=True)
    output_folder_cache = os.path.join(output_folder, "cache")
    os.makedirs(output_folder_cache, exist_ok=True)

    # Сохранение обрезанного изображения в формате JPEG
    image_path = os.path.join(output_folder_cache, f"{pdf_filename}_page_{page_number}.jpg")
    cropped_image.save(image_path, "JPEG")
    return image_path

def convert_pdf_to_jpg(pdf_data, output_folder, pdf_filename, progress_bar, action_label):
    # Конвертация PDF-файла в изображения
    images = convert_from_bytes(pdf_data)

    # Создание выходной папки
    os.makedirs(output_folder, exist_ok=True)

    total_pages = len(images)
    progress_bar["maximum"] = total_pages

    # Обработка каждого изображения
    for i, image in enumerate(images, start=1):
        image_path = crop_and_save(image, output_folder, pdf_filename, i)
        progress_bar["value"] = i
        action_label.config(text=f"Конвертация страницы {i} из {total_pages} ({image_path})")
        app.update_idletasks()

    # Завершение конвертации - скрытие ProgressBar и отображение завершающей надписи
    progress_bar.pack_forget()
    action_label.config(text="Задача выполнена, Босс")

def merge_images(output_folder, progress_bar, action_label):
    # Объединение обрезанных изображений в одно большое изображение
    cache_folder = os.path.join(output_folder, "cache")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    final_folder = os.path.join(output_folder, f"final_{timestamp}")
    os.makedirs(final_folder, exist_ok=True)

    files = os.listdir(cache_folder)
    images = [f for f in files if f.lower().endswith((".jpg", ".png", ".bmp"))]

    if not images:
        return

    images.sort()

    # Расчет размеров сетки для объединения изображений
    grid_cols = 3
    grid_rows = 3
    images_per_grid = grid_cols * grid_rows

    # Обработка изображений по сетке
    for idx in tqdm(range(0, len(images), images_per_grid), desc="Объединение изображений", unit=" изображений"):
        grid_images = images[idx:idx + images_per_grid]

        # Расчет размера объединенного изображения
        merged_width = 827 * grid_cols
        merged_height = 1170 * grid_rows

        # Создание пустого изображения для вставки изображений
        merged_image = Image.new("RGB", (merged_width, merged_height), (255, 255, 255))

        # Вставка каждого изображения в пустое изображение
        for i, img_name in enumerate(grid_images):
            col = i % grid_cols
            row = i // grid_cols
            x_offset = col * 827
            y_offset = row * 1170

            img_path = os.path.join(cache_folder, img_name)
            img = Image.open(img_path)
            img = img.resize((827, 1170))
            merged_image.paste(img, (x_offset, y_offset))

        # Сохранение объединенного изображения в папке "final"
        merged_image.save(os.path.join(final_folder, f"merged_result_{idx // images_per_grid + 1}.jpg"))

    # Удаление папки "cache" после объединения изображений
    shutil.rmtree(cache_folder)

def process_pdf_archive(archive_file, output_folder, progress_bar, action_label):
    # Обработка архива с PDF-файлами
    with zipfile.ZipFile(archive_file, 'r') as zip_file:
        for file_info in zip_file.infolist():
            if file_info.filename.endswith(".pdf"):
                pdf_data = zip_file.read(file_info)
                pdf_filename = file_info.filename.replace(".pdf", "")
                convert_pdf_to_jpg(pdf_data, output_folder, pdf_filename, progress_bar, action_label)

        # Объединение изображений после конвертации PDF-файлов
        merge_images(output_folder, progress_bar, action_label)

def browse_archive():
    # Открытие диалогового окна для выбора архива и папки назначения
    archive_file = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
    if archive_file:
        output_folder = filedialog.askdirectory()
        if output_folder:
            # Создание ProgressBar и Label для отображения прогресса
            progress_bar = ttk.Progressbar(app, length=200, mode="determinate")
            progress_bar.pack(pady=10)
            action_label = tk.Label(app, text="")
            action_label.pack()
            # Обработка архива с PDF-файлами
            process_pdf_archive(archive_file, output_folder, progress_bar, action_label)

app = tk.Tk()
app.title("PDF to JPG Converter for PDF Archives")
app.geometry("500x500")

watermark_label = tk.Label(app, text="𝒜𝓁𝒻𝒶", font=("Arial", 24))
watermark_label.pack()

browse_button = tk.Button(app, text="Выбрать архив с PDF-файлами", command=browse_archive)
browse_button.pack(pady=10)

result_label = tk.Label(app, text="")
result_label.pack(pady=10)

bottom_label = tk.Label(app, text="Сделано для Akeso с любовью")
bottom_label.pack(side="bottom")

app.mainloop()
