import os
import zipfile
import tkinter as tk
from tkinter import filedialog, ttk
from pdf2image import convert_from_bytes
from PIL import Image
from datetime import datetime
from tqdm import tqdm
import shutil

class PDFConverterApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PDF to JPG Converter for PDF Archives")
        self.master.geometry("400x350")

        # Добавленный код для установки прозрачности окна
        self.set_transparency(0.95)

        self.grid_cols_label = tk.Label(self.master, text="Столбцы:")
        self.grid_cols_label.pack()

        self.grid_cols_scale = tk.Scale(self.master, from_=3, to=6, orient=tk.HORIZONTAL, length=200, command=self.sync_sliders)
        self.grid_cols_scale.set(3)  # Установите значение по умолчанию
        self.grid_cols_scale.pack()

        self.grid_rows_label = tk.Label(self.master, text="Строки:")
        self.grid_rows_label.pack()

        self.grid_rows_scale = tk.Scale(self.master, from_=3, to=6, orient=tk.HORIZONTAL, length=200, command=self.sync_sliders)
        self.grid_rows_scale.set(3)  # Установите значение по умолчанию
        self.grid_rows_scale.pack()

        self.watermark_label = tk.Label(self.master, text="𝒜𝓁𝒻𝒶", font=("Arial", 24))
        self.watermark_label.pack()

        self.browse_button = tk.Button(self.master, text="Выбрать архив с PDF-файлами", command=self.browse_archive)
        self.browse_button.pack(pady=10)

        self.result_label = tk.Label(self.master, text="")
        self.result_label.pack(pady=10)

        self.bottom_label = tk.Label(self.master, text="Сделано для Akeso с любовью")
        self.bottom_label.pack(side="bottom")

    def set_transparency(self, alpha):
        # Установка прозрачности для окна
        self.master.attributes('-alpha', alpha)

    def sync_sliders(self, *args):
        # Синхронизация значений слайдеров в реальном времени
        cols_value = self.grid_cols_scale.get()
        rows_value = self.grid_rows_scale.get()
        
        if cols_value != rows_value:
            self.grid_rows_scale.set(cols_value)
        self.master.update_idletasks()

    def browse_archive(self):
        grid_cols = self.grid_cols_scale.get()
        grid_rows = self.grid_rows_scale.get()

        # Остальной код для обработки архива с использованием grid_cols и grid_rows
        self.process_pdf_archive(grid_cols, grid_rows)

    def crop_and_save(self, image, output_folder, pdf_filename, page_number):
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

    def convert_pdf_to_jpg(self, pdf_data, output_folder, pdf_filename, progress_bar, action_label, grid_cols, grid_rows):
        # Конвертация PDF-файла в изображения
        images = convert_from_bytes(pdf_data)

        # Создание выходной папки
        os.makedirs(output_folder, exist_ok=True)

        total_pages = len(images)
        progress_bar["maximum"] = total_pages

        # Обработка каждого изображения
        for i, image in enumerate(images, start=1):
            image_path = self.crop_and_save(image, output_folder, pdf_filename, i)
            progress_bar["value"] = i
            action_label.config(text=f"Конвертация страницы {i} из {total_pages} ({image_path})")
            self.master.update_idletasks()

        # Завершение конвертации - скрытие ProgressBar и отображение завершающей надписи
        progress_bar.pack_forget()
        action_label.config(text="Задача выполнена, Босс")

    def merge_images(self, output_folder, progress_bar, action_label, grid_cols, grid_rows):
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

    def process_pdf_archive(self, grid_cols, grid_rows):
        # Открытие диалогового окна для выбора архива и папки назначения
        archive_file = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if archive_file:
            output_folder = filedialog.askdirectory()
            if output_folder:
                # Создание ProgressBar и Label для отображения прогресса
                progress_bar = ttk.Progressbar(self.master, length=200, mode="determinate")
                progress_bar.pack(pady=10)
                action_label = tk.Label(self.master, text="")
                action_label.pack()
                # Обработка архива с PDF-файлами
                with zipfile.ZipFile(archive_file, 'r') as zip_file:
                    for file_info in zip_file.infolist():
                        if file_info.filename.endswith(".pdf"):
                            pdf_data = zip_file.read(file_info)
                            pdf_filename = file_info.filename.replace(".pdf", "")
                            self.convert_pdf_to_jpg(pdf_data, output_folder, pdf_filename, progress_bar, action_label, grid_cols, grid_rows)

                    # Объединение изображений после конвертации PDF-файлов
                    self.merge_images(output_folder, progress_bar, action_label, grid_cols, grid_rows)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFConverterApp(root)
    root.mainloop()
