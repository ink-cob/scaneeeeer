import os
import re
import socket
import threading  # ТАК МЫ ИСПРАВИЛИ ОШИБКУ
import logging
import cv2
import easyocr
import numpy as np
import pandas as pd
import pyperclip
from flask import Flask, request, jsonify, render_template


os.system("")
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
logging.getLogger('easyocr').setLevel(logging.WARNING)

app = Flask(__name__)

print("[ИИ] Инициализация EasyOCR на CPU... Пожалуйста, подождите.")
reader = easyocr.Reader(['en', 'ru'])

# Локальная база для хранения подтвержденных данных
cmd_table = []

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('8.8.8.8', 80)); ip = s.getsockname()
    except Exception: ip = '127.0.0.1'
    finally: s.close()
    return ip

def refresh_cmd_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    BLUE, GREEN, YELLOW, RED, CYAN, BOLD, RESET = "\033[94m", "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[1m", "\033[0m"
    
    print(f"{BLUE}┌─────────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{BLUE}│{RESET} {BOLD}{CYAN}      ВТОРОЙ ФАЙЛ (CMD): ЖИВОЙ ПРИЕМ ДАННЫХ ДЛЯ WORD            {RESET} {BLUE}│{RESET}")
    print(f"{BLUE}└─────────────────────────────────────────────────────────────────┘{RESET}")
    print(f" 🌐 Ссылка для телефона:  {BOLD}{YELLOW}http://{get_local_ip()}:8080{RESET}")
    print(f"{BLUE}───────────────────────────────────────────────────────────────────{RESET}")
    print(f" {BOLD}УПРАВЛЕНИЕ:{RESET}")
    print(f" [{GREEN}{BOLD} C {RESET}] — {BOLD}Скопировать всю таблицу для Word{RESET} (мгновенный Ctrl+V)")
    print(f" [{RED}{BOLD} Q {RESET}] — {BOLD}Выйти и сохранить Excel архив{RESET}")
    print(f"{BLUE}───────────────────────────────────────────────────────────────────{RESET}")
    print(f" {BOLD}ТЕКУЩАЯ ТАБЛИЦА МОНИТОРОВ:{RESET}\n")
    
    if not cmd_table:
        print(f"    {YELLOW}[ Ожидание первой отправки с телефона... ]{RESET}\n")
    else:
        df = pd.DataFrame(cmd_table)
        table_str = df.to_string(index=False)
        lines = table_str.split('\n')
        print(f"   {BOLD}{CYAN}{lines}{RESET}")
        print(f"   {BLUE}" + "─" * len(lines) + f"{RESET}")
        for line in lines[1:]:
            print(f"   {line}")
        print(f"\n Всего записей: {BOLD}{GREEN}{len(cmd_table)}{RESET} шт.")
    print(f"{BLUE}───────────────────────────────────────────────────────────────────{RESET}")
    print(f"Введите команду ({GREEN}C{RESET}/{RED}Q{RESET}) и нажмите Enter: ", end="", flush=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ocr-line', methods=['POST'])
def ocr_line():
    file = request.files['photo']
    filestr = file.read()
    nparr = np.frombuffer(filestr, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Считываем текст строго из кропнутой узкой рамки
    ocr_result = reader.readtext(frame)
    detected_text = ""
    if ocr_result:
        # Склеиваем слова, если их несколько в рамке, и убираем мусор по краям
        detected_text = " ".join([item.strip() for item in ocr_result]).strip()
        # Чистим от спецсимволов, оставляя буквы, цифры, точки и дефисы
        detected_text = re.sub(r'[^a-zA-Z0-9\-\/\s.]', '', detected_text)
        
    return jsonify({"text": detected_text})

@app.route('/submit-data', methods=['POST'])
def submit_data():
    data = request.json
    
    # Очищаем производителя только до букв по вашему правилу
    clean_brand = re.sub(r'[^a-zA-Zа-яА-Я\s]', '', data.get('brand', ''))
    
    cmd_table.append({
        "№": len(cmd_table) + 1,
        "Производитель": clean_brand.strip().upper(),
        "Модель устройства": data.get('model', '').strip(),
        "Серия / Спецификация": data.get('series', '').strip()
    })
    
    # Мгновенно обновляем CMD экран ПК
    threading.Thread(target=refresh_cmd_screen).start()
    return jsonify({"status": "success"})

def start_server():
    app.run(host='0.0.0.0', port=8080, threaded=True)

if __name__ == "__main__":
    # Запускаем приемщик в фоне
    threading.Thread(target=start_server, daemon=True).start()
    refresh_cmd_screen()
    
    while True:
        cmd = input().strip().lower()
        if cmd == 'c' or cmd == 'с':
            if not cmd_table:
                print(f"\n\033[91m❌ Ошибка: Таблица пуста!\033[0m")
                input("Нажмите Enter...")
            else:
                df = pd.DataFrame(cmd_table)
                tsv_format = df.to_csv(sep='\t', index=False)
                pyperclip.copy(tsv_format)
                print(f"\n\033[92m🚀 Скопировано! Открывайте Word и жмите Ctrl + V.\033[0m")
                input("Нажмите Enter для возврата...")
            refresh_cmd_screen()
        elif cmd == 'q' or cmd == 'й':
            if cmd_table:
                pd.DataFrame(cmd_table).to_excel("final_monitors.xlsx", index=False)
            break
        else:
            refresh_cmd_screen()
