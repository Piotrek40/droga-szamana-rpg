#!/usr/bin/env python3
"""
Uproszczony graficzny interfejs dla Droga Szamana RPG.
Stabilna wersja z podstawowymi funkcjami.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.game_state import game_state
from ui.commands import CommandParser


class SimpleRPGInterface:
    """Prosty ale funkcjonalny graficzny interfejs gry."""
    
    def __init__(self):
        # Inicjalizuj grę
        print("Inicjalizacja gry...")
        game_state.init_game("Bohater")
        self.game_state = game_state
        self.command_parser = CommandParser(game_state)
        
        # Główne okno
        self.root = tk.Tk()
        self.root.title("Droga Szamana RPG - Graficzny Interfejs")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2a2a2a')
        
        # Buduj interfejs
        self.build_interface()
        
        # Początkowy stan
        self.execute_command("rozejrzyj")
        
    def build_interface(self):
        """Buduje interfejs użytkownika."""
        
        # === GÓRNY PANEL - STATUS ===
        status_frame = tk.Frame(self.root, bg='#1a1a1a', height=100)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        status_frame.pack_propagate(False)
        
        # Lewy status - HP/Stamina
        left_status = tk.Frame(status_frame, bg='#1a1a1a')
        left_status.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.hp_label = tk.Label(left_status, text="❤️ Życie: 100/100", 
                                font=("Arial", 12), bg='#1a1a1a', fg='#ff6666')
        self.hp_label.pack(anchor='w')
        
        self.stamina_label = tk.Label(left_status, text="⚡ Stamina: 100/100",
                                     font=("Arial", 12), bg='#1a1a1a', fg='#66ff66')
        self.stamina_label.pack(anchor='w')
        
        self.pain_label = tk.Label(left_status, text="😣 Ból: 0%",
                                  font=("Arial", 12), bg='#1a1a1a', fg='#ffaa66')
        self.pain_label.pack(anchor='w')
        
        # Prawy status - Lokacja/Czas
        right_status = tk.Frame(status_frame, bg='#1a1a1a')
        right_status.pack(side=tk.RIGHT, padx=20, pady=10)
        
        self.location_label = tk.Label(right_status, text="📍 Lokacja: Cela",
                                      font=("Arial", 12), bg='#1a1a1a', fg='#66aaff')
        self.location_label.pack(anchor='e')
        
        self.time_label = tk.Label(right_status, text="🕐 Czas: Dzień 1, 07:00",
                                  font=("Arial", 11), bg='#1a1a1a', fg='#aaaaaa')
        self.time_label.pack(anchor='e')
        
        self.gold_label = tk.Label(right_status, text="💰 Złoto: 0",
                                  font=("Arial", 11), bg='#1a1a1a', fg='#ffdd66')
        self.gold_label.pack(anchor='e')
        
        # === ŚRODKOWY PANEL - GRA ===
        middle_frame = tk.Frame(self.root, bg='#2a2a2a')
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Główne okno tekstowe
        self.game_text = scrolledtext.ScrolledText(middle_frame, 
                                                  wrap=tk.WORD,
                                                  font=("Consolas", 11),
                                                  bg='#1a1a1a',
                                                  fg='#e0e0e0',
                                                  height=20)
        self.game_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Panel wprowadzania komend
        input_frame = tk.Frame(middle_frame, bg='#2a2a2a')
        input_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(input_frame, text="Komenda:", font=("Arial", 11),
                bg='#2a2a2a', fg='#e0e0e0').pack(side=tk.LEFT, padx=5)
        
        self.input_entry = tk.Entry(input_frame, font=("Consolas", 11),
                                   bg='#1a1a1a', fg='#e0e0e0', width=50)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_entry.bind('<Return>', self.on_enter)
        self.input_entry.focus()
        
        send_btn = tk.Button(input_frame, text="Wyślij", 
                           command=self.on_enter,
                           bg='#4a9eff', fg='white',
                           font=("Arial", 10))
        send_btn.pack(side=tk.RIGHT, padx=5)
        
        # === DOLNY PANEL - SZYBKIE AKCJE ===
        action_frame = tk.Frame(self.root, bg='#1a1a1a')
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Przyciski ruchu
        move_frame = tk.LabelFrame(action_frame, text="Ruch", 
                                  font=("Arial", 10), bg='#1a1a1a', fg='#aaaaaa')
        move_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Układ kierunków
        btn_n = tk.Button(move_frame, text="⬆ Północ", width=10,
                         command=lambda: self.execute_command("idź północ"))
        btn_n.grid(row=0, column=1, padx=2, pady=2)
        
        btn_w = tk.Button(move_frame, text="⬅ Zachód", width=10,
                         command=lambda: self.execute_command("idź zachód"))
        btn_w.grid(row=1, column=0, padx=2, pady=2)
        
        btn_e = tk.Button(move_frame, text="Wschód ➡", width=10,
                         command=lambda: self.execute_command("idź wschód"))
        btn_e.grid(row=1, column=2, padx=2, pady=2)
        
        btn_s = tk.Button(move_frame, text="⬇ Południe", width=10,
                         command=lambda: self.execute_command("idź południe"))
        btn_s.grid(row=2, column=1, padx=2, pady=2)
        
        # Przyciski akcji
        action_btns = tk.Frame(action_frame, bg='#1a1a1a')
        action_btns.pack(side=tk.LEFT, padx=20, pady=5)
        
        actions = [
            ("👀 Rozejrzyj się", "rozejrzyj"),
            ("🔍 Przeszukaj", "przeszukaj"),
            ("💬 Rozmawiaj", self.show_npc_menu),
            ("⚔️ Atakuj", self.show_attack_menu),
            ("🎒 Ekwipunek", "ekwipunek"),
            ("📊 Status", "status"),
            ("💤 Odpocznij", "odpocznij"),
            ("💾 Zapisz", self.save_game),
        ]
        
        for i, (text, cmd) in enumerate(actions):
            if callable(cmd):
                btn = tk.Button(action_btns, text=text, width=12, command=cmd)
            else:
                btn = tk.Button(action_btns, text=text, width=12,
                              command=lambda c=cmd: self.execute_command(c))
            
            if i < 4:
                btn.grid(row=0, column=i, padx=2, pady=2)
            else:
                btn.grid(row=1, column=i-4, padx=2, pady=2)
        
        # Przycisk wyjścia
        quit_btn = tk.Button(action_frame, text="❌ Wyjście", 
                           command=self.quit_game,
                           bg='#aa4444', fg='white',
                           font=("Arial", 10))
        quit_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Aktualizuj status co sekundę
        self.update_status()
    
    def execute_command(self, command):
        """Wykonuje komendę gry."""
        # Wyświetl komendę
        self.append_text(f"\n> {command}\n", 'command')
        
        # Wykonaj
        success, message = self.command_parser.parse_and_execute(command)
        
        # Wyświetl wynik
        if message:
            self.append_text(message + "\n", 'normal' if success else 'error')
        
        # Aktualizuj status
        self.update_status()
    
    def append_text(self, text, style='normal'):
        """Dodaje tekst do okna gry."""
        self.game_text.config(state=tk.NORMAL)
        
        # Dodaj tekst
        start = self.game_text.index(tk.END)
        self.game_text.insert(tk.END, text)
        
        # Kolorowanie
        if style == 'command':
            self.game_text.tag_add('command', f"{start}", tk.END)
            self.game_text.tag_config('command', foreground='#4a9eff')
        elif style == 'error':
            self.game_text.tag_add('error', f"{start}", tk.END)
            self.game_text.tag_config('error', foreground='#ff6666')
        
        self.game_text.config(state=tk.DISABLED)
        self.game_text.see(tk.END)
    
    def on_enter(self, event=None):
        """Obsługa Enter w polu input."""
        command = self.input_entry.get()
        if command:
            self.execute_command(command)
            self.input_entry.delete(0, tk.END)
    
    def update_status(self):
        """Aktualizuje paski statusu."""
        if self.game_state.player:
            player = self.game_state.player
            
            # HP
            self.hp_label.config(text=f"❤️ Życie: {player.health}/{player.max_health}")
            
            # Stamina
            self.stamina_label.config(text=f"⚡ Stamina: {player.stamina}/{player.max_stamina}")
            
            # Ból
            pain = getattr(player, 'pain', 0)
            self.pain_label.config(text=f"😣 Ból: {pain}%")
            
            # Złoto
            gold = 0
            if hasattr(player, 'gold'):
                gold = player.gold
            elif hasattr(player, 'equipment'):
                gold = getattr(player.equipment, 'gold', 0)
            self.gold_label.config(text=f"💰 Złoto: {gold}")
            
            # Lokacja
            loc = getattr(player, 'current_location', getattr(player, 'location', 'Nieznana'))
            self.location_label.config(text=f"📍 Lokacja: {loc}")
        
        # Czas
        time_str = f"🕐 Czas: Dzień {self.game_state.day}, {self.game_state.game_time//60:02d}:{self.game_state.game_time%60:02d}"
        self.time_label.config(text=time_str)
        
        # Powtórz za sekundę
        self.root.after(1000, self.update_status)
    
    def show_npc_menu(self):
        """Pokazuje menu wyboru NPC do rozmowy."""
        # Pobierz NPCów z lokacji
        npcs = ["Strażnik", "Więzień Piotr", "Szczur"]  # Note: Pobierz z game_state
        
        if not npcs:
            self.append_text("Nikogo tu nie ma.\n", 'error')
            return
        
        # Okno dialogowe
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz rozmówcę")
        dialog.geometry("250x200")
        dialog.configure(bg='#2a2a2a')
        
        tk.Label(dialog, text="Z kim chcesz porozmawiać?",
                font=("Arial", 11), bg='#2a2a2a', fg='#e0e0e0').pack(pady=10)
        
        for npc in npcs:
            tk.Button(dialog, text=npc, width=20,
                    command=lambda n=npc: [
                        self.execute_command(f"rozmawiaj {n}"),
                        dialog.destroy()
                    ]).pack(pady=3)
    
    def show_attack_menu(self):
        """Pokazuje menu wyboru celu ataku."""
        targets = ["Szczur"]  # Note: Pobierz wrogów z lokacji
        
        if not targets:
            self.append_text("Nie ma tu wrogów.\n", 'error')
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz cel ataku")
        dialog.geometry("250x150")
        dialog.configure(bg='#2a2a2a')
        
        tk.Label(dialog, text="Kogo zaatakować?",
                font=("Arial", 11), bg='#2a2a2a', fg='#e0e0e0').pack(pady=10)
        
        for target in targets:
            tk.Button(dialog, text=target, width=20,
                    command=lambda t=target: [
                        self.execute_command(f"atakuj {t}"),
                        dialog.destroy()
                    ]).pack(pady=3)
    
    def save_game(self):
        """Zapisuje grę."""
        slot = tk.simpledialog.askinteger("Zapisz grę", "Podaj slot (1-5):",
                                         minvalue=1, maxvalue=5)
        if slot:
            self.execute_command(f"zapisz {slot}")
    
    def quit_game(self):
        """Wyjście z gry."""
        if messagebox.askyesno("Wyjście", "Czy na pewno chcesz wyjść?"):
            self.root.quit()
    
    def run(self):
        """Uruchamia główną pętlę."""
        self.append_text("=== DROGA SZAMANA RPG ===\n", 'command')
        self.append_text("Graficzny interfejs v1.0\n\n")
        self.append_text("Możesz używać przycisków lub wpisywać komendy.\n")
        self.append_text("Wpisz 'pomoc' aby zobaczyć listę komend.\n\n")
        
        self.root.mainloop()


if __name__ == "__main__":
    print("Uruchamianie graficznego interfejsu...")
    gui = SimpleRPGInterface()
    gui.run()