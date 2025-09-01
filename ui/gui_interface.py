"""
Prawdziwy graficzny interfejs użytkownika dla gry Droga Szamana.
Używa tkinter do stworzenia okna z panelami jak w klasycznych RPG.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import font as tkfont
import threading
import queue
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Import systemów gry
from core.game_state import GameState, GameMode
from ui.commands import CommandParser
from player.character import CharacterState


class GamePanel(Enum):
    """Typy paneli w interfejsie."""
    MAIN_VIEW = "main"
    INVENTORY = "inventory"
    CHARACTER = "character"
    MAP = "map"
    JOURNAL = "journal"
    SETTINGS = "settings"


class RPGInterface:
    """
    Pełny graficzny interfejs gry w stylu klasycznych RPG.
    Okno podzielone na panele z przyciskami, mapą, ekwipunkiem itp.
    """
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.command_parser = CommandParser(game_state)
        self.command_queue = queue.Queue()
        self.update_queue = queue.Queue()
        
        # Główne okno
        self.root = tk.Tk()
        self.root.title("Droga Szamana RPG")
        self.root.geometry("1280x800")
        self.root.configure(bg='#1a1a1a')
        
        # Style
        self.setup_styles()
        
        # Panele
        self.current_panel = GamePanel.MAIN_VIEW
        self.panels = {}
        
        # Buduj interfejs
        self.build_interface()
        
        # Stan gry
        self.in_combat = False
        self.current_target = None
        self.dialogue_active = False
        
        # Automatyczna aktualizacja
        self.update_timer = None
        self.start_auto_update()
        
    def setup_styles(self):
        """Konfiguruje style dla ładnego wyglądu."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Ciemny motyw
        self.colors = {
            'bg': '#1a1a1a',
            'panel': '#2a2a2a',
            'text': '#e0e0e0',
            'accent': '#4a9eff',
            'health': '#ff4444',
            'mana': '#4444ff',
            'stamina': '#44ff44',
            'gold': '#ffdd44',
            'border': '#3a3a3a'
        }
        
        # Fonty
        self.fonts = {
            'title': tkfont.Font(family="Arial", size=16, weight="bold"),
            'header': tkfont.Font(family="Arial", size=12, weight="bold"),
            'normal': tkfont.Font(family="Arial", size=10),
            'small': tkfont.Font(family="Arial", size=9),
            'console': tkfont.Font(family="Consolas", size=10)
        }
        
        # Style przycisków
        self.style.configure('Game.TButton',
                           background=self.colors['panel'],
                           foreground=self.colors['text'],
                           borderwidth=1,
                           relief='raised',
                           padding=(10, 5))
        
        self.style.map('Game.TButton',
                      background=[('active', self.colors['accent'])],
                      foreground=[('active', 'white')])
        
    def build_interface(self):
        """Buduje główny interfejs gry."""
        # Główny kontener
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Górny pasek - status gracza
        self.build_status_bar(main_container)
        
        # Środkowa część - 3 kolumny
        middle_frame = tk.Frame(main_container, bg=self.colors['bg'])
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Lewa kolumna - mapa i eksploracja
        self.build_left_panel(middle_frame)
        
        # Środkowa kolumna - główny widok gry
        self.build_center_panel(middle_frame)
        
        # Prawa kolumna - ekwipunek i statystyki
        self.build_right_panel(middle_frame)
        
        # Dolny pasek - szybkie akcje
        self.build_action_bar(main_container)
        
    def build_status_bar(self, parent):
        """Buduje górny pasek statusu."""
        status_frame = tk.Frame(parent, bg=self.colors['panel'], height=80)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        # Portret postaci
        portrait = tk.Frame(status_frame, bg=self.colors['border'], width=70, height=70)
        portrait.pack(side=tk.LEFT, padx=5, pady=5)
        
        portrait_label = tk.Label(portrait, text="👤", font=("Arial", 30), 
                                 bg=self.colors['border'], fg=self.colors['text'])
        portrait_label.pack(expand=True)
        
        # Paski życia, many, staminy
        bars_frame = tk.Frame(status_frame, bg=self.colors['panel'])
        bars_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Życie
        self.health_var = tk.StringVar(value="100/100")
        health_frame = self.create_stat_bar(bars_frame, "Życie", self.health_var, 
                                           self.colors['health'], 100, 100)
        health_frame.pack(fill=tk.X, pady=2)
        
        # Mana
        self.mana_var = tk.StringVar(value="50/50")
        mana_frame = self.create_stat_bar(bars_frame, "Mana", self.mana_var,
                                         self.colors['mana'], 50, 50)
        mana_frame.pack(fill=tk.X, pady=2)
        
        # Stamina
        self.stamina_var = tk.StringVar(value="100/100")
        stamina_frame = self.create_stat_bar(bars_frame, "Stamina", self.stamina_var,
                                            self.colors['stamina'], 100, 100)
        stamina_frame.pack(fill=tk.X, pady=2)
        
        # Info dodatkowe
        info_frame = tk.Frame(status_frame, bg=self.colors['panel'])
        info_frame.pack(side=tk.RIGHT, padx=10)
        
        # Złoto
        self.gold_label = tk.Label(info_frame, text="💰 0 złota",
                                  font=self.fonts['header'],
                                  bg=self.colors['panel'],
                                  fg=self.colors['gold'])
        self.gold_label.pack()
        
        # Lokacja
        self.location_label = tk.Label(info_frame, text="📍 Cela więzienna",
                                      font=self.fonts['normal'],
                                      bg=self.colors['panel'],
                                      fg=self.colors['text'])
        self.location_label.pack()
        
        # Czas
        self.time_label = tk.Label(info_frame, text="🕐 Dzień 1, 07:00",
                                   font=self.fonts['small'],
                                   bg=self.colors['panel'],
                                   fg=self.colors['text'])
        self.time_label.pack()
        
    def create_stat_bar(self, parent, label, var, color, current, maximum):
        """Tworzy pasek dla statystyki (HP/MP/Stamina)."""
        frame = tk.Frame(parent, bg=self.colors['panel'])
        
        # Label
        label_widget = tk.Label(frame, text=label, font=self.fonts['small'],
                               bg=self.colors['panel'], fg=self.colors['text'])
        label_widget.pack(side=tk.LEFT, padx=(0, 5))
        
        # Progress bar
        progress = ttk.Progressbar(frame, length=150, mode='determinate',
                                  style='Health.Horizontal.TProgressbar')
        progress['maximum'] = maximum
        progress['value'] = current
        progress.pack(side=tk.LEFT, padx=5)
        
        # Wartość tekstowa
        value_label = tk.Label(frame, textvariable=var, font=self.fonts['small'],
                              bg=self.colors['panel'], fg=color)
        value_label.pack(side=tk.LEFT, padx=5)
        
        return frame
    
    def build_left_panel(self, parent):
        """Buduje lewy panel z mapą."""
        left_frame = tk.Frame(parent, bg=self.colors['panel'], width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # Tytuł
        title = tk.Label(left_frame, text="MAPA OKOLICY",
                        font=self.fonts['header'],
                        bg=self.colors['accent'],
                        fg='white')
        title.pack(fill=tk.X)
        
        # Canvas na mapę
        self.map_canvas = tk.Canvas(left_frame, bg='#1a1a1a',
                                   highlightthickness=0)
        self.map_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Rysuj przykładową mapę
        self.draw_mini_map()
        
        # Przyciski nawigacji
        nav_frame = tk.Frame(left_frame, bg=self.colors['panel'])
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Układ przycisków kierunkowych
        tk.Button(nav_frame, text="⬆", width=3, command=lambda: self.move("północ"),
                 font=("Arial", 16), bg=self.colors['panel'], fg=self.colors['text']
                ).grid(row=0, column=1, padx=2, pady=2)
        
        tk.Button(nav_frame, text="⬅", width=3, command=lambda: self.move("zachód"),
                 font=("Arial", 16), bg=self.colors['panel'], fg=self.colors['text']
                ).grid(row=1, column=0, padx=2, pady=2)
        
        tk.Button(nav_frame, text="⬇", width=3, command=lambda: self.move("południe"),
                 font=("Arial", 16), bg=self.colors['panel'], fg=self.colors['text']
                ).grid(row=1, column=1, padx=2, pady=2)
        
        tk.Button(nav_frame, text="➡", width=3, command=lambda: self.move("wschód"),
                 font=("Arial", 16), bg=self.colors['panel'], fg=self.colors['text']
                ).grid(row=1, column=2, padx=2, pady=2)
        
        # Przycisk rozejrzyj się
        tk.Button(left_frame, text="👀 Rozejrzyj się",
                 command=lambda: self.execute_command("rozejrzyj"),
                 bg=self.colors['accent'], fg='white',
                 font=self.fonts['normal']).pack(fill=tk.X, padx=5, pady=5)
        
    def draw_mini_map(self):
        """Rysuje minimapę lokacji."""
        # Wyczyść canvas
        self.map_canvas.delete("all")
        
        # Rozmiary
        width = 290
        height = 200
        
        # Tło
        self.map_canvas.create_rectangle(0, 0, width, height, 
                                        fill='#0a0a0a', outline='#3a3a3a')
        
        # Przykładowa mapa więzienia (3x3 pokoje)
        room_size = 60
        rooms = [
            (1, 0, "Korytarz"),
            (0, 1, "Cela 2"),
            (1, 1, "Cela 1", True),  # Aktualna lokacja
            (2, 1, "Cela 3"),
            (1, 2, "Dziedziniec")
        ]
        
        for x, y, name, *current in rooms:
            rx = 50 + x * (room_size + 10)
            ry = 20 + y * (room_size + 10)
            
            # Kolor pokoju
            if current:
                color = self.colors['accent']
                text_color = 'white'
            else:
                color = '#2a2a2a'
                text_color = '#888888'
            
            # Rysuj pokój
            self.map_canvas.create_rectangle(rx, ry, rx + room_size, ry + room_size,
                                            fill=color, outline='#4a4a4a', width=2)
            
            # Nazwa pokoju
            self.map_canvas.create_text(rx + room_size//2, ry + room_size//2,
                                       text=name, fill=text_color,
                                       font=("Arial", 8))
        
        # Połączenia między pokojami
        connections = [
            (1, 0, 1, 1),  # Korytarz - Cela 1
            (0, 1, 1, 1),  # Cela 2 - Cela 1
            (1, 1, 2, 1),  # Cela 1 - Cela 3
            (1, 1, 1, 2),  # Cela 1 - Dziedziniec
        ]
        
        for x1, y1, x2, y2 in connections:
            cx1 = 50 + x1 * (room_size + 10) + room_size // 2
            cy1 = 20 + y1 * (room_size + 10) + room_size // 2
            cx2 = 50 + x2 * (room_size + 10) + room_size // 2
            cy2 = 20 + y2 * (room_size + 10) + room_size // 2
            
            self.map_canvas.create_line(cx1, cy1, cx2, cy2,
                                       fill='#666666', width=2)
    
    def build_center_panel(self, parent):
        """Buduje centralny panel z głównym widokiem gry."""
        center_frame = tk.Frame(parent, bg=self.colors['panel'])
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Główne okno tekstowe - opis lokacji i wydarzenia
        text_frame = tk.Frame(center_frame, bg=self.colors['panel'])
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tytuł
        title = tk.Label(text_frame, text="GŁÓWNY WIDOK",
                        font=self.fonts['header'],
                        bg=self.colors['accent'],
                        fg='white')
        title.pack(fill=tk.X)
        
        # Tekst gry z scrollbarem
        self.game_text = scrolledtext.ScrolledText(text_frame,
                                                  wrap=tk.WORD,
                                                  font=self.fonts['console'],
                                                  bg='#0a0a0a',
                                                  fg=self.colors['text'],
                                                  insertbackground=self.colors['accent'],
                                                  height=20)
        self.game_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel interakcji (NPC, przedmioty w lokacji)
        interaction_frame = tk.LabelFrame(center_frame, text="W LOKACJI",
                                         font=self.fonts['header'],
                                         bg=self.colors['panel'],
                                         fg=self.colors['text'])
        interaction_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # NPCe
        npc_frame = tk.Frame(interaction_frame, bg=self.colors['panel'])
        npc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(npc_frame, text="Osoby:", font=self.fonts['normal'],
                bg=self.colors['panel'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.npc_buttons = tk.Frame(npc_frame, bg=self.colors['panel'])
        self.npc_buttons.pack(side=tk.LEFT, padx=10)
        
        # Przykładowe NPCe
        self.update_npcs(["Strażnik", "Więzień Piotr", "Szczur"])
        
        # Przedmioty
        items_frame = tk.Frame(interaction_frame, bg=self.colors['panel'])
        items_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(items_frame, text="Przedmioty:", font=self.fonts['normal'],
                bg=self.colors['panel'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.item_buttons = tk.Frame(items_frame, bg=self.colors['panel'])
        self.item_buttons.pack(side=tk.LEFT, padx=10)
        
        # Input gracza
        input_frame = tk.Frame(center_frame, bg=self.colors['panel'])
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(input_frame, text=">", font=self.fonts['console'],
                bg=self.colors['panel'], fg=self.colors['accent']).pack(side=tk.LEFT)
        
        self.input_entry = tk.Entry(input_frame, font=self.fonts['console'],
                                   bg='#0a0a0a', fg=self.colors['text'],
                                   insertbackground=self.colors['accent'])
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_entry.bind('<Return>', self.on_enter_pressed)
        
        tk.Button(input_frame, text="Wyślij",
                 command=self.on_enter_pressed,
                 bg=self.colors['accent'], fg='white').pack(side=tk.RIGHT)
        
    def build_right_panel(self, parent):
        """Buduje prawy panel z ekwipunkiem i statystykami."""
        right_frame = tk.Frame(parent, bg=self.colors['panel'], width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_frame.pack_propagate(False)
        
        # Zakładki
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Zakładka Ekwipunek
        inv_frame = tk.Frame(notebook, bg=self.colors['panel'])
        notebook.add(inv_frame, text="Ekwipunek")
        
        # Wyposażone przedmioty
        equipped_frame = tk.LabelFrame(inv_frame, text="WYPOSAŻONE",
                                      font=self.fonts['normal'],
                                      bg=self.colors['panel'],
                                      fg=self.colors['text'])
        equipped_frame.pack(fill=tk.X, padx=5, pady=5)
        
        equipment_slots = [
            ("Głowa:", "Brak"),
            ("Broń:", "Pięści"),
            ("Zbroja:", "Łachmany więzienne"),
            ("Buty:", "Brak")
        ]
        
        for slot, item in equipment_slots:
            row = tk.Frame(equipped_frame, bg=self.colors['panel'])
            row.pack(fill=tk.X, padx=5, pady=2)
            
            tk.Label(row, text=slot, width=10, anchor='w',
                    font=self.fonts['small'],
                    bg=self.colors['panel'],
                    fg=self.colors['text']).pack(side=tk.LEFT)
            
            tk.Label(row, text=item, anchor='w',
                    font=self.fonts['small'],
                    bg=self.colors['panel'],
                    fg='#888888').pack(side=tk.LEFT)
        
        # Lista przedmiotów
        inv_list_frame = tk.LabelFrame(inv_frame, text="PRZEDMIOTY",
                                       font=self.fonts['normal'],
                                       bg=self.colors['panel'],
                                       fg=self.colors['text'])
        inv_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollowana lista
        inv_scroll = tk.Scrollbar(inv_list_frame)
        inv_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.inventory_list = tk.Listbox(inv_list_frame,
                                        yscrollcommand=inv_scroll.set,
                                        font=self.fonts['small'],
                                        bg='#1a1a1a',
                                        fg=self.colors['text'],
                                        selectbackground=self.colors['accent'])
        self.inventory_list.pack(fill=tk.BOTH, expand=True)
        inv_scroll.config(command=self.inventory_list.yview)
        
        # Przyciski akcji dla przedmiotów
        inv_buttons = tk.Frame(inv_frame, bg=self.colors['panel'])
        inv_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(inv_buttons, text="Użyj",
                 command=self.use_item,
                 bg=self.colors['accent'], fg='white').pack(side=tk.LEFT, padx=2)
        
        tk.Button(inv_buttons, text="Wyposarz",
                 command=self.equip_item,
                 bg=self.colors['panel'], fg=self.colors['text']).pack(side=tk.LEFT, padx=2)
        
        tk.Button(inv_buttons, text="Wyrzuć",
                 command=self.drop_item,
                 bg='#aa4444', fg='white').pack(side=tk.LEFT, padx=2)
        
        # Zakładka Statystyki
        stats_frame = tk.Frame(notebook, bg=self.colors['panel'])
        notebook.add(stats_frame, text="Postać")
        
        # Statystyki postaci
        stats_label = tk.Label(stats_frame, text="STATYSTYKI POSTACI",
                              font=self.fonts['header'],
                              bg=self.colors['accent'],
                              fg='white')
        stats_label.pack(fill=tk.X)
        
        stats_list = tk.Frame(stats_frame, bg=self.colors['panel'])
        stats_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        character_stats = [
            ("Siła:", "10"),
            ("Zręczność:", "12"),
            ("Wytrzymałość:", "8"),
            ("Inteligencja:", "14"),
            ("Mądrość:", "11"),
            ("Charyzma:", "9"),
            ("", ""),
            ("Obrona:", "2"),
            ("Atak:", "5-8"),
            ("Szybkość:", "10"),
            ("", ""),
            ("Poziom bólu:", "0%"),
            ("Głód:", "20%"),
            ("Zmęczenie:", "10%")
        ]
        
        for stat, value in character_stats:
            if stat:  # Pomiń puste linie
                row = tk.Frame(stats_list, bg=self.colors['panel'])
                row.pack(fill=tk.X, pady=2)
                
                tk.Label(row, text=stat, width=15, anchor='w',
                        font=self.fonts['normal'],
                        bg=self.colors['panel'],
                        fg=self.colors['text']).pack(side=tk.LEFT)
                
                tk.Label(row, text=value, anchor='w',
                        font=self.fonts['normal'],
                        bg=self.colors['panel'],
                        fg=self.colors['accent']).pack(side=tk.LEFT)
            else:
                # Separator
                tk.Frame(stats_list, height=10, bg=self.colors['panel']).pack()
        
        # Zakładka Dziennik
        journal_frame = tk.Frame(notebook, bg=self.colors['panel'])
        notebook.add(journal_frame, text="Dziennik")
        
        # Lista questów
        quest_label = tk.Label(journal_frame, text="AKTYWNE ZADANIA",
                             font=self.fonts['header'],
                             bg=self.colors['accent'],
                             fg='white')
        quest_label.pack(fill=tk.X)
        
        self.quest_list = tk.Listbox(journal_frame,
                                    font=self.fonts['small'],
                                    bg='#1a1a1a',
                                    fg=self.colors['text'],
                                    height=10)
        self.quest_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Przykładowe questy
        self.quest_list.insert(tk.END, "🎯 Ucieczka z więzienia")
        self.quest_list.insert(tk.END, "📜 Znajdź sposób na otwarcie celi")
        self.quest_list.insert(tk.END, "🔍 Zbadaj słaby punkt w murze")
        
    def build_action_bar(self, parent):
        """Buduje dolny pasek szybkich akcji."""
        action_frame = tk.Frame(parent, bg=self.colors['panel'], height=80)
        action_frame.pack(fill=tk.X, pady=(5, 0))
        action_frame.pack_propagate(False)
        
        # Przyciski szybkich akcji
        actions = [
            ("⚔️ Atakuj", self.attack),
            ("🛡️ Broń się", self.defend),
            ("💬 Rozmawiaj", self.talk),
            ("🔍 Przeszukaj", self.search),
            ("🎒 Ekwipunek", self.toggle_inventory),
            ("🗺️ Mapa", self.toggle_map),
            ("💤 Odpocznij", self.rest),
            ("💾 Zapisz", self.save_game),
            ("⚙️ Opcje", self.show_settings),
            ("❌ Wyjście", self.quit_game)
        ]
        
        for i, (text, command) in enumerate(actions):
            btn = tk.Button(action_frame, text=text,
                          command=command,
                          width=12,
                          font=self.fonts['normal'],
                          bg=self.colors['panel'],
                          fg=self.colors['text'],
                          relief=tk.RAISED,
                          bd=2)
            btn.pack(side=tk.LEFT, padx=2, pady=10)
            
            # Tooltip z numerem klawisza
            self.create_tooltip(btn, f"Klawisz: {i+1}")
    
    def create_tooltip(self, widget, text):
        """Tworzy tooltip dla widgetu."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text,
                           background="#ffffe0",
                           relief=tk.SOLID,
                           borderwidth=1,
                           font=self.fonts['small'])
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    # === FUNKCJE AKCJI ===
    
    def execute_command(self, command: str):
        """Wykonuje komendę gry."""
        if not command:
            return
            
        # Wyświetl komendę w oknie gry
        self.append_text(f"\n> {command}\n", 'command')
        
        # Wykonaj przez parser
        success, message = self.command_parser.parse_and_execute(command)
        
        # Wyświetl rezultat
        if message:
            self.append_text(message + "\n", 'success' if success else 'error')
        
        # Aktualizuj interfejs
        self.update_display()
    
    def append_text(self, text: str, tag: str = 'normal'):
        """Dodaje tekst do głównego okna."""
        self.game_text.config(state=tk.NORMAL)
        self.game_text.insert(tk.END, text)
        
        # Kolory dla różnych tagów
        if tag == 'command':
            self.game_text.tag_add('command', 'end-2l', 'end-1l')
            self.game_text.tag_config('command', foreground=self.colors['accent'])
        elif tag == 'error':
            self.game_text.tag_add('error', 'end-2l', 'end-1l')
            self.game_text.tag_config('error', foreground=self.colors['health'])
        elif tag == 'success':
            self.game_text.tag_add('success', 'end-2l', 'end-1l')
            self.game_text.tag_config('success', foreground=self.colors['stamina'])
        
        self.game_text.config(state=tk.DISABLED)
        self.game_text.see(tk.END)
    
    def move(self, direction: str):
        """Porusza gracza w danym kierunku."""
        self.execute_command(f"idź {direction}")
    
    def attack(self):
        """Atakuje cel."""
        if self.current_target:
            self.execute_command(f"atakuj {self.current_target}")
        else:
            # Pokaż dialog wyboru celu
            self.show_target_dialog()
    
    def defend(self):
        """Przyjmuje postawę obronną."""
        self.execute_command("broń")
    
    def talk(self):
        """Rozpoczyna rozmowę z NPC."""
        # Pokaż dialog wyboru NPC
        self.show_npc_dialog()
    
    def search(self):
        """Przeszukuje lokację."""
        self.execute_command("przeszukaj")
    
    def rest(self):
        """Odpoczywa."""
        self.execute_command("odpocznij")
    
    def use_item(self):
        """Używa wybranego przedmiotu."""
        selection = self.inventory_list.curselection()
        if selection:
            item = self.inventory_list.get(selection[0])
            self.execute_command(f"użyj {item}")
    
    def equip_item(self):
        """Wyposaża przedmiot."""
        selection = self.inventory_list.curselection()
        if selection:
            item = self.inventory_list.get(selection[0])
            self.execute_command(f"załóż {item}")
    
    def drop_item(self):
        """Wyrzuca przedmiot."""
        selection = self.inventory_list.curselection()
        if selection:
            item = self.inventory_list.get(selection[0])
            if messagebox.askyesno("Potwierdź", f"Czy na pewno wyrzucić {item}?"):
                self.execute_command(f"wyrzuć {item}")
    
    def toggle_inventory(self):
        """Przełącza widok ekwipunku."""
        # TODO: Przełącz zakładkę na ekwipunek
        pass
    
    def toggle_map(self):
        """Przełącza widok mapy."""
        # TODO: Pokaż pełną mapę
        pass
    
    def save_game(self):
        """Zapisuje grę."""
        slot = messagebox.askinteger("Zapisz grę", "Podaj numer slotu (1-5):", 
                                    minvalue=1, maxvalue=5)
        if slot:
            self.execute_command(f"zapisz {slot}")
            messagebox.showinfo("Sukces", f"Gra zapisana w slocie {slot}")
    
    def show_settings(self):
        """Pokazuje okno ustawień."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Ustawienia")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.colors['panel'])
        
        tk.Label(settings_window, text="USTAWIENIA GRY",
                font=self.fonts['header'],
                bg=self.colors['accent'],
                fg='white').pack(fill=tk.X)
        
        # TODO: Dodaj opcje ustawień
        
    def quit_game(self):
        """Wyjście z gry."""
        if messagebox.askyesno("Wyjście", "Czy na pewno chcesz wyjść z gry?"):
            self.root.quit()
    
    def on_enter_pressed(self, event=None):
        """Obsługuje wciśnięcie Enter w polu input."""
        command = self.input_entry.get()
        if command:
            self.execute_command(command)
            self.input_entry.delete(0, tk.END)
    
    def update_npcs(self, npcs: List[str]):
        """Aktualizuje listę NPCów w lokacji."""
        # Wyczyść stare przyciski
        for widget in self.npc_buttons.winfo_children():
            widget.destroy()
        
        # Dodaj nowe
        for npc in npcs[:3]:  # Max 3 NPCe widoczne
            btn = tk.Button(self.npc_buttons, text=npc,
                          command=lambda n=npc: self.interact_with_npc(n),
                          font=self.fonts['small'],
                          bg=self.colors['panel'],
                          fg=self.colors['text'])
            btn.pack(side=tk.LEFT, padx=2)
    
    def interact_with_npc(self, npc_name: str):
        """Interakcja z NPC."""
        # Menu kontekstowe
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=f"Rozmawiaj z {npc_name}",
                        command=lambda: self.execute_command(f"rozmawiaj {npc_name}"))
        menu.add_command(label=f"Zbadaj {npc_name}",
                        command=lambda: self.execute_command(f"zbadaj {npc_name}"))
        
        if "Szczur" in npc_name or "potwór" in npc_name.lower():
            menu.add_separator()
            menu.add_command(label=f"Atakuj {npc_name}",
                           command=lambda: self.execute_command(f"atakuj {npc_name}"))
        
        # Pokaż menu w pozycji kursora
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
    
    def show_target_dialog(self):
        """Pokazuje dialog wyboru celu ataku."""
        # TODO: Pobierz listę celów z game_state
        targets = ["Szczur", "Strażnik"]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz cel")
        dialog.geometry("300x200")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Wybierz cel ataku:",
                font=self.fonts['header'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        for target in targets:
            tk.Button(dialog, text=target,
                    command=lambda t=target: [self.execute_command(f"atakuj {t}"),
                                             dialog.destroy()],
                    width=20,
                    bg=self.colors['accent'],
                    fg='white').pack(pady=5)
    
    def show_npc_dialog(self):
        """Pokazuje dialog wyboru NPC do rozmowy."""
        # TODO: Pobierz listę NPCów z game_state
        npcs = ["Strażnik", "Więzień Piotr"]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz rozmówcę")
        dialog.geometry("300x200")
        dialog.configure(bg=self.colors['panel'])
        
        tk.Label(dialog, text="Z kim chcesz porozmawiać?",
                font=self.fonts['header'],
                bg=self.colors['panel'],
                fg=self.colors['text']).pack(pady=10)
        
        for npc in npcs:
            tk.Button(dialog, text=npc,
                    command=lambda n=npc: [self.execute_command(f"rozmawiaj {n}"),
                                          dialog.destroy()],
                    width=20,
                    bg=self.colors['accent'],
                    fg='white').pack(pady=5)
    
    def update_display(self):
        """Aktualizuje cały interfejs na podstawie stanu gry."""
        if not self.game_state.player:
            return
        
        # Aktualizuj paski statusu
        player = self.game_state.player
        self.health_var.set(f"{player.health}/{player.max_health}")
        
        # Mana - tylko jeśli postać ją ma
        if hasattr(player, 'mana'):
            self.mana_var.set(f"{player.mana}/{player.max_mana}")
        else:
            self.mana_var.set("N/A")
        
        self.stamina_var.set(f"{player.stamina}/{player.max_stamina}")
        
        # Aktualizuj złoto
        if hasattr(player, 'gold'):
            gold = player.gold
        elif hasattr(player, 'equipment') and hasattr(player.equipment, 'gold'):
            gold = player.equipment.gold
        else:
            gold = 0
        self.gold_label.config(text=f"💰 {gold} złota")
        
        # Aktualizuj lokację
        if hasattr(player, 'current_location'):
            self.location_label.config(text=f"📍 {player.current_location}")
        elif hasattr(player, 'location'):
            self.location_label.config(text=f"📍 {player.location}")
        
        # Aktualizuj czas
        time_str = f"🕐 Dzień {self.game_state.day}, {self.game_state.game_time//60:02d}:{self.game_state.game_time%60:02d}"
        self.time_label.config(text=time_str)
        
        # Aktualizuj ekwipunek
        self.inventory_list.delete(0, tk.END)
        if hasattr(player, 'equipment') and hasattr(player.equipment, 'items'):
            for item in player.equipment.items:
                if isinstance(item, dict):
                    self.inventory_list.insert(tk.END, item.get('name', 'Nieznany przedmiot'))
                else:
                    self.inventory_list.insert(tk.END, str(item))
        elif hasattr(player, 'inventory'):
            for item in player.inventory:
                if isinstance(item, dict):
                    self.inventory_list.insert(tk.END, item.get('name', 'Nieznany przedmiot'))
                else:
                    self.inventory_list.insert(tk.END, str(item))
    
    def start_auto_update(self):
        """Startuje automatyczną aktualizację interfejsu."""
        def update():
            self.update_display()
            self.update_timer = self.root.after(1000, update)  # Co sekundę
        
        update()
    
    def run(self):
        """Uruchamia główną pętlę interfejsu."""
        # Wstępna aktualizacja
        self.update_display()
        
        # Powitanie
        self.append_text("=== DROGA SZAMANA RPG ===\n", 'success')
        self.append_text("Witaj w graficznym interfejsie gry!\n\n")
        self.append_text("Użyj przycisków lub wpisz komendy poniżej.\n")
        self.append_text("Kliknij na NPCa lub przedmiot prawym przyciskiem dla opcji.\n\n")
        
        # Pokaż początkową lokację
        self.execute_command("rozejrzyj")
        
        # Uruchom główną pętlę
        self.root.mainloop()


def launch_gui(game_state: GameState):
    """Uruchamia graficzny interfejs gry."""
    gui = RPGInterface(game_state)
    gui.run()