import tkinter as tk                    #Библиотке для создания графического интерфейса
from tkinter import scrolledtext        #Текстовое полсе с полосами прокуртки
import os                               #Библиотека для получения данных из OS
import socket                            #Библиотека для работы с сетью (для получения имени компьютера)
import shlex                              # Библиотека для разбора командной строки (для правильной обработки аргументов в кавычках)

class UnixEmulator:
    def __init__(self, root): # self - ссылка на сам объект, root - главное окно приложения
        self.root = root # Сохранение ссылки на главное окно
        self.root.title(f"Эмулятор - [{os.getlogin()}@{socket.gethostname()}]") # getlogin - имя текущего пользователя OC, gethostname - имя компьютера
        self.root.geometry("800x600")
