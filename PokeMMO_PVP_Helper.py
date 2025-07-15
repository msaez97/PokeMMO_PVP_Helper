import easyocr
import pyautogui
import cv2
import numpy as np
import json
import tkinter as tk
from PIL import Image, ImageTk
import re
import difflib
import sys
import os

# ✅ Resolver rutas seguras para PyInstaller
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

def resource_path(relative_path):
    return os.path.join(base_path, relative_path)

# ✅ Instanciar el lector OCR
reader = easyocr.Reader(['en'])

# ✅ Cargar datos desde JSON
with open(resource_path('type_chart.json'), encoding="utf-8") as f:
    type_chart = json.load(f)

with open(resource_path('pokemon_types.json'), encoding="utf-8") as f:
    pokemon_types = json.load(f)

pokemon_names = list(pokemon_types.keys())

# ✅ Coordenadas de las zonas de captura (ajústalas según resolución)
MY_POKEMON_BOX = (1395, 530, 100, 20)
RIVAL_POKEMON_BOX = (335, 150, 100, 20)

# ✅ Limpieza básica del texto OCR
def clean_text(raw_text):
    # Elimina niveles tipo "Lv.50" o "Nv.50"
    text = re.sub(r'(Lv|Nv)[\.\s]*\d+', '', raw_text, flags=re.IGNORECASE)
    # Normaliza espacios
    text = re.sub(r'\s+', ' ', text)
    # Elimina caracteres no válidos
    text = re.sub(r'[^a-zA-Z\- ]', '', text)
    text = text.strip()
    # 👉 Si hay un espacio, corta y toma solo la primera palabra
    text = text.split(' ')[0]
    return text.capitalize()

# ✅ Corregir nombre aproximado
def correct_name(name):
    matches = difflib.get_close_matches(name, pokemon_names, n=1, cutoff=0.8)
    return matches[0] if matches else name

# ✅ Captura texto con OCR
def get_text(region):
    img = pyautogui.screenshot(region=region)
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    result = reader.readtext(img)
    text = " ".join([item[1] for item in result])
    return correct_name(clean_text(text))

# ✅ Calcular efectividades combinadas
def get_effectiveness(types):
    weak, resist, immune = [], [], []
    for t in types:
        t_data = type_chart.get(t, {})
        weak += t_data.get("weak", [])
        resist += t_data.get("resist", [])
        immune += t_data.get("immune", [])

    result = {}
    for type_name in set(weak + resist + immune):
        mult = 1.0
        for t in types:
            if type_name in type_chart[t]["weak"]:
                mult *= 2
            if type_name in type_chart[t]["resist"]:
                mult *= 0.5
            if type_name in type_chart[t]["immune"]:
                mult *= 0
        result[type_name] = mult

    w, r, i = [], [], []
    for type_name, mult in result.items():
        if mult == 0:
            i.append(type_name)
        elif mult > 1:
            w.append(type_name)
        elif mult < 1:
            r.append(type_name)
    return w, r, i

# ✅ Obtener tipos del Pokémon y calcular efectividades
def get_pokemon_data(name):
    types = pokemon_types.get(name, [])
    return get_effectiveness(types) if types else ([], [], [])

# ✅ Actualizar lado de la interfaz
def update_side(side_widgets, poke_name, w_list, r_list, i_list):
    side_widgets["name_label"].config(text=poke_name)

    for frame_name in ["weak_frame", "resist_frame", "immune_frame"]:
        for widget in side_widgets[frame_name].winfo_children():
            widget.destroy()

    for t in w_list:
        icon = type_icons.get(t)
        if icon:
            lbl = tk.Label(side_widgets["weak_frame"], image=icon, bg="#1e1e1e")
            lbl.pack(side="left", padx=2)
    for t in r_list:
        icon = type_icons.get(t)
        if icon:
            lbl = tk.Label(side_widgets["resist_frame"], image=icon, bg="#1e1e1e")
            lbl.pack(side="left", padx=2)
    for t in i_list:
        icon = type_icons.get(t)
        if icon:
            lbl = tk.Label(side_widgets["immune_frame"], image=icon, bg="#1e1e1e")
            lbl.pack(side="left", padx=2)

# ✅ Actualizar etiquetas cada 3 segundos
def update_labels():
    my_poke = get_text(MY_POKEMON_BOX)
    rival_poke = get_text(RIVAL_POKEMON_BOX)

    my_w, my_r, my_i = get_pokemon_data(my_poke)
    rival_w, rival_r, rival_i = get_pokemon_data(rival_poke)

    update_side(my_widgets, my_poke, my_w, my_r, my_i)
    update_side(rival_widgets, rival_poke, rival_w, rival_r, rival_i)

    root.after(3000, update_labels)

# ✅ INICIALIZAR INTERFAZ
root = tk.Tk()
root.title("⚔️ PokeMMO PVP Helper")
root.configure(bg="#1e1e1e")
root.wm_attributes("-topmost", 1)

width, height = 600, 300
screen_width = root.winfo_screenwidth()
x = screen_width - width
y = 0
root.geometry(f"{width}x{height}+{x}+{y}")

title_label = tk.Label(root, text="⚔️ PokeMMO PVP Helper ⚔️",
                       bg="#1e1e1e", fg="#00ffcc",
                       font=("Helvetica", 14, "bold"))
title_label.pack(pady=5)

# ✅ Cargar iconos de tipos
type_icons = {}
for t in type_chart.keys():
    try:
        img = Image.open(resource_path(f"icons/{t}.png")).resize((30, 30))
        type_icons[t] = ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error cargando icono para {t}: {e}")

# ✅ Cuerpo principal
main_frame = tk.Frame(root, bg="#1e1e1e")
main_frame.pack(fill="both", expand=True)

# ✅ Lado tu Pokémon
my_frame = tk.Frame(main_frame, bg="#1e1e1e")
my_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

my_name_label = tk.Label(my_frame, text="Tu Pokémon", fg="#ffffff", bg="#1e1e1e", font=("Helvetica", 12, "bold"))
my_name_label.pack()

my_weak_label = tk.Label(my_frame, text="💥 Débil a:", fg="#ff4444", bg="#1e1e1e", anchor="w")
my_weak_label.pack(anchor="w")
my_weak_frame = tk.Frame(my_frame, bg="#1e1e1e")
my_weak_frame.pack(anchor="w")

my_resist_label = tk.Label(my_frame, text="🛡️ Resiste:", fg="#44ff44", bg="#1e1e1e", anchor="w")
my_resist_label.pack(anchor="w")
my_resist_frame = tk.Frame(my_frame, bg="#1e1e1e")
my_resist_frame.pack(anchor="w")

my_immune_label = tk.Label(my_frame, text="🚫 Inmune:", fg="#44ffff", bg="#1e1e1e", anchor="w")
my_immune_label.pack(anchor="w")
my_immune_frame = tk.Frame(my_frame, bg="#1e1e1e")
my_immune_frame.pack(anchor="w")

# ✅ Lado rival
rival_frame = tk.Frame(main_frame, bg="#1e1e1e")
rival_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

rival_name_label = tk.Label(rival_frame, text="Rival Pokémon", fg="#ffffff", bg="#1e1e1e", font=("Helvetica", 12, "bold"))
rival_name_label.pack()

rival_weak_label = tk.Label(rival_frame, text="💥 Débil a:", fg="#ff4444", bg="#1e1e1e", anchor="w")
rival_weak_label.pack(anchor="w")
rival_weak_frame = tk.Frame(rival_frame, bg="#1e1e1e")
rival_weak_frame.pack(anchor="w")

rival_resist_label = tk.Label(rival_frame, text="🛡️ Resiste:", fg="#44ff44", bg="#1e1e1e", anchor="w")
rival_resist_label.pack(anchor="w")
rival_resist_frame = tk.Frame(rival_frame, bg="#1e1e1e")
rival_resist_frame.pack(anchor="w")

rival_immune_label = tk.Label(rival_frame, text="🚫 Inmune:", fg="#44ffff", bg="#1e1e1e", anchor="w")
rival_immune_label.pack(anchor="w")
rival_immune_frame = tk.Frame(rival_frame, bg="#1e1e1e")
rival_immune_frame.pack(anchor="w")

footer_label = tk.Label(root, text="Actualiza cada 3s | by MASM",
                        bg="#1e1e1e", fg="#888888",
                        font=("Helvetica", 8))
footer_label.pack(pady=5)

# ✅ Diccionarios de widgets
my_widgets = {
    "name_label": my_name_label,
    "weak_frame": my_weak_frame,
    "resist_frame": my_resist_frame,
    "immune_frame": my_immune_frame
}

rival_widgets = {
    "name_label": rival_name_label,
    "weak_frame": rival_weak_frame,
    "resist_frame": rival_resist_frame,
    "immune_frame": rival_immune_frame
}

# ✅ Iniciar bucle de actualización
update_labels()
root.mainloop()
