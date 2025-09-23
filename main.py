import tkinter as tk                                                        # Библиотека для GUI
from tkinter import scrolledtext                                            # виджет текстового поля с полосой прокуртки
import getpass                                                              # Для имени пользователя
import socket                                                               # Для имени компьютера
import shlex                                                                # парсер, который разбивает строку как shell (учитывает кавычки)

class EmulatorOs:
    def __init__(self):
        user = getpass.getuser()
        host = socket.gethostname()

        self.root = tk.Tk()                                                 # Создаем окно
        self.root.title(f'Эмулятор - [{user}@{host}]')                      # Заголовок окна
        self.text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', height=20, width=80)
        # pack - менеджер геометрии (упорядочивает виджеты по пакетам), padx/pady - отступ по гориз./вертикал., fill - как растянуть виджет, expand - доп пространство родителя
        self.text.pack(padx=6, pady=6, fill=tk.BOTH, expand=True)

        self.input_var = tk.StringVar()                                     # Объект, который хранит строковое значение
        self.entry = tk.Entry(self.root, textvariable=self.input_var)       # Однострочное поле для ввода команд
        self.entry.bind('<Return>', self.on_enter)                          # При нажатии Enter
        self.entry.pack(fill=tk.X, padx=6, pady=(0, 6))
        self.entry.focus() # Курсор сразу в поле ввода

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
        elif cmd == "cd":
            self.log(f"cd - args: {args}")
        elif cmd == "exit":
            self.log("Завершение работы...")
            self.root.quit()
        else:
            self.log(f"Неизвестная команда: {cmd}")

    def run(self):
        self.root.mainloop()
    def on_enter(self, event):
        line = self.input_var.get().strip()                                 # Берем строку из StringVar, удаляем пробелы с начала и конца строки
        self.input_var.set("")                                              # Очищаем поле ввода
        if not line:
            return

        self.log(f"> {line}")                                               # Печатаем строку

        cmd, args = self.parse_cmd(line)
        if cmd:
            self.execute(cmd, args)



app = EmulatorOs()
app.run()