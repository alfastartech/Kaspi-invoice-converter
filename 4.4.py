import os
import zipfile
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pdf2image import convert_from_bytes
from PIL import Image
from datetime import datetime
from tqdm import tqdm
import shutil
import PyPDF2
import io

# Функция для проверки условий строки
def check_condition(line):
    if line.startswith(('Akeso', 'Эвалар')) or (line.startswith('3') and not line.endswith('-1\n')):
        return True
    if line.strip().endswith("шт."):
        return True
    return False

class PDFConverterApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Преобразование PDF в JPG для PDF-архивов")
        self.master.geometry("400x400")

        # Добавленный код для установки прозрачности окна
        self.set_transparency(0.75)

        # Установка стиля для окна и его виджетов
        self.master.configure(bg="#333333")  # Задайте цвет фона окна
        self.master.option_add("*Background", "#333333")  # Задайте цвет фона для всех виджетов

        self.grid_cols_label = tk.Label(self.master, text="Столбцы:", bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Label
        self.grid_cols_label.pack()

        self.grid_cols_scale = tk.Scale(self.master, from_=3, to=6, orient=tk.HORIZONTAL, length=200, command=self.sync_sliders, bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Scale
        self.grid_cols_scale.set(3)  # Установите значение по умолчанию
        self.grid_cols_scale.pack()

        self.grid_rows_label = tk.Label(self.master, text="Строки:", bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Label
        self.grid_rows_label.pack()

        self.grid_rows_scale = tk.Scale(self.master, from_=3, to=6, orient=tk.HORIZONTAL, length=200, command=self.sync_sliders, bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Scale
        self.grid_rows_scale.set(3)  # Установите значение по умолчанию
        self.grid_rows_scale.pack()

        self.watermark_label = tk.Label(self.master, text="𝒜𝓁𝒻𝒶", font=("Arial", 24), bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Label
        self.watermark_label.pack()

        self.browse_button = tk.Button(self.master, text="Выбрать архив с PDF-файлами", command=self.browse_archive, bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Button
        self.browse_button.pack(pady=10)

        self.result_label = tk.Label(self.master, text="", bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Label
        self.result_label.pack(pady=10)

        self.bottom_label = tk.Label(self.master, text="Сделано для Akeso с любовью", bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Label
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

    def extract_lines_from_pdf(self, file_path, lines):
        try:
            with open(file_path, 'rb') as file:
                pdf = PyPDF2.PdfFileReader(file)
                extracted_lines = ''
                for page_num in range(pdf.numPages):
                    page = pdf.getPage(page_num)
                    lines_on_page = page.extractText().split('\n')
                    for line_num in lines:
                        if 0 <= line_num < len(lines_on_page):
                            extracted_lines += lines_on_page[line_num] + '\n'
                return extracted_lines
        except PyPDF2.utils.PdfReadError:
            messagebox.showerror("Ошибка", "Невозможно прочитать PDF файл.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
        return None

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, file_path)

    def extract_text(self):
        file_path = self.entry.get()
        if file_path:
            pdf_lines = self.extract_lines_from_pdf(file_path, [9, 11, 15])  # 10-ая и 12-ая строки
            if pdf_lines:
                self.text_box.delete(1.0, tk.END)
                self.text_box.insert(tk.END, pdf_lines)
        else:
            messagebox.showwarning("Предупреждение", "Файл не выбран.")

    def browse_archive(self):
        grid_cols = self.grid_cols_scale.get()
        grid_rows = self.grid_rows_scale.get()

        # Открытие диалогового окна для выбора архива и папки назначения
        archive_file = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if archive_file:
            output_folder = filedialog.askdirectory()
            if output_folder:
                # Создание ProgressBar и Label для отображения прогресса
                progress_bar = ttk.Progressbar(self.master, length=200, mode="determinate", style="black.Horizontal.TProgressbar")  # Задайте стиль для Progressbar
                progress_bar.pack(pady=10)
                action_label = tk.Label(self.master, text="", bg="#333333", fg="white")  # Задайте цвет фона и цвет текста для Label
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
        text_output_folder = os.path.join(output_folder, "text")
        os.makedirs(text_output_folder, exist_ok=True)  # Создаем папку для текстовых файлов

        total_pages = len(images)
        progress_bar["maximum"] = total_pages

        # Обработка каждого изображения
        for i, image in enumerate(images, start=1):
            image_path = self.crop_and_save(image, output_folder, pdf_filename, i)
            progress_bar["value"] = i
            action_label.config(text=f"Конвертация страницы {i} из {total_pages} ({image_path})")
            self.master.update_idletasks()

            # Извлекаем текст из текущей страницы PDF и записываем его в текстовый файл
            pdf_text = self.extract_text_from_pdf(pdf_data)
            text_file_path = os.path.join(text_output_folder, f"{pdf_filename}_page_{i}.txt")
            with open(text_file_path, "w", encoding="utf-8") as text_file:
                text_file.write(pdf_text)

        # Завершение конвертации - скрытие ProgressBar и отображение завершающей надписи
        progress_bar.pack_forget()
        action_label.config(text="Задача выполнена, Босс")

    def extract_text_from_pdf(self, pdf_data):
        try:
            pdf = PyPDF2.PdfFileReader(io.BytesIO(pdf_data))
            extracted_text = ''
            for page_num in range(pdf.numPages):
                page = pdf.getPage(page_num)
                extracted_text += page.extractText()
            return extracted_text
        except PyPDF2.utils.PdfReadError:
            messagebox.showerror("Ошибка", "Невозможно прочитать PDF файл.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
        return ''

    def filter_text_lines(self, lines):
        filtered_lines = [line for line in lines if check_condition(line)]
        return filtered_lines

    def remove_word_from_text(self, text, word):
        # Удаление всех вхождений слова из текста
        return text.replace(word, "")

    def merge_text_files(self, output_folder, final_text_file):
        text_output_folder = os.path.join(output_folder, "text")
        files = os.listdir(text_output_folder)
        files.sort()
        with open(final_text_file, 'w', encoding='utf-8') as output_file:
            for file in files:
                file_path = os.path.join(text_output_folder, file)
                with open(file_path, 'r', encoding='utf-8') as input_file:
                    lines = input_file.readlines()
                    filtered_lines = self.filter_text_lines(lines)
                    output_file.writelines(filtered_lines)
                    output_file.write('\n')

        # Удаление папки с изначальными текстовыми файлами
        shutil.rmtree(text_output_folder)

        # Удаление вхождений слова "Akeso" из итогового текстового файла
        with open(final_text_file, 'r', encoding='utf-8') as f:
            text = f.read()
            text_without_word = self.remove_word_from_text(text, "Akeso")

        # Запись измененного текста обратно в итоговый текстовый файл
        with open(final_text_file, 'w', encoding='utf-8') as f:
            f.write(text_without_word)

    def merge_images(self, output_folder, progress_bar, action_label, grid_cols, grid_rows):
        cache_folder = os.path.join(output_folder, "cache")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        final_folder = os.path.join(output_folder, f"final_{timestamp}")
        os.makedirs(final_folder, exist_ok=True)

        files = os.listdir(cache_folder)
        images = [f for f in files if f.lower().endswith((".jpg", ".png", ".bmp"))]

        if not images:
            return

        images.sort()
        images_per_grid = grid_cols * grid_rows
        line_thickness = 2  # Толщина линии

        for idx in tqdm(range(0, len(images), images_per_grid), desc="Объединение изображений", unit=" изображений"):
            grid_images = images[idx:idx + images_per_grid]

            merged_width = 829 * grid_cols + (grid_cols - 1) * line_thickness
            merged_height = 1172 * grid_rows + (grid_rows - 1) * line_thickness
            merged_image = Image.new("RGB", (merged_width, merged_height), (255, 255, 255))  # Белый фон

            for i, img_name in enumerate(grid_images):
                col = i % grid_cols
                row = i // grid_cols
                x_offset = (827 + line_thickness) * col
                y_offset = (1170 + line_thickness) * row

                img_path = os.path.join(cache_folder, img_name)
                img = Image.open(img_path)
                img = img.resize((827, 1170))
                merged_image.paste(img, (x_offset, y_offset))

            # Добавляем вертикальные линии
            for i in range(1, grid_cols):
                x = (827 + line_thickness) * i - line_thickness // 2
                for y in range(merged_height):
                    merged_image.putpixel((x, y), (0, 0, 0))  # Чёрная линия

            # Добавляем горизонтальные линии
            for i in range(1, grid_rows):
                y = (1170 + line_thickness) * i - line_thickness // 2
                for x in range(merged_width):
                    merged_image.putpixel((x, y), (0, 0, 0))  # Чёрная линия

            # Сохраняем объединенное изображение
            merged_image.save(os.path.join(final_folder, f"merged_result_{idx // images_per_grid + 1}.jpg"))

        # Удаление папки с изначальными текстовыми файлами
        self.merge_text_files(output_folder, os.path.join(final_folder, "merged_text_file.txt"))

        # Удаление папки с изначальными текстовыми файлами
        shutil.rmtree(cache_folder)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFConverterApp(root)
    root.mainloop()
