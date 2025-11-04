#!/usr/bin/env python3
"""
W pełni zintegrowany graficzny interfejs dla Droga Szamana RPG.
Dopasowany do rzeczywistego stanu gry - wszystkie lokacje, NPCe, przedmioty.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from tkinter import font as tkfont
import sys
import os
import json
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.game_state import game_state, GameMode
from ui.commands import CommandParser
from player.character import CharacterState
from player.classes import ClassName
from quests.emergent_quests import QuestIntegrationManager, create_quest_seed_library
from quests.quest_engine import QuestEngine, QuestState
from quests.consequences import ConsequenceTracker


class IntegratedRPGInterface:
    """
    W pełni zintegrowany graficzny interfejs gry.
    Wszystkie funkcje dopasowane do rzeczywistego stanu gry.
    """
    
    def __init__(self):
        self.game_state = None
        self.command_parser = None
        
        # System questów
        self.quest_engine = None
        self.quest_integration = None
        self.consequence_tracker = None
        
        # Główne okno
        self.root = tk.Tk()
        self.root.title("Droga Szamana RPG - Więzienie")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        # Style i kolory
        self.setup_styles()
        
        # Stan interfejsu
        self.current_dialogue = None
        self.in_combat = False
        self.selected_target = None
        self.selected_quest = None
        
        # Mapa więzienia - rzeczywiste lokacje
        self.prison_map = {
            'cela_1': {'x': 2, 'y': 1, 'name': 'Cela 1', 'desc': 'Cela Szeptów'},
            'cela_2': {'x': 0, 'y': 1, 'name': 'Cela 2', 'desc': 'Cela Milczenia'},
            'cela_3': {'x': 2, 'y': 3, 'name': 'Cela 3', 'desc': 'Cela Bólu'},
            'cela_4': {'x': 0, 'y': 3, 'name': 'Cela 4', 'desc': 'Cela Mądrości'},
            'cela_5': {'x': 4, 'y': 2, 'name': 'Cela 5', 'desc': 'Cela Zapomnienia'},
            'korytarz_centralny': {'x': 1, 'y': 2, 'name': 'Korytarz', 'desc': 'Centralny'},
            'korytarz_polnocny': {'x': 1, 'y': 1, 'name': 'Korytarz', 'desc': 'Północny'},
            'korytarz_poludniowy': {'x': 1, 'y': 3, 'name': 'Korytarz', 'desc': 'Południowy'},
            'korytarz_wschodni': {'x': 3, 'y': 2, 'name': 'Korytarz', 'desc': 'Wschodni'},
            'kuchnia': {'x': 1, 'y': 0, 'name': 'Kuchnia', 'desc': 'Więzienna'},
            'zbrojownia': {'x': 1, 'y': 4, 'name': 'Zbrojownia', 'desc': 'Tajna'},
            'dziedziniec': {'x': 4, 'y': 1, 'name': 'Dziedziniec', 'desc': 'Spacerowy'},
            'wartownia': {'x': 0, 'y': 2, 'name': 'Wartownia', 'desc': 'Strażnicza'},
            'wiezienie_glowne': {'x': 2, 'y': 2, 'name': 'Więzienie', 'desc': 'Główne'}
        }
        
        # Menu startowe
        self.show_start_menu()
        
    def setup_styles(self):
        """Konfiguruje style dla interfejsu."""
        self.colors = {
            'bg': '#1a1a1a',
            'panel': '#2a2a2a',
            'text': '#e0e0e0',
            'accent': '#4a9eff',
            'health': '#ff4444',
            'mana': '#4444ff',
            'stamina': '#44ff44',
            'pain': '#ff8844',
            'gold': '#ffdd44',
            'border': '#3a3a3a',
            'quest': '#9966ff',
            'consequence': '#ff6666'
        }
        
        self.fonts = {
            'title': tkfont.Font(family="Arial", size=18, weight="bold"),
            'header': tkfont.Font(family="Arial", size=14, weight="bold"),
            'normal': tkfont.Font(family="Arial", size=11),
            'small': tkfont.Font(family="Arial", size=10),
            'console': tkfont.Font(family="Consolas", size=11)
        }
    
    def show_start_menu(self):
        """Pokazuje menu startowe z wyborem klasy."""
        # Wyczyść okno
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Tło
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tytuł
        title_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        title_frame.pack(pady=50)
        
        tk.Label(title_frame, text="DROGA SZAMANA", 
                font=self.fonts['title'], 
                bg=self.colors['bg'], 
                fg=self.colors['accent']).pack()
        
        tk.Label(title_frame, text="Więzienie w Barlionii", 
                font=self.fonts['header'],
                bg=self.colors['bg'],
                fg=self.colors['text']).pack()
        
        # Panel tworzenia postaci
        char_frame = tk.LabelFrame(main_frame, text="STWÓRZ POSTAĆ",
                                  font=self.fonts['header'],
                                  bg=self.colors['panel'],
                                  fg=self.colors['text'])
        char_frame.pack(pady=20)
        
        # Imię postaci
        name_frame = tk.Frame(char_frame, bg=self.colors['panel'])
        name_frame.pack(pady=10, padx=20)
        
        tk.Label(name_frame, text="Imię:", font=self.fonts['normal'],
                bg=self.colors['panel'], fg=self.colors['text']).pack(side=tk.LEFT, padx=5)
        
        self.name_entry = tk.Entry(name_frame, font=self.fonts['normal'],
                                   bg='#1a1a1a', fg=self.colors['text'], width=20)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        self.name_entry.insert(0, "Mahan")
        
        # Wybór klasy
        tk.Label(char_frame, text="Wybierz klasę postaci:",
                font=self.fonts['normal'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        classes_frame = tk.Frame(char_frame, bg=self.colors['panel'])
        classes_frame.pack(pady=10, padx=20)
        
        # Opisy klas
        class_info = {
            'wojownik': {
                'name': '⚔️ Wojownik',
                'desc': 'Żelazna Pięść Losu\n+3 Siła, +2 Wytrzymałość\nSzał bitewny, Tarcza woli',
                'enum': ClassName.WOJOWNIK
            },
            'lotrzyk': {
                'name': '🗡️ Łotrzyk', 
                'desc': 'Cień w Ciemności\n+4 Zręczność, +2 Inteligencja\nPłaszcz cieni, Zwinne palce',
                'enum': ClassName.LOTRZYK
            },
            'lowca': {
                'name': '🏹 Łowca',
                'desc': 'Strażnik Lasu\n+2 Zręczność, +2 Wytrzymałość\nOko sokoła, Zew dziczy',
                'enum': ClassName.LOWCA
            },
            'rzemieslnik': {
                'name': '🔨 Rzemieślnik',
                'desc': 'Kuźnia Przeznaczenia\n+3 Inteligencja, +1 Siła\nBłyskawiczna naprawa, Ładunek wybuchowy',
                'enum': ClassName.RZEMIESLNIK
            },
            'mag': {
                'name': '✨ Mag',
                'desc': 'Tkacz Rzeczywistości\n+4 Inteligencja, +4 Wola\nKula ognia, Bariera arkanów\n⚠️ Posiada manę',
                'enum': ClassName.MAG
            }
        }
        
        self.selected_class = tk.StringVar(value='wojownik')
        
        for i, (key, info) in enumerate(class_info.items()):
            frame = tk.Frame(classes_frame, bg=self.colors['panel'], relief=tk.RAISED, bd=2)
            frame.grid(row=i//3, column=i%3, padx=5, pady=5)
            
            rb = tk.Radiobutton(frame, text=info['name'], 
                               variable=self.selected_class, 
                               value=key,
                               font=self.fonts['normal'],
                               bg=self.colors['panel'],
                               fg=self.colors['text'],
                               selectcolor=self.colors['panel'],
                               activebackground=self.colors['accent'])
            rb.pack(padx=10, pady=5)
            
            tk.Label(frame, text=info['desc'], 
                    font=self.fonts['small'],
                    bg=self.colors['panel'],
                    fg='#aaaaaa',
                    justify=tk.LEFT).pack(padx=10, pady=5)
        
        # Poziom trudności
        diff_frame = tk.Frame(char_frame, bg=self.colors['panel'])
        diff_frame.pack(pady=10)
        
        tk.Label(diff_frame, text="Trudność:", font=self.fonts['normal'],
                bg=self.colors['panel'], fg=self.colors['text']).pack(side=tk.LEFT, padx=5)
        
        self.difficulty = tk.StringVar(value='normal')
        difficulties = [
            ('Łatwy', 'easy'),
            ('Normalny', 'normal'),
            ('Trudny', 'hard'),
            ('Hardcore (permadeath)', 'hardcore')
        ]
        
        for text, value in difficulties:
            tk.Radiobutton(diff_frame, text=text,
                          variable=self.difficulty,
                          value=value,
                          font=self.fonts['small'],
                          bg=self.colors['panel'],
                          fg=self.colors['text'],
                          selectcolor=self.colors['panel']).pack(side=tk.LEFT, padx=5)
        
        # Przyciski
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="🎮 Rozpocznij grę",
                 command=self.start_new_game,
                 font=self.fonts['header'],
                 bg=self.colors['accent'],
                 fg='white',
                 width=20).pack(pady=5)
        
        tk.Button(button_frame, text="💾 Wczytaj grę",
                 command=self.load_game_menu,
                 font=self.fonts['normal'],
                 bg=self.colors['panel'],
                 fg=self.colors['text'],
                 width=20).pack(pady=5)
        
        tk.Button(button_frame, text="❌ Wyjście",
                 command=self.root.quit,
                 font=self.fonts['normal'],
                 bg='#aa4444',
                 fg='white',
                 width=20).pack(pady=5)
    
    def start_new_game(self):
        """Rozpoczyna nową grę z wybraną klasą."""
        name = self.name_entry.get() or "Bezimienny"
        class_key = self.selected_class.get()
        difficulty = self.difficulty.get()
        
        # Mapuj na enum klasy
        class_map = {
            'wojownik': ClassName.WOJOWNIK,
            'lotrzyk': ClassName.LOTRZYK,
            'lowca': ClassName.LOWCA,
            'rzemieslnik': ClassName.RZEMIESLNIK,
            'mag': ClassName.MAG
        }
        
        character_class = class_map.get(class_key)
        
        # Inicjalizuj grę
        game_state.init_game(name, difficulty, character_class.value if character_class else None)
        self.game_state = game_state
        self.command_parser = CommandParser(game_state)
        
        # Inicjalizuj system questów
        self.initialize_quest_system()
        
        # Przejdź do głównego interfejsu
        self.build_game_interface()
        
        # Pokaż intro
        self.show_intro()
    
    def load_game_menu(self):
        """Menu wczytywania gry."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Wczytaj grę")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Wybierz zapis do wczytania:",
                font=self.fonts['header'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        # Lista zapisów
        saves_frame = tk.Frame(dialog, bg=self.colors['panel'])
        saves_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for slot in range(1, 6):
            # Note: Sprawdź czy istnieje zapis
            btn = tk.Button(saves_frame, text=f"Slot {slot}",
                          command=lambda s=slot: self.load_game(s, dialog),
                          font=self.fonts['normal'],
                          bg=self.colors['panel'],
                          fg=self.colors['text'],
                          width=30)
            btn.pack(pady=5)
    
    def load_game(self, slot, dialog):
        """Wczytuje grę z danego slotu."""
        if game_state.load_game(slot):
            self.game_state = game_state
            self.command_parser = CommandParser(game_state)
            dialog.destroy()
            self.build_game_interface()
            self.append_text("Gra wczytana pomyślnie!\n\n", 'success')
            self.execute_command("rozejrzyj")
        else:
            messagebox.showerror("Błąd", "Nie można wczytać gry z tego slotu.")
    
    def build_game_interface(self):
        """Buduje główny interfejs gry."""
        # Wyczyść okno
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Główny kontener
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Górny pasek - status gracza
        self.build_status_bar(main_container)
        
        # Środkowa część - 3 kolumny
        middle_frame = tk.Frame(main_container, bg=self.colors['bg'])
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Lewa kolumna - mapa więzienia
        self.build_map_panel(middle_frame)
        
        # Środkowa kolumna - główny widok
        self.build_main_panel(middle_frame)
        
        # Prawa kolumna - statystyki i ekwipunek
        self.build_right_panel(middle_frame)
        
        # Dolny pasek - akcje
        self.build_action_bar(main_container)
        
        # Rozpocznij auto-update
        self.update_display()
    
    def build_status_bar(self, parent):
        """Buduje górny pasek statusu."""
        status_frame = tk.Frame(parent, bg=self.colors['panel'], height=100)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        # Lewa część - życie, stamina, ból
        left_frame = tk.Frame(status_frame, bg=self.colors['panel'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Życie
        self.health_frame = tk.Frame(left_frame, bg=self.colors['panel'])
        self.health_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(self.health_frame, text="Życie:", width=10,
                font=self.fonts['small'], bg=self.colors['panel'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.health_bar = ttk.Progressbar(self.health_frame, length=200,
                                         mode='determinate', style='Health.Horizontal.TProgressbar')
        self.health_bar.pack(side=tk.LEFT, padx=5)
        
        self.health_label = tk.Label(self.health_frame, text="100/100",
                                    font=self.fonts['small'],
                                    bg=self.colors['panel'],
                                    fg=self.colors['health'])
        self.health_label.pack(side=tk.LEFT, padx=5)
        
        # Stamina
        self.stamina_frame = tk.Frame(left_frame, bg=self.colors['panel'])
        self.stamina_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(self.stamina_frame, text="Stamina:", width=10,
                font=self.fonts['small'], bg=self.colors['panel'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.stamina_bar = ttk.Progressbar(self.stamina_frame, length=200,
                                          mode='determinate')
        self.stamina_bar.pack(side=tk.LEFT, padx=5)
        
        self.stamina_label = tk.Label(self.stamina_frame, text="100/100",
                                     font=self.fonts['small'],
                                     bg=self.colors['panel'],
                                     fg=self.colors['stamina'])
        self.stamina_label.pack(side=tk.LEFT, padx=5)
        
        # Ból
        self.pain_frame = tk.Frame(left_frame, bg=self.colors['panel'])
        self.pain_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(self.pain_frame, text="Ból:", width=10,
                font=self.fonts['small'], bg=self.colors['panel'],
                fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.pain_bar = ttk.Progressbar(self.pain_frame, length=200,
                                       mode='determinate')
        self.pain_bar.pack(side=tk.LEFT, padx=5)
        
        self.pain_label = tk.Label(self.pain_frame, text="0%",
                                  font=self.fonts['small'],
                                  bg=self.colors['panel'],
                                  fg=self.colors['pain'])
        self.pain_label.pack(side=tk.LEFT, padx=5)
        
        # Prawa część - info
        right_frame = tk.Frame(status_frame, bg=self.colors['panel'])
        right_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Klasa postaci
        self.class_label = tk.Label(right_frame, text="Klasa: Wojownik",
                                   font=self.fonts['normal'],
                                   bg=self.colors['panel'],
                                   fg=self.colors['accent'])
        self.class_label.pack(anchor='e')
        
        # Złoto
        self.gold_label = tk.Label(right_frame, text="💰 0 złota",
                                  font=self.fonts['normal'],
                                  bg=self.colors['panel'],
                                  fg=self.colors['gold'])
        self.gold_label.pack(anchor='e')
        
        # Czas
        self.time_label = tk.Label(right_frame, text="🕐 Dzień 1, 07:00",
                                  font=self.fonts['small'],
                                  bg=self.colors['panel'],
                                  fg=self.colors['text'])
        self.time_label.pack(anchor='e')
    
    def build_map_panel(self, parent):
        """Buduje panel z mapą więzienia."""
        map_frame = tk.LabelFrame(parent, text="MAPA WIĘZIENIA",
                                 font=self.fonts['header'],
                                 bg=self.colors['panel'],
                                 fg=self.colors['text'],
                                 width=350)
        map_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        map_frame.pack_propagate(False)
        
        # Canvas na mapę
        self.map_canvas = tk.Canvas(map_frame, bg='#0a0a0a',
                                   highlightthickness=0)
        self.map_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Przyciski kierunkowe
        nav_frame = tk.Frame(map_frame, bg=self.colors['panel'])
        nav_frame.pack(pady=5)
        
        # Układ kierunków
        tk.Button(nav_frame, text="⬆", width=3,
                 command=lambda: self.execute_command("północ"),
                 font=("Arial", 14)).grid(row=0, column=1, padx=1, pady=1)
        
        tk.Button(nav_frame, text="⬅", width=3,
                 command=lambda: self.execute_command("zachód"),
                 font=("Arial", 14)).grid(row=1, column=0, padx=1, pady=1)
        
        tk.Button(nav_frame, text="👁", width=3,
                 command=lambda: self.execute_command("rozejrzyj"),
                 font=("Arial", 14)).grid(row=1, column=1, padx=1, pady=1)
        
        tk.Button(nav_frame, text="➡", width=3,
                 command=lambda: self.execute_command("wschód"),
                 font=("Arial", 14)).grid(row=1, column=2, padx=1, pady=1)
        
        tk.Button(nav_frame, text="⬇", width=3,
                 command=lambda: self.execute_command("południe"),
                 font=("Arial", 14)).grid(row=2, column=1, padx=1, pady=1)
        
        # Przycisk mapy ASCII
        tk.Button(map_frame, text="📜 Pokaż pełną mapę",
                 command=lambda: self.execute_command("mapa"),
                 bg=self.colors['accent'], fg='white').pack(pady=5)
    
    def draw_prison_map(self):
        """Rysuje mapę więzienia."""
        self.map_canvas.delete("all")
        
        # Rozmiary
        cell_size = 50
        padding = 30
        
        # Rysuj pokoje
        for loc_id, loc_data in self.prison_map.items():
            x = padding + loc_data['x'] * (cell_size + 10)
            y = padding + loc_data['y'] * (cell_size + 10)
            
            # Kolor zależny od tego czy to aktualna lokacja
            current = False
            if self.game_state and self.game_state.player:
                current = (self.game_state.player.current_location == loc_id)
            
            color = self.colors['accent'] if current else '#2a2a2a'
            text_color = 'white' if current else '#888888'
            
            # Rysuj pokój
            rect = self.map_canvas.create_rectangle(
                x, y, x + cell_size, y + cell_size,
                fill=color, outline='#4a4a4a', width=2
            )
            
            # Nazwa pokoju
            self.map_canvas.create_text(
                x + cell_size//2, y + cell_size//2 - 8,
                text=loc_data['name'], fill=text_color,
                font=("Arial", 8, "bold")
            )
            
            # Opis
            self.map_canvas.create_text(
                x + cell_size//2, y + cell_size//2 + 8,
                text=loc_data['desc'], fill=text_color,
                font=("Arial", 7)
            )
            
            # Klikalne
            self.map_canvas.tag_bind(rect, "<Button-1>", 
                                    lambda e, loc=loc_id: self.on_map_click(loc))
    
    def on_map_click(self, location):
        """Obsługa kliknięcia na mapie."""
        # Note: Implementacja pathfindingu do lokacji
        self.append_text(f"Cel podróży: {location}\n", 'info')
    
    def build_main_panel(self, parent):
        """Buduje główny panel gry."""
        main_frame = tk.Frame(parent, bg=self.colors['panel'])
        main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Główne okno tekstowe
        self.game_text = scrolledtext.ScrolledText(main_frame,
                                                  wrap=tk.WORD,
                                                  font=self.fonts['console'],
                                                  bg='#0a0a0a',
                                                  fg=self.colors['text'],
                                                  height=25)
        self.game_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel interakcji - NPCe i przedmioty w lokacji
        interaction_frame = tk.LabelFrame(main_frame, text="W LOKACJI",
                                         font=self.fonts['normal'],
                                         bg=self.colors['panel'],
                                         fg=self.colors['text'])
        interaction_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # NPCe
        self.npc_frame = tk.Frame(interaction_frame, bg=self.colors['panel'])
        self.npc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(self.npc_frame, text="Osoby:",
                font=self.fonts['small'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(side=tk.LEFT, padx=5)
        
        self.npc_buttons = tk.Frame(self.npc_frame, bg=self.colors['panel'])
        self.npc_buttons.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Przedmioty
        self.items_frame = tk.Frame(interaction_frame, bg=self.colors['panel'])
        self.items_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(self.items_frame, text="Przedmioty:",
                font=self.fonts['small'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(side=tk.LEFT, padx=5)
        
        self.item_buttons = tk.Frame(self.items_frame, bg=self.colors['panel'])
        self.item_buttons.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Input gracza
        input_frame = tk.Frame(main_frame, bg=self.colors['panel'])
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(input_frame, text=">",
                font=self.fonts['console'],
                bg=self.colors['panel'],
                fg=self.colors['accent']).pack(side=tk.LEFT, padx=5)
        
        self.input_entry = tk.Entry(input_frame,
                                   font=self.fonts['console'],
                                   bg='#0a0a0a',
                                   fg=self.colors['text'])
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_entry.bind('<Return>', self.on_enter_pressed)
        self.input_entry.focus()
        
        tk.Button(input_frame, text="Wyślij",
                 command=self.on_enter_pressed,
                 bg=self.colors['accent'],
                 fg='white').pack(side=tk.RIGHT, padx=5)
    
    def build_right_panel(self, parent):
        """Buduje prawy panel ze statystykami."""
        right_frame = tk.Frame(parent, bg=self.colors['panel'], width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_frame.pack_propagate(False)
        
        # Zakładki
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Zakładka Postać
        self.build_character_tab()
        
        # Zakładka Ekwipunek
        self.build_inventory_tab()
        
        # Zakładka Umiejętności
        self.build_skills_tab()
        
        # Zakładka Dziennik
        self.build_journal_tab()
        
        # Zakładka Questy
        self.build_quests_tab()
    
    def build_character_tab(self):
        """Buduje zakładkę postaci."""
        char_frame = tk.Frame(self.notebook, bg=self.colors['panel'])
        self.notebook.add(char_frame, text="Postać")
        
        # Scrollowany frame
        canvas = tk.Canvas(char_frame, bg=self.colors['panel'])
        scrollbar = tk.Scrollbar(char_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['panel'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Statystyki
        stats_frame = tk.LabelFrame(scrollable_frame, text="ATRYBUTY",
                                   font=self.fonts['normal'],
                                   bg=self.colors['panel'],
                                   fg=self.colors['text'])
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stat_labels = {}
        stats = ['Siła', 'Zręczność', 'Wytrzymałość', 'Inteligencja', 'Wola']
        
        for stat in stats:
            frame = tk.Frame(stats_frame, bg=self.colors['panel'])
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            tk.Label(frame, text=f"{stat}:", width=15, anchor='w',
                    font=self.fonts['small'],
                    bg=self.colors['panel'],
                    fg=self.colors['text']).pack(side=tk.LEFT)
            
            label = tk.Label(frame, text="0", anchor='w',
                           font=self.fonts['small'],
                           bg=self.colors['panel'],
                           fg=self.colors['accent'])
            label.pack(side=tk.LEFT)
            self.stat_labels[stat.lower()] = label
        
        # Stan postaci
        state_frame = tk.LabelFrame(scrollable_frame, text="STAN",
                                   font=self.fonts['normal'],
                                   bg=self.colors['panel'],
                                   fg=self.colors['text'])
        state_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.state_label = tk.Label(state_frame, text="Stan: Normalny",
                                   font=self.fonts['normal'],
                                   bg=self.colors['panel'],
                                   fg=self.colors['stamina'])
        self.state_label.pack(padx=10, pady=5)
        
        self.hunger_label = tk.Label(state_frame, text="Głód: 0%",
                                    font=self.fonts['small'],
                                    bg=self.colors['panel'],
                                    fg=self.colors['text'])
        self.hunger_label.pack(padx=10, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def build_inventory_tab(self):
        """Buduje zakładkę ekwipunku."""
        inv_frame = tk.Frame(self.notebook, bg=self.colors['panel'])
        self.notebook.add(inv_frame, text="Ekwipunek")
        
        # Wyposażone
        equipped_frame = tk.LabelFrame(inv_frame, text="WYPOSAŻONE",
                                      font=self.fonts['normal'],
                                      bg=self.colors['panel'],
                                      fg=self.colors['text'])
        equipped_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.equipped_labels = {}
        slots = ['Broń', 'Głowa', 'Tułów', 'Ręce', 'Nogi']
        
        for slot in slots:
            frame = tk.Frame(equipped_frame, bg=self.colors['panel'])
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            tk.Label(frame, text=f"{slot}:", width=10, anchor='w',
                    font=self.fonts['small'],
                    bg=self.colors['panel'],
                    fg=self.colors['text']).pack(side=tk.LEFT)
            
            label = tk.Label(frame, text="Brak", anchor='w',
                           font=self.fonts['small'],
                           bg=self.colors['panel'],
                           fg='#888888')
            label.pack(side=tk.LEFT)
            self.equipped_labels[slot.lower()] = label
        
        # Lista przedmiotów
        items_frame = tk.LabelFrame(inv_frame, text="PRZEDMIOTY",
                                   font=self.fonts['normal'],
                                   bg=self.colors['panel'],
                                   fg=self.colors['text'])
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Listbox z scrollbarem
        scroll = tk.Scrollbar(items_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.inventory_listbox = tk.Listbox(items_frame,
                                           yscrollcommand=scroll.set,
                                           font=self.fonts['small'],
                                           bg='#1a1a1a',
                                           fg=self.colors['text'],
                                           selectbackground=self.colors['accent'])
        self.inventory_listbox.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.inventory_listbox.yview)
        
        # Przyciski akcji
        inv_buttons = tk.Frame(inv_frame, bg=self.colors['panel'])
        inv_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(inv_buttons, text="Użyj",
                 command=self.use_item,
                 bg=self.colors['accent'],
                 fg='white').pack(side=tk.LEFT, padx=2)
        
        tk.Button(inv_buttons, text="Załóż",
                 command=self.equip_item,
                 bg=self.colors['panel'],
                 fg=self.colors['text']).pack(side=tk.LEFT, padx=2)
        
        tk.Button(inv_buttons, text="Wyrzuć",
                 command=self.drop_item,
                 bg='#aa4444',
                 fg='white').pack(side=tk.LEFT, padx=2)
    
    def build_skills_tab(self):
        """Buduje zakładkę umiejętności."""
        skills_frame = tk.Frame(self.notebook, bg=self.colors['panel'])
        self.notebook.add(skills_frame, text="Umiejętności")
        
        # Lista umiejętności
        canvas = tk.Canvas(skills_frame, bg=self.colors['panel'])
        scrollbar = tk.Scrollbar(skills_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['panel'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.skill_frames = {}
        skills = [
            'Walka Wręcz', 'Miecze', 'Łucznictwo', 'Skradanie',
            'Perswazja', 'Handel', 'Kowalstwo', 'Alchemia',
            'Medycyna', 'Wytrzymałość'
        ]
        
        for skill in skills:
            frame = tk.Frame(scrollable_frame, bg=self.colors['panel'],
                           relief=tk.RIDGE, bd=1)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            # Nazwa umiejętności
            tk.Label(frame, text=skill, width=15, anchor='w',
                    font=self.fonts['small'],
                    bg=self.colors['panel'],
                    fg=self.colors['text']).pack(side=tk.LEFT, padx=5)
            
            # Poziom
            level_label = tk.Label(frame, text="Poziom: 0",
                                 font=self.fonts['small'],
                                 bg=self.colors['panel'],
                                 fg=self.colors['accent'])
            level_label.pack(side=tk.LEFT, padx=5)
            
            # Progress bar
            progress = ttk.Progressbar(frame, length=100,
                                      mode='determinate',
                                      maximum=100)
            progress.pack(side=tk.LEFT, padx=5)
            
            self.skill_frames[skill] = {
                'level': level_label,
                'progress': progress
            }
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def build_journal_tab(self):
        """Buduje zakładkę dziennika."""
        journal_frame = tk.Frame(self.notebook, bg=self.colors['panel'])
        self.notebook.add(journal_frame, text="Dziennik")
        
        # Lista questów
        quest_label = tk.Label(journal_frame, text="AKTYWNE ZADANIA",
                             font=self.fonts['normal'],
                             bg=self.colors['panel'],
                             fg=self.colors['text'])
        quest_label.pack(pady=5)
        
        self.quest_listbox = tk.Listbox(journal_frame,
                                       font=self.fonts['small'],
                                       bg='#1a1a1a',
                                       fg=self.colors['text'],
                                       height=10)
        self.quest_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Notatki
        notes_label = tk.Label(journal_frame, text="NOTATKI",
                             font=self.fonts['normal'],
                             bg=self.colors['panel'],
                             fg=self.colors['text'])
        notes_label.pack(pady=5)
        
        self.notes_text = tk.Text(journal_frame,
                                 font=self.fonts['small'],
                                 bg='#1a1a1a',
                                 fg=self.colors['text'],
                                 height=10,
                                 wrap=tk.WORD)
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def build_quests_tab(self):
        """Buduje zakładkę questów emergentnych."""
        quest_frame = tk.Frame(self.notebook, bg=self.colors['panel'])
        self.notebook.add(quest_frame, text="Questy")
        
        # Panel questów aktywnych
        active_frame = tk.LabelFrame(quest_frame, text="AKTYWNE SYTUACJE",
                                   font=self.fonts['normal'],
                                   bg=self.colors['panel'],
                                   fg=self.colors['quest'])
        active_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Lista questów
        self.active_quests_listbox = tk.Listbox(active_frame,
                                               font=self.fonts['small'],
                                               bg='#1a1a1a',
                                               fg=self.colors['quest'],
                                               height=8,
                                               selectmode=tk.SINGLE)
        self.active_quests_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.active_quests_listbox.bind('<<ListboxSelect>>', self.on_quest_selected)
        
        # Szczegóły questa
        details_frame = tk.LabelFrame(quest_frame, text="SZCZEGÓŁY",
                                    font=self.fonts['normal'],
                                    bg=self.colors['panel'],
                                    fg=self.colors['text'])
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.quest_details_text = scrolledtext.ScrolledText(details_frame,
                                                           font=self.fonts['small'],
                                                           bg='#1a1a1a',
                                                           fg=self.colors['text'],
                                                           height=8,
                                                           wrap=tk.WORD,
                                                           state=tk.DISABLED)
        self.quest_details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel konsekwencji
        consequences_frame = tk.LabelFrame(quest_frame, text="KONSEKWENCJE TWOICH DZIAŁAŃ",
                                         font=self.fonts['normal'],
                                         bg=self.colors['panel'],
                                         fg=self.colors['consequence'])
        consequences_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.consequences_text = tk.Text(consequences_frame,
                                        font=self.fonts['small'],
                                        bg='#1a1a1a',
                                        fg=self.colors['consequence'],
                                        height=4,
                                        wrap=tk.WORD,
                                        state=tk.DISABLED)
        self.consequences_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Przyciski akcji questowych
        quest_actions_frame = tk.Frame(quest_frame, bg=self.colors['panel'])
        quest_actions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(quest_actions_frame, text="🔍 Zbadaj",
                 command=self.investigate_quest,
                 font=self.fonts['small'],
                 bg=self.colors['accent'],
                 fg='white').pack(side=tk.LEFT, padx=2)
        
        tk.Button(quest_actions_frame, text="💡 Rozwiąż",
                 command=self.resolve_quest,
                 font=self.fonts['small'],
                 bg=self.colors['stamina'],
                 fg='white').pack(side=tk.LEFT, padx=2)
        
        tk.Button(quest_actions_frame, text="🚫 Zignoruj",
                 command=self.ignore_quest,
                 font=self.fonts['small'],
                 bg=self.colors['health'],
                 fg='white').pack(side=tk.LEFT, padx=2)
    
    def build_action_bar(self, parent):
        """Buduje dolny pasek akcji."""
        action_frame = tk.Frame(parent, bg=self.colors['panel'])
        action_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Podstawowe akcje
        basic_frame = tk.LabelFrame(action_frame, text="AKCJE",
                                   font=self.fonts['small'],
                                   bg=self.colors['panel'],
                                   fg=self.colors['text'])
        basic_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        actions = [
            ("🔍 Szukaj", "szukaj"),
            ("💬 Rozmawiaj", self.show_dialogue_menu),
            ("⚔️ Atakuj", self.show_attack_menu),
            ("🛡️ Broń się", "broń"),
            ("🎒 Ekwipunek", "ekwipunek"),
            ("💤 Odpocznij", "odpocznij"),
            ("⏰ Czekaj", self.wait_time),
            ("💾 Zapisz", self.save_game)
        ]
        
        for i, (text, cmd) in enumerate(actions):
            if callable(cmd):
                btn = tk.Button(basic_frame, text=text,
                              command=cmd,
                              font=self.fonts['small'],
                              width=12)
            else:
                btn = tk.Button(basic_frame, text=text,
                              command=lambda c=cmd: self.execute_command(c),
                              font=self.fonts['small'],
                              width=12)
            
            btn.grid(row=i//4, column=i%4, padx=2, pady=2)
        
        # Przycisk wyjścia
        tk.Button(action_frame, text="❌ Menu główne",
                 command=self.return_to_menu,
                 bg='#aa4444',
                 fg='white',
                 font=self.fonts['normal']).pack(side=tk.RIGHT, padx=10, pady=5)
    
    def show_intro(self):
        """Pokazuje intro gry."""
        intro = """
Budzisz się na zimnej, kamiennej podłodze. Głowa pęka ci z bólu, a w ustach czujesz metaliczny posmak krwi.

Jesteś w celi więziennej. Małej, ciemnej, cuchnącej pleśnią i rozpaczą.

Musisz stąd uciec. Ale najpierw musisz przeżyć...

"""
        self.append_text(intro, 'story')
        self.execute_command("rozejrzyj")
    
    def execute_command(self, command):
        """Wykonuje komendę gry."""
        if not command:
            return
        
        # Wyświetl komendę
        self.append_text(f"\n> {command}\n", 'command')
        
        # Wykonaj
        success, message = self.command_parser.parse_and_execute(command)
        
        # Wyświetl wynik
        if message:
            # Obsłuż zarówno string jak i listę
            if isinstance(message, list):
                for msg in message:
                    self.append_text(str(msg) + "\n", 'normal' if success else 'error')
            else:
                self.append_text(str(message) + "\n", 'normal' if success else 'error')
        
        # Aktualizuj interfejs
        self.update_display()
        self.update_location_info()
    
    def append_text(self, text, style='normal'):
        """Dodaje tekst do okna gry."""
        self.game_text.config(state=tk.NORMAL)
        
        start = self.game_text.index(tk.END)
        self.game_text.insert(tk.END, text)
        
        # Kolorowanie
        if style == 'command':
            self.game_text.tag_add('command', f"{start}", tk.END)
            self.game_text.tag_config('command', foreground=self.colors['accent'])
        elif style == 'error':
            self.game_text.tag_add('error', f"{start}", tk.END)
            self.game_text.tag_config('error', foreground=self.colors['health'])
        elif style == 'success':
            self.game_text.tag_add('success', f"{start}", tk.END)
            self.game_text.tag_config('success', foreground=self.colors['stamina'])
        elif style == 'story':
            self.game_text.tag_add('story', f"{start}", tk.END)
            self.game_text.tag_config('story', foreground='#ffaa66', font=self.fonts['normal'])
        elif style == 'quest':
            self.game_text.tag_add('quest', f"{start}", tk.END)
            self.game_text.tag_config('quest', foreground=self.colors['quest'], font=self.fonts['normal'])
        elif style == 'consequence':
            self.game_text.tag_add('consequence', f"{start}", tk.END)
            self.game_text.tag_config('consequence', foreground=self.colors['consequence'], font=self.fonts['normal'])
        
        self.game_text.config(state=tk.DISABLED)
        self.game_text.see(tk.END)
    
    def update_display(self):
        """Aktualizuje cały interfejs."""
        if not self.game_state or not self.game_state.player:
            self.root.after(1000, self.update_display)
            return
        
        player = self.game_state.player
        
        # Status bars
        self.health_bar['maximum'] = player.max_health
        self.health_bar['value'] = player.health
        self.health_label.config(text=f"{player.health}/{player.max_health}")
        
        self.stamina_bar['maximum'] = player.max_stamina
        self.stamina_bar['value'] = player.stamina
        self.stamina_label.config(text=f"{player.stamina}/{player.max_stamina}")
        
        pain = getattr(player, 'pain', 0)
        self.pain_bar['maximum'] = 100
        self.pain_bar['value'] = pain
        self.pain_label.config(text=f"{pain}%")
        
        # Klasa
        if player.character_class:
            self.class_label.config(text=f"Klasa: {player.character_class.name}")
        
        # Złoto
        gold = player.gold if hasattr(player, 'gold') else 0
        self.gold_label.config(text=f"💰 {gold} złota")
        
        # Czas
        time_str = f"🕐 Dzień {self.game_state.day}, {self.game_state.game_time//60:02d}:{self.game_state.game_time%60:02d}"
        self.time_label.config(text=time_str)
        
        # Statystyki
        if hasattr(self, 'stat_labels'):
            self.stat_labels['siła'].config(text=str(player.strength))
            self.stat_labels['zręczność'].config(text=str(player.agility))
            self.stat_labels['wytrzymałość'].config(text=str(player.endurance))
            self.stat_labels['inteligencja'].config(text=str(player.intelligence))
            self.stat_labels['wola'].config(text=str(player.willpower))
        
        # Stan
        if hasattr(self, 'state_label'):
            self.state_label.config(text=f"Stan: {player.state.value}")
            hunger = getattr(player, 'hunger', 0)
            self.hunger_label.config(text=f"Głód: {hunger}%")
        
        # Ekwipunek
        self.update_inventory()
        
        # Umiejętności
        self.update_skills()
        
        # Mapa
        self.draw_prison_map()
        
        # Aktualizuj questy
        self.update_quests()
        
        # Powtórz
        self.root.after(1000, self.update_display)
    
    def update_location_info(self):
        """Aktualizuje informacje o lokacji."""
        if not self.game_state or not self.game_state.prison:
            return
        
        location = self.game_state.prison.get_current_location()
        if not location:
            return
        
        # NPCe w lokacji
        for widget in self.npc_buttons.winfo_children():
            widget.destroy()
        
        npcs = []
        if hasattr(location, 'prisoners'):
            for prisoner in location.prisoners:
                npcs.append(prisoner.name)
        if hasattr(location, 'guards'):
            for guard in location.guards:
                npcs.append(guard.name)
        if hasattr(location, 'npcs'):
            for npc in location.npcs:
                if hasattr(npc, 'name'):
                    npcs.append(npc.name)
        
        # Sprawdź też NPCów z managera
        if self.game_state.npc_manager:
            for npc_id, npc in self.game_state.npc_manager.npcs.items():
                if hasattr(npc, 'current_location'):
                    if npc.current_location == self.game_state.current_location:
                        if npc.name not in npcs:
                            npcs.append(npc.name)
        
        for npc_name in npcs[:6]:  # Max 6 NPCów
            btn = tk.Button(self.npc_buttons, text=npc_name,
                          command=lambda n=npc_name: self.interact_with_npc(n),
                          font=self.fonts['small'],
                          bg=self.colors['panel'],
                          fg=self.colors['text'])
            btn.pack(side=tk.LEFT, padx=2)
        
        # Przedmioty w lokacji
        for widget in self.item_buttons.winfo_children():
            widget.destroy()
        
        if hasattr(location, 'items'):
            for item in location.items[:6]:  # Max 6 przedmiotów
                item_name = item.name if hasattr(item, 'name') else str(item)
                btn = tk.Button(self.item_buttons, text=item_name,
                              command=lambda i=item_name: self.take_item(i),
                              font=self.fonts['small'],
                              bg=self.colors['panel'],
                              fg=self.colors['text'])
                btn.pack(side=tk.LEFT, padx=2)
    
    def update_inventory(self):
        """Aktualizuje ekwipunek."""
        if not self.game_state or not self.game_state.player:
            return
        
        player = self.game_state.player
        
        # Wyposażone
        if hasattr(player, 'equipment'):
            eq = player.equipment
            
            # Broń
            if eq.weapon:
                weapon_name = eq.weapon.get('name', 'Nieznana broń')
                self.equipped_labels['broń'].config(text=weapon_name)
            
            # Pancerz
            for slot, label_key in [('glowa', 'głowa'), ('tulow', 'tułów'), 
                                   ('rece', 'ręce'), ('nogi', 'nogi')]:
                armor = eq.armor.get(slot)
                if armor:
                    self.equipped_labels[label_key].config(text=armor.get('name', 'Nieznany'))
        
        # Lista przedmiotów
        self.inventory_listbox.delete(0, tk.END)
        if hasattr(player, 'equipment') and hasattr(player.equipment, 'items'):
            for item in player.equipment.items:
                if isinstance(item, dict):
                    name = item.get('name', 'Nieznany przedmiot')
                    quality = item.get('quality', '')
                    if quality:
                        name = f"{name} ({quality})"
                    self.inventory_listbox.insert(tk.END, name)
                else:
                    self.inventory_listbox.insert(tk.END, str(item))
    
    def update_skills(self):
        """Aktualizuje umiejętności."""
        if not self.game_state or not self.game_state.player:
            return
        
        player = self.game_state.player
        
        if hasattr(player, 'skills'):
            from player.skills import SkillName
            
            skill_map = {
                'Walka Wręcz': SkillName.WALKA_WRECZ,
                'Miecze': SkillName.MIECZE,
                'Łucznictwo': SkillName.LUCZNICTWO,
                'Skradanie': SkillName.SKRADANIE,
                'Perswazja': SkillName.PERSWAZJA,
                'Handel': SkillName.HANDEL,
                'Kowalstwo': SkillName.KOWALSTWO,
                'Alchemia': SkillName.ALCHEMIA,
                'Medycyna': SkillName.MEDYCYNA,
                'Wytrzymałość': SkillName.WYTRZYMALOSC
            }
            
            for skill_name, skill_enum in skill_map.items():
                if skill_name in self.skill_frames:
                    try:
                        skill = player.skills.get_skill(skill_enum)
                        if skill:
                            self.skill_frames[skill_name]['level'].config(
                                text=f"Poziom: {skill.level}"
                            )
                            # Progress do następnego poziomu
                            progress = int((skill.experience % 100))
                            self.skill_frames[skill_name]['progress']['value'] = progress
                    except:
                        pass
    
    def interact_with_npc(self, npc_name):
        """Interakcja z NPC."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=f"Rozmawiaj z {npc_name}",
                        command=lambda: self.execute_command(f"rozmawiaj {npc_name}"))
        menu.add_command(label=f"Zbadaj {npc_name}",
                        command=lambda: self.execute_command(f"zbadaj {npc_name}"))
        
        # Handel dla niektórych NPCów
        if "kowal" in npc_name.lower() or "handlarz" in npc_name.lower():
            menu.add_separator()
            menu.add_command(label=f"Handluj z {npc_name}",
                           command=lambda: self.execute_command(f"handluj {npc_name}"))
        
        # Atak dla wrogów
        if "szczur" in npc_name.lower() or "strażnik" in npc_name.lower():
            menu.add_separator()
            menu.add_command(label=f"Atakuj {npc_name}",
                           command=lambda: self.execute_command(f"atakuj {npc_name}"))
        
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
    
    def take_item(self, item_name):
        """Podnosi przedmiot."""
        self.execute_command(f"weź {item_name}")
    
    def use_item(self):
        """Używa wybranego przedmiotu."""
        selection = self.inventory_listbox.curselection()
        if selection:
            item = self.inventory_listbox.get(selection[0])
            # Usuń info o jakości
            if '(' in item:
                item = item.split('(')[0].strip()
            self.execute_command(f"użyj {item}")
    
    def equip_item(self):
        """Zakłada przedmiot."""
        selection = self.inventory_listbox.curselection()
        if selection:
            item = self.inventory_listbox.get(selection[0])
            if '(' in item:
                item = item.split('(')[0].strip()
            self.execute_command(f"załóż {item}")
    
    def drop_item(self):
        """Wyrzuca przedmiot."""
        selection = self.inventory_listbox.curselection()
        if selection:
            item = self.inventory_listbox.get(selection[0])
            if '(' in item:
                item = item.split('(')[0].strip()
            if messagebox.askyesno("Potwierdź", f"Wyrzucić {item}?"):
                self.execute_command(f"wyrzuć {item}")
    
    def show_dialogue_menu(self):
        """Menu wyboru NPC do rozmowy."""
        # Pobierz NPCów z lokacji
        npcs = []
        if self.game_state and self.game_state.prison:
            location = self.game_state.prison.get_current_location()
            if location:
                if hasattr(location, 'prisoners'):
                    npcs.extend([p.name for p in location.prisoners])
                if hasattr(location, 'guards'):
                    npcs.extend([g.name for g in location.guards])
        
        # Dodaj NPCów z managera
        if self.game_state and self.game_state.npc_manager:
            for npc_id, npc in self.game_state.npc_manager.npcs.items():
                if hasattr(npc, 'current_location'):
                    if npc.current_location == self.game_state.current_location:
                        if npc.name not in npcs:
                            npcs.append(npc.name)
        
        if not npcs:
            self.append_text("Nikogo tu nie ma.\n", 'error')
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz rozmówcę")
        dialog.geometry("300x400")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Z kim chcesz porozmawiać?",
                font=self.fonts['header'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        for npc in npcs:
            tk.Button(dialog, text=npc, width=25,
                    command=lambda n=npc: [
                        self.execute_command(f"rozmawiaj {n}"),
                        dialog.destroy()
                    ],
                    font=self.fonts['normal'],
                    bg=self.colors['panel'],
                    fg=self.colors['text']).pack(pady=3)
    
    def show_attack_menu(self):
        """Menu wyboru celu ataku."""
        targets = []
        
        # Znajdź wrogów w lokacji
        if self.game_state and self.game_state.prison:
            location = self.game_state.prison.get_current_location()
            if location:
                # Szczególnie szczur i agresywni więźniowie
                if hasattr(location, 'npcs'):
                    for npc in location.npcs:
                        if hasattr(npc, 'name'):
                            if 'szczur' in npc.name.lower():
                                targets.append(npc.name)
        
        # Dodaj NPCów z managera
        if self.game_state and self.game_state.npc_manager:
            for npc_id, npc in self.game_state.npc_manager.npcs.items():
                if hasattr(npc, 'current_location'):
                    if npc.current_location == self.game_state.current_location:
                        if 'szczur' in npc.name.lower() or 'rat' in npc_id:
                            if npc.name not in targets:
                                targets.append(npc.name)
        
        if not targets:
            self.append_text("Nie ma tu wrogów do zaatakowania.\n", 'info')
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz cel ataku")
        dialog.geometry("300x200")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Kogo zaatakować?",
                font=self.fonts['header'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        for target in targets:
            tk.Button(dialog, text=target, width=25,
                    command=lambda t=target: [
                        self.execute_command(f"atakuj {t}"),
                        dialog.destroy()
                    ],
                    font=self.fonts['normal'],
                    bg='#aa4444',
                    fg='white').pack(pady=3)
    
    def wait_time(self):
        """Dialog czekania."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Czekaj")
        dialog.geometry("250x150")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Ile minut czekać?",
                font=self.fonts['normal'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        entry = tk.Entry(dialog, font=self.fonts['normal'])
        entry.pack(pady=5)
        entry.insert(0, "30")
        
        tk.Button(dialog, text="Czekaj",
                command=lambda: [
                    self.execute_command(f"czekaj {entry.get()}"),
                    dialog.destroy()
                ],
                bg=self.colors['accent'],
                fg='white').pack(pady=10)
    
    def save_game(self):
        """Zapisuje grę."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Zapisz grę")
        dialog.geometry("300x200")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Wybierz slot zapisu:",
                font=self.fonts['header'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        for slot in range(1, 6):
            tk.Button(dialog, text=f"Slot {slot}",
                    command=lambda s=slot: [
                        self.execute_command(f"zapisz {s}"),
                        dialog.destroy(),
                        messagebox.showinfo("Sukces", f"Gra zapisana w slocie {s}")
                    ],
                    width=20,
                    font=self.fonts['normal'],
                    bg=self.colors['panel'],
                    fg=self.colors['text']).pack(pady=3)
    
    def return_to_menu(self):
        """Powrót do menu głównego."""
        if messagebox.askyesno("Potwierdź", "Czy na pewno wrócić do menu? Niezapisany postęp zostanie utracony!"):
            self.show_start_menu()
    
    def on_enter_pressed(self, event=None):
        """Obsługa Enter w polu input."""
        command = self.input_entry.get()
        if command:
            self.execute_command(command)
            self.input_entry.delete(0, tk.END)
    
    # ========== METODY SYSTEMU QUESTÓW ==========
    
    def initialize_quest_system(self):
        """Inicjalizuje system questów emergentnych."""
        # Stwórz silnik questów
        self.quest_engine = QuestEngine()
        
        # Stwórz tracker konsekwencji
        self.consequence_tracker = ConsequenceTracker()
        
        # Stwórz manager integracji
        if hasattr(self.game_state, 'npc_manager'):
            self.quest_integration = QuestIntegrationManager(
                self.quest_engine,
                self.game_state,
                self.game_state.npc_manager
            )
        else:
            # Podstawowa inicjalizacja bez NPCów
            self.quest_engine.world_state = {
                "location": "wiezienie",
                "player_imprisoned": True,
                "time_in_prison": 0
            }
            self.quest_engine.player_state = {}
            
            # Zarejestruj podstawowe ziarna questów
            seeds = create_quest_seed_library()
            for seed in seeds.values():
                self.quest_engine.register_seed(seed)
    
    def update_quests(self):
        """Aktualizuje system questów."""
        if not self.quest_integration:
            return
        
        # Aktualizuj integrację
        self.quest_integration.update()
        
        # Przetwórz konsekwencje
        if self.game_state.npc_manager and self.game_state.player:
            consequences = self.consequence_tracker.process_due_consequences(
                self.quest_engine.world_state,
                self.game_state.npc_manager,
                self.game_state.player
            )
            
            # Wyświetl konsekwencje
            for cons in consequences:
                self.append_text(
                    f"\n[KONSEKWENCJA] {cons.get('quest', 'Unknown')}: Efekty się ujawniają...\n",
                    'consequence'
                )
        
        # Aktualizuj UI questów
        self.update_quest_ui()
    
    def update_quest_ui(self):
        """Aktualizuje interfejs questów."""
        if not hasattr(self, 'active_quests_listbox'):
            return
        
        # Wyczyść listę
        self.active_quests_listbox.delete(0, tk.END)
        
        # Dodaj aktywne questy
        for quest in self.quest_engine.get_active_quests():
            status_icon = ""
            if quest.state == QuestState.DISCOVERABLE:
                status_icon = "❓"
            elif quest.state == QuestState.ACTIVE:
                status_icon = "❗"
            elif quest.state == QuestState.INVESTIGATING:
                status_icon = "🔍"
            elif quest.state == QuestState.RESOLVED:
                status_icon = "✅"
            
            quest_name = f"{status_icon} {quest.seed.name}"
            self.active_quests_listbox.insert(tk.END, quest_name)
        
        # Dodaj podpowiedzi o odkrywalnych questach
        discoverable = self.quest_engine.get_discoverable_quests()
        if discoverable:
            self.active_quests_listbox.insert(tk.END, "")
            self.active_quests_listbox.insert(tk.END, "--- Coś się dzieje... ---")
            for quest in discoverable:
                hint = f"💭 {list(quest.seed.initial_clues.keys())[0]}: ???"
                self.active_quests_listbox.insert(tk.END, hint)
        
        # Aktualizuj timeline konsekwencji
        self.update_consequences_display()
    
    def on_quest_selected(self, event):
        """Obsługa wyboru questa z listy."""
        selection = self.active_quests_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        quests = self.quest_engine.get_active_quests()
        
        if index < len(quests):
            quest = quests[index]
            self.selected_quest = quest.quest_id
            self.show_quest_details(quest)
    
    def show_quest_details(self, quest):
        """Pokazuje szczegóły questa."""
        self.quest_details_text.config(state=tk.NORMAL)
        self.quest_details_text.delete(1.0, tk.END)
        
        # Nazwa i stan
        self.quest_details_text.insert(tk.END, f"{quest.seed.name}\n", 'title')
        self.quest_details_text.insert(tk.END, f"Stan: {quest.state.value}\n\n", 'state')
        
        # Wskazówki
        if quest.investigation.discovered_clues:
            self.quest_details_text.insert(tk.END, "Odkryte wskazówki:\n", 'header')
            for clue in quest.investigation.discovered_clues:
                self.quest_details_text.insert(tk.END, f"• {clue}\n", 'clue')
            self.quest_details_text.insert(tk.END, "\n")
        
        # Postęp śledztwa
        progress = quest.investigation.get_completion_percentage(10)
        self.quest_details_text.insert(tk.END, f"Postęp śledztwa: {progress:.0f}%\n\n", 'progress')
        
        # Dostępne rozwiązania
        branches = self.quest_engine.get_available_branches(quest.quest_id)
        if branches:
            self.quest_details_text.insert(tk.END, "Możliwe rozwiązania:\n", 'header')
            for branch in branches:
                self.quest_details_text.insert(tk.END, f"• {branch['description']}\n", 'branch')
        
        # Formatowanie
        self.quest_details_text.tag_config('title', font=self.fonts['header'], 
                                          foreground=self.colors['quest'])
        self.quest_details_text.tag_config('state', foreground=self.colors['accent'])
        self.quest_details_text.tag_config('header', font=self.fonts['normal'], 
                                          foreground=self.colors['text'])
        self.quest_details_text.tag_config('clue', foreground=self.colors['stamina'])
        self.quest_details_text.tag_config('progress', foreground=self.colors['gold'])
        self.quest_details_text.tag_config('branch', foreground=self.colors['accent'])
        
        self.quest_details_text.config(state=tk.DISABLED)
    
    def update_consequences_display(self):
        """Aktualizuje wyświetlanie konsekwencji."""
        if not hasattr(self, 'consequences_text'):
            return
        
        self.consequences_text.config(state=tk.NORMAL)
        self.consequences_text.delete(1.0, tk.END)
        
        # Pobierz timeline
        timeline = self.consequence_tracker.get_consequence_timeline()
        
        # Pokaż ostatnie konsekwencje
        recent = timeline[-5:] if timeline else []
        for event in recent:
            time_str = event['time'].split('T')[1][:5]  # HH:MM
            if event['type'] == 'scheduled':
                self.consequences_text.insert(
                    tk.END,
                    f"⏰ {time_str}: {event['quest']} - zaplanowane\n",
                    'scheduled'
                )
            else:
                self.consequences_text.insert(
                    tk.END,
                    f"✓ {time_str}: {event['quest']} - wykonane\n",
                    'completed'
                )
        
        # Pokaż karmę
        karma = self.consequence_tracker.get_karma_score()
        if karma:
            dominant = max(karma, key=karma.get)
            self.consequences_text.insert(
                tk.END,
                f"\nKarma: {dominant.capitalize()} ({karma[dominant]:.0f}%)",
                'karma'
            )
        
        # Formatowanie
        self.consequences_text.tag_config('scheduled', foreground=self.colors['gold'])
        self.consequences_text.tag_config('completed', foreground=self.colors['stamina'])
        self.consequences_text.tag_config('karma', foreground=self.colors['quest'])
        
        self.consequences_text.config(state=tk.DISABLED)
    
    def investigate_quest(self):
        """Prowadzi śledztwo w sprawie questa."""
        if not self.selected_quest:
            messagebox.showinfo("Info", "Wybierz najpierw questa do zbadania")
            return
        
        # Dialog wyboru akcji
        dialog = tk.Toplevel(self.root)
        dialog.title("Śledztwo")
        dialog.geometry("300x200")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Jak chcesz prowadzić śledztwo?",
                font=self.fonts['normal'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        actions = [
            ("Przeszukaj okolicę", "search"),
            ("Przesłuchaj NPCów", "interrogate"),
            ("Zbadaj ślady", "scout"),
            ("Analizuj wskazówki", "analyze")
        ]
        
        for text, action in actions:
            tk.Button(dialog, text=text,
                    command=lambda a=action: self.do_investigation(a, dialog),
                    font=self.fonts['small'],
                    bg=self.colors['accent'],
                    fg='white',
                    width=20).pack(pady=3)
    
    def do_investigation(self, action, dialog):
        """Wykonuje akcję śledczą."""
        dialog.destroy()
        
        if self.quest_integration:
            result = self.quest_integration.handle_player_action(action, "general")
            
            for msg in result.get("messages", []):
                self.append_text(f"\n{msg}\n", 'quest')
            
            if result.get("success"):
                self.update_quest_ui()
    
    def resolve_quest(self):
        """Rozwiązuje questa."""
        if not self.selected_quest:
            messagebox.showinfo("Info", "Wybierz najpierw questa do rozwiązania")
            return
        
        # Pobierz dostępne gałęzie
        branches = self.quest_engine.get_available_branches(self.selected_quest)
        if not branches:
            messagebox.showinfo("Info", "Brak dostępnych rozwiązań. Zbierz więcej informacji.")
            return
        
        # Dialog wyboru rozwiązania
        dialog = tk.Toplevel(self.root)
        dialog.title("Rozwiązanie")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Wybierz sposób rozwiązania:",
                font=self.fonts['normal'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        for branch in branches:
            frame = tk.Frame(dialog, bg=self.colors['panel'])
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Button(frame, text=branch['description'],
                    command=lambda b=branch['id']: self.do_resolution(b, dialog),
                    font=self.fonts['small'],
                    bg=self.colors['stamina'],
                    fg='white',
                    wraplength=350).pack(fill=tk.X)
            
            # Pokaż wymagania
            if branch.get('requirements'):
                req_text = "Wymaga: " + ", ".join(
                    f"{k}: {v}" for k, v in branch['requirements'].items()
                )
                tk.Label(frame, text=req_text,
                        font=self.fonts['small'],
                        bg=self.colors['panel'],
                        fg=self.colors['text'],
                        wraplength=350).pack()
    
    def do_resolution(self, branch_id, dialog):
        """Wykonuje rozwiązanie questa."""
        dialog.destroy()
        
        result = self.quest_engine.resolve_quest(self.selected_quest, branch_id)
        
        if result['success']:
            self.append_text(f"\n[QUEST ROZWIĄZANY] {result.get('dialogue', '')}\n", 'success')
            
            # Pokaż efekty
            if result.get('immediate_effects'):
                self.append_text("Natychmiastowe efekty:\n", 'quest')
                for key, value in result['immediate_effects'].items():
                    self.append_text(f"  • {key}: {value}\n", 'normal')
            
            if result.get('scheduled_effects'):
                self.append_text(
                    f"Zaplanowano {result['scheduled_effects']} przyszłych konsekwencji.\n",
                    'consequence'
                )
            
            # Pokaż wpływ moralny
            moral = result.get('moral_impact', 0)
            if moral != 0:
                moral_text = "Dobry" if moral > 0 else "Zły"
                self.append_text(f"Wpływ moralny: {moral_text} ({moral})\n", 'quest')
        else:
            self.append_text(f"\n[NIEPOWODZENIE] {result.get('reason', 'Nie udało się')}\n", 'error')
        
        self.update_quest_ui()
    
    def ignore_quest(self):
        """Ignoruje questa."""
        if not self.selected_quest:
            messagebox.showinfo("Info", "Wybierz najpierw questa do zignorowania")
            return
        
        if messagebox.askyesno("Potwierdź", 
                              "Zignorowanie questa może mieć poważne konsekwencje. Kontynuować?"):
            quest = self.quest_engine.active_quests.get(self.selected_quest)
            if quest:
                result = quest.fail("Gracz zignorował sytuację", self.quest_engine.world_state)
                self.append_text(
                    f"\n[QUEST ZIGNOROWANY] {result.get('dialogue', 'Twoja bezczynność będzie miała konsekwencje...')}\n",
                    'consequence'
                )
                
                # Pokaż konsekwencje
                if result.get('consequences'):
                    self.append_text("Konsekwencje ignorowania:\n", 'error')
                    for key, value in result['consequences'].items():
                        self.append_text(f"  • {key}: {value}\n", 'normal')
                
                self.update_quest_ui()
    
    def run(self):
        """Uruchamia główną pętlę."""
        self.root.mainloop()


if __name__ == "__main__":
    print("Uruchamianie zintegrowanego interfejsu graficznego...")
    gui = IntegratedRPGInterface()
    gui.run()