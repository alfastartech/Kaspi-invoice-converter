import os
import zipfile
import tkinter as tk
from tkinter import filedialog, ttk, StringVar
from pdf2image import convert_from_bytes
from PIL import Image
from datetime import datetime
from tqdm import tqdm
import shutil

def get_season_color(manual_season=None):
    if manual_season:
        # Ручной выбор сезона
        manual_seasons = {
            'Winter': '#FF0000',  # Красный
            'Spring': '#00FF00',  # Зеленый
            'Summer': '#0000FF',  # Синий
            'Autumn': '#FFFF00'   # Желтый
        }
        return manual_seasons.get(manual_season, '#FFFFFF')  # По умолчанию белый, если сезон не найден

    # Автоматическое определение сезона
    now = datetime.now()
    month = now.month

    # Определение цвета для каждого сезона на основе месяца
    if 1 <= month <= 2 or month == 12:  # Зима: Декабрь, Январь, Февраль
        return '#FF0000'  # Красный
    elif 3 <= month <= 5:  # Весна: Март, Апрель, Май
        return '#00FF00'  # Зеленый
    elif 6 <= month <= 8:  # Лето: Июнь, Июль, Август
        return '#0000FF'  # Синий
    elif 9 <= month <= 11:  # Осень: Сентябрь, Октябрь, Ноябрь
        return '#FFFF00'  # Желтый

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
        action_label.config(text=f"Конвертация страницы {i} из {total_pages} ({image_path})", bg=get_season_color())
        app.update_idletasks()

    # Завершение конвертации - скрытие ProgressBar и отображение завершающей надписи
    progress_bar.pack_forget()
    action_label.config(text="Задача выполнена, Босс", bg=get_season_color())
    app.update_idletasks()

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
            action_label = tk.Label(app, text="", bg=get_season_color())  # Задний фон для Label
            action_label.pack()
            # Обработка архива с PDF-файлами
            process_pdf_archive(archive_file, output_folder, progress_bar, action_label)

            # Запуск функции обновления цветов каждую секунду
            app.after(1000, update_colors)

def update_colors():
    selected_season = season_var.get()
    if selected_season == "Automatic":
        automatic_season = get_season_color()
        app.configure(bg=automatic_season)
        browse_button.config(bg=automatic_season)
        result_label.config(bg=automatic_season)
        bottom_label.config(bg=automatic_season)
        action_label.config(bg=automatic_season)
        watermark_label.config(bg=automatic_season)
    else:
        manual_season_color = get_season_color(manual_season=selected_season)
        app.configure(bg=manual_season_color)
        browse_button.config(bg=manual_season_color)
        result_label.config(bg=manual_season_color)
        bottom_label.config(bg=manual_season_color)
        action_label.config(bg=manual_season_color)
        watermark_label.config(bg=manual_season_color)

    # Повторное запуск функции обновления цветов каждую секунду
    app.after(1000, update_colors)

# Создание основного окна Tkinter
app = tk.Tk()
app.title("Конвертер PDF в JPG для архивов PDF")
app.geometry("500x500")

# Установка цвета фона в зависимости от текущего сезона
season_var = StringVar(app)
season_var.set("Automatic")  # По умолчанию - Автоматический выбор

# Функция для обработки ручного выбора сезона
def on_season_change(*args):
    selected_season = season_var.get()
    if selected_season == "Automatic":
        automatic_season = get_season_color()
        app.configure(bg=automatic_season)
        browse_button.config(bg=automatic_season)
        result_label.config(bg=automatic_season)
        bottom_label.config(bg=automatic_season)
        action_label.config(bg=automatic_season)
        watermark_label.config(bg=automatic_season)
    else:
        manual_season_color = get_season_color(manual_season=selected_season)
        app.configure(bg=manual_season_color)
        browse_button.config(bg=manual_season_color)
        result_label.config(bg=manual_season_color)
        bottom_label.config(bg=manual_season_color)
        action_label.config(bg=manual_season_color)
        watermark_label.config(bg=manual_season_color)

# Выпадающее меню для выбора сезона
season_menu = ttk.Combobox(app, textvariable=season_var, values=["Automatic", "Winter", "Spring", "Summer", "Autumn"])
season_menu.pack(pady=10)
season_menu.bind("<<ComboboxSelected>>", on_season_change)

# Кнопка для выбора архива
browse_button = tk.Button(app, text="Выбрать архив с PDF-файлами", command=browse_archive, bg=get_season_color())  # Задний фон для Button
browse_button.pack(pady=10)

# Метка для вывода результата
result_label = tk.Label(app, text="", bg=get_season_color())  # Задний фон для Label
result_label.pack(pady=10)

# Метка внизу окна
bottom_label = tk.Label(app, text="Сделано для Akeso с любовью", bg=get_season_color())  # Задний фон для Label
bottom_label.pack(side="bottom")

# Метка для отображения прогресса
action_label = tk.Label(app, text="", bg=get_season_color())  # Задний фон для Label
action_label.pack()

# Создание водяного знака
watermark_label = tk.Label(app, text="𝒜𝓁𝒻𝒶", font=("Arial", 24), bg=get_season_color())  # Задний фон для Label
watermark_label.pack()

# Запуск цикла событий Tkinter
app.after(1000, update_colors)  # Запуск функции обновления цветов каждую секунду
app.mainloop()
