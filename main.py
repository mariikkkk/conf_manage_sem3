import tkinter as tk                                                        # Библиотека для GUI
from tkinter import scrolledtext                                            # виджет текстового поля с полосой прокуртки
import getpass                                                              # Для имени пользователя
import socket                                                               # Для имени компьютера
import shlex                                                                # парсер, который разбивает строку как shell (учитывает кавычки)
import argparse                                                             # Для обработки аргументов командной строки
import zipfile                                                              # Для работы с zip файлами (чтение/запись)
import io                                                                   # Для работы с данными в файле прямо в памяти
import os
from dataclasses import dataclass, field                                    # Упрощает работу, не нужно описывать init, repr
from typing import Dict, Optional                                           # Словарь, опциональные значения
@dataclass
class VNode:                                                                # Хранит данные о файле или каталоге, строит дерево каталогов, добавляет файлы
    name: str                                                               # имя элемента (файла/каталога), без полного пути
    is_dir: bool                                                            # флаг, чтобы отличать файл от каталога
    children: Dict[str, "Vnode"] = field(default_factory=dict)              # Дочерние узлы. Словарь (имя - узел) для каждого каталога. Создаем новый пустой словарь для каждого экземпляра
    data: bytes = b""                                                       # Содержимое файла; для каталога - пусто

    def ensure_dir(self, parts):                                            # Обеспечивает, что по пути parts существует цепочка каталогов. Возвращает узел последленго каталога
        node = self                                                         # Начинаем с текущего узла
        for p in parts:                                                     # Идем по пути
            if p not in node.children:                                      # Если не нашли такой каталог
                node.children[p] = VNode(p, True)                           # Создаем новый
            node = node.children[p]
            if not node.is_dir:                                             # Если не каталог (файл)
                raise ValueError(f"Путь содержит файл как каталог: {p}")
        return node
    def add_file(self, parts, data: bytes):                                 # Добавляет файл по пути parts и записывает его содержимое data
        *dirs, filename = parts
        parent = self.ensure_dir(dirs)                                      # Находим узел родитель
        parent.children[filename] = VNode(filename, False, data=data)       # Создаем файл
class VFS:                                                                  # Хранит дерево узлов, имя, хеш, текущий каталог
    def __init__(self, name: str, raw_zip_bytes: bytes, root: VNode):
        self.name = name
        self._raw_zip_bytes = raw_zip_bytes
        self.root = root
        self.cwd = "/"                                                  # Текущий рабочий каталог
    @staticmethod
    def from_zip_file(path: str) -> "VFS":                              # Принимает путь к зип файлу, возвращает новый объект VFS
        try:
            with open(path, "rb") as f:                                 # Открываем zip как бинарный файл
                raw = f.read()                                          # Сырые байты нужны чтобы построить дерево файлов
        except FileNotFoundError as e:
            raise FileNotFoundError(f"VFS не найдена: {path}") from e
        except Exception as e:
            raise RuntimeError(f"Ошибка чтения VFS: {e}") from e
        try:
            root = VNode("/", True)                                      # Создаем корень дерева
            with zipfile.ZipFile(io.BytesIO(raw), "r") as z:       # Открываем ZIP из памяти (io.BytesIO создает файлоподобный объект из raw, zipFile открывает его как архив для чтения
                for info in z.infolist():                                # Обходим все записи архива
                    p = info.filename                                    # путь внутри архива
                    if p.endswith("/"):                                  # Если путь заканчивается на /, то это каталог
                        parts = [x for x in p.strip("/").split("/") if x]# Разбиваем на части
                        root.ensure_dir(parts)                           # Создаем каталог в дереве
                    else:                                                # Значит это файл
                        parts = [x for x in p.split("/") if x]           # Разбиваем на части
                        data = z.read(info.filename)                     # Читаем содержимое файла
                        root.add_file(parts, data)                       # Создаем файл и кладем туда байты
        except zipfile.BadZipfile as e:                                  # zip поврежден/невалиден
            raise ValueError("Неверный формат ZIP для VFS") from e
        return VFS(name=os.path.basename(path), raw_zip_bytes=raw, root=root)   # Создаем объект VFS, оставляем

    def default():
        mem = io.BytesIO()              # Создаем буфер в памяти
        with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("readme.txt", "Hello World!\n")      # Добавляем текстовый файл
            z.writestr("bin/", "")                          # Добавляем каталог
            z.writestr("etc/", "")                          # Добавляем еще один каталог
        raw = mem.getvalue()                                                    # Берем сырые байты zip

        root = VNode("/", True)
        with zipfile.ZipFile(io.BytesIO(raw),"r") as z:                   # Открываем ZIP из памяти (io.BytesIO создает файлоподобный объект из raw, zipFile открывает его как архив для чтения
            for info in z.infolist():                                           # Обходим все записи архива
                p = info.filename                                               # путь внутри архива
                if p.endswith("/"):                                             # Если путь заканчивается на /, то это каталог
                    parts = [x for x in p.strip("/").split("/") if x]           # Разбиваем на части
                    root.ensure_dir(parts)                                      # Создаем каталог в дереве
                else:                                                           # Значит это файл
                    parts = [x for x in p.split("/") if x]                      # Разбиваем на части
                    data = z.read(info.filename)                                # Читаем содержимое файла
                    root.add_file(parts, data)                                  # Создаем файл и кладем туда байты
        return VFS(name="default.zip", raw_zip_bytes=raw, root=root)            # Создаем объект VFS, оставляем




class EmulatorOs:
    def __init__(self, vfs_path=None, script_path=None):
        self.vfs_path = vfs_path
        self.script_path = script_path

        user = getpass.getuser()
        host = socket.gethostname()

        self.root = tk.Tk()                                                 # Создаем окно
        self.root.configure(bg="black")
        self.root.title(f'Эмулятор - [{user}@{host}]')                      # Заголовок окна
        self.text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', height=20, width=80, bg="black", fg="green")
        # pack - менеджер геометрии (упорядочивает виджеты по пакетам), padx/pady - отступ по гориз./вертикал., fill - как растянуть виджет, expand - доп пространство родителя
        self.text.pack(padx=6, pady=6, fill=tk.BOTH, expand=True)

        self.input_var = tk.StringVar()                                     # Объект, который хранит строковое значение
        self.entry = tk.Entry(self.root, textvariable=self.input_var, bg="black", fg="green")       # Однострочное поле для ввода команд
        self.entry.bind('<Return>', self.on_enter)                          # При нажатии Enter
        self.entry.pack(fill=tk.X, padx=6, pady=(0, 6))
        self.entry.focus()                                                  # Курсор сразу в поле ввода

        self.log(f"[debug] vfs = {self.vfs_path}, script = {self.script_path}") # Отладочный вывод параметров

        self.vfs: Optional[VFS] = None                                          # объявляем поле для VFS
        self._init_vfs(vfs_path)                                                # пробуем загрузить zip или создаем дефолт

        if self.script_path:
            self.run_startup_script(self.script_path)                           # Запускаем стартовый скрипт

    def _init_vfs(self, vfs_path: Optional[str]):
        try:
            if vfs_path:
                self.vfs = VFS.from_zip_file(vfs_path)                      # Грузим зип из диска
                self.log(f"[VFS] Загружена '{self.vfs.name}'")
            else:
                self.vfs = VFS.default()
                self.log("[VFS] Создана дефолтная VFS")
        except FileNotFoundError as e:
            self.log(f"[Ошибка] {e}")
        except ValueError as e:
            self.log(f"[Ошибка] {e}")
        except Exception as e:
            self.log(f"[Ошибка] Не удалось инициализировать VFS: {e}")
    def log(self, msg):                                                     # Вывод текста
        self.text.configure(state='normal')                                 # Доступный для записи
        self.text.insert(tk.END, msg + "\n")                                # Перенос строки в конце сообщения
        self.text.see(tk.END)                                               # Прокручиваем вниз
        self.text.configure(state='disabled')

    def parse_cmd(self, line):                                              # Парсер команд
        try:
            parts = shlex.split(line)                                       # Разбивает строку с учётом кавычек
            if not parts:                                                   # Проверка на пустую строку
                return None, []
            return parts[0], parts[1:]                                      # Иначе возвращаем команду и аргументы
        except ValueError as e:                                             # Если строка с ошибкой синтаксиса
            self.log(f"Ошибка парсинга аргументов: {e}")
            return None, []

    def execute(self, cmd, args):
        if cmd == "ls":
            self.log(f"ls - args: {args}")
            return True
        elif cmd == "cd":
            self.log(f"cd - args: {args}")
            return True
        elif cmd == "exit":
            self.log("Завершение работы...")
            self.root.quit()
            return True
        else:
            self.log(f"Неизвестная команда: {cmd}")
            return False

    def run(self):
        self.root.mainloop()
    def on_enter(self, event):
        line = self.input_var.get().strip()                                 # Берем строку из StringVar, удаляем пробелы с начала и конца строки
        self.input_var.set("")                                              # Очищаем поле ввода
        if not line:
            return

        self.log(f">{getpass.getuser()}@{socket.gethostname()} {line}")                                               # Печатаем строку

        cmd, args = self.parse_cmd(line)
        if cmd:
            self.execute(cmd, args)
    def run_startup_script(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:                # with сам закроет файл, "r" - режим чтения
                for lineno, raw_line in enumerate(f, start=1):
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    self.log(f"> {line}")                               # Имитация ввода пользователя
                    cmd, args = self.parse_cmd(line)
                    if not cmd:
                        self.log(f"[Ошибка в строке {lineno}] Парсинг команды не удался.")
                        break
                    ok = self.execute(cmd, args)
                    if not ok:
                        self.log(f"[Ошибка в строке {lineno}] Команда '{cmd}' завершилась ошибкой.")
                        break
        except FileNotFoundError:
            self.log(f"[Ошибка] Стартовый скрипт '{path}' не найден.")
        except Exception as e:
            self.log(f"[Ошибка] При чтении скрипта возникла ошибка: {e}")




def main():
    parser = argparse.ArgumentParser(description="Stage 3")
    parser.add_argument("--vfs", help="Путь к ZIP-файлу виртуальной ФС", default=None)
    parser.add_argument("--script", help="Путь к стартовому скрипту", default=None)
    args = parser.parse_args()

    app = EmulatorOs(vfs_path=args.vfs, script_path=args.script)
    app.run()

main()