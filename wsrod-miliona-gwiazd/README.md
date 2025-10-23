# 🌌 Wśród Miliona Gwiazd

**Tekstowa gra strategiczna science fiction po polsku**

## 📖 Opis

"Wśród Miliona Gwiazd" to turowa gra strategiczna rozgrywana w galaktyce pełnej planet do odkrycia i kolonizacji. Jako komandor jednej z czterech frakcji, Twoim celem jest dominacja wśród gwiazd poprzez rozwój ekonomiczny, postęp technologiczny i siłę militarną.

## ✨ Główne cechy

- 🌍 **Dynamiczna galaktyka** - Losowo generowane planety z różnymi właściwościami
- 🏭 **System ekonomiczny** - Zarządzaj zasobami i rozwijaj infrastrukturę
- 🔬 **Drzewo technologiczne** - Badaj nowe technologie w 4 gałęziach
- 🚀 **System floty** - Buduj różne typy statków kosmicznych
- ⚔️ **System walki** - Taktyczne starcia między flotami
- 💾 **Zapis/odczyt** - Zapisuj postępy i wczytuj gry
- 🎮 **Intuicyjny interfejs** - Prosty tekstowy interfejs z czytelnymi komendami

## 🎯 Frakcje

### 1. Imperium
Potężna militarna monarchia
**Bonus:** +20% siły ataku flot

### 2. Federacja
Pokojowa unia planet
**Bonus:** +25% do produkcji zasobów

### 3. Korporacja
Mega-korporacja handlowa
**Bonus:** +30% przychodów z kredytów

### 4. Piraci
Wolni łowcy galaktyczni
**Bonus:** +2 do zasięgu ruchu flot

## 🎮 Jak grać

### Instalacja

```bash
# Sklonuj repozytorium
git clone https://github.com/TwojNick/wsrod-miliona-gwiazd.git
cd wsrod-miliona-gwiazd

# Uruchom grę
python3 main.py
```

### Wymagania

- Python 3.7 lub nowszy
- Brak dodatkowych zależności (czyste Python!)

### Podstawowe komendy

```
status              - Pokaż status gracza
planety             - Lista Twoich planet
planeta <nazwa>     - Szczegóły planety
mapa                - Mapa galaktyki
buduj <typ> <planeta> - Buduj budynek
badania             - Status badań
badaj <id>          - Rozpocznij badanie
floty               - Lista Twoich flot
następna            - Następna tura
zapisz              - Zapisz grę
pomoc               - Pomoc
koniec              - Zakończ grę
```

### Przykładowa rozgrywka

```bash
> status                          # Zobacz swoje zasoby
> planety                         # Lista Twoich planet
> planeta "Alpha Prime"           # Szczegóły planety
> buduj kopalnia "Alpha Prime"    # Zbuduj kopalnię
> badania                         # Zobacz dostępne technologie
> badaj lasery_1                  # Rozpocznij badanie laserów
> następna                        # Przejdź do następnej tury
```

## 🏗️ Budynki

| Budynek | Opis | Produkcja |
|---------|------|-----------|
| **Kopalnia** | Wydobywa metale | ⚙️ Metale |
| **Rafineria** | Przetwarza kryształy | 💎 Kryształy |
| **Elektrownia** | Produkuje energię | ⚡ Energia |
| **Laboratorium** | Przyspiesza badania | 🔬 Punkty badań |
| **Stocznia** | Buduje statki | 🚀 Produkcja floty |
| **Tarcza** | Obrona planetarna | 🛡️ Obrona |
| **Farma** | Zwiększa populację | 👥 Populacja |

## 🔬 Technologie

### Militarne
- Działa Laserowe I/II
- Pancerz Reaktywny
- Tarcze Energetyczne

### Ekonomiczne
- Zaawansowane Wydobycie
- Efektywna Rafinacja
- Ulepszona Fuzja

### Naukowe
- Komputery Kwantowe
- Sztuczna Inteligencja

### Eksploracyjne
- Napęd Jonowy/Warpowy
- Skanery Długozasięgowe
- Technologia Kolonizacyjna

## 🚀 Statki

| Typ | Zadanie | Parametry |
|-----|---------|-----------|
| **Zwiadowca** | Rekonesans | Szybki, słaby |
| **Niszczyciel** | Patrol | Średni atak |
| **Krążownik** | Wojna | Silny atak |
| **Pancernik** | Dominacja | Najsilniejszy |
| **Transportowiec** | Logistyka | Transport zasobów |
| **Kolonizator** | Ekspansja | Kolonizacja planet |

## 📊 Zasoby

- ⚙️ **Metale** - Podstawowy surowiec do budowy
- 💎 **Kryształy** - Zaawansowane komponenty technologiczne
- ⚡ **Energia** - Zasilanie budynków i systemów
- 💰 **Kredyty** - Uniwersalna waluta
- 👥 **Populacja** - Siła robocza cywilizacji
- ⚛️ **Antymateria** - Rzadki zasób do napędu FTL
- 🛢️ **Deuterium** - Paliwo do statków

## 🎯 Cele gry

### Zwycięstwo
Kontroluj 75% planet w galaktyce

### Porażka
Utrata wszystkich planet

## 🗺️ Struktura projektu

```
wsrod-miliona-gwiazd/
├── core/              # Silnik gry
│   ├── __init__.py
│   └── game_engine.py
├── systems/           # Systemy gry
│   ├── __init__.py
│   ├── resources.py   # System zasobów
│   ├── buildings.py   # Budynki
│   ├── technology.py  # Drzewo technologiczne
│   └── fleet.py       # Flota i walka
├── game/              # Logika gry
│   ├── __init__.py
│   ├── planet.py      # Planety
│   ├── galaxy.py      # Galaktyka
│   └── player.py      # Gracz
├── ui/                # Interfejs
│   ├── __init__.py
│   ├── interface.py   # Wyświetlanie
│   └── commands.py    # Komendy
├── data/              # Dane gry (puste na start)
├── saves/             # Zapisy gier
├── tests/             # Testy (TODO)
├── main.py            # Punkt wejścia
└── README.md          # Ten plik
```

## 🛠️ Rozwój

### Planowane funkcje

- [ ] System dyplomacji z AI
- [ ] Więcej typów planet
- [ ] Wydarzenia losowe
- [ ] Tryb kampanii
- [ ] Multiplayer (hotseat)
- [ ] Statystyki i osiągnięcia
- [ ] Eksploracja anomalii kosmicznych
- [ ] System handlu międzyplanetarnego

### Jak przyczynić się do rozwoju

1. Fork repozytorium
2. Utwórz branch dla swojej funkcji (`git checkout -b feature/nowa-funkcja`)
3. Commituj zmiany (`git commit -am 'Dodaj nową funkcję'`)
4. Push do brancha (`git push origin feature/nowa-funkcja`)
5. Utwórz Pull Request

## 📝 Licencja

MIT License - zobacz plik LICENSE

## 👨‍💻 Autor

Projekt stworzony przez Claude AI dla społeczności graczy strategicznych.

## 🌟 Podziękowania

Podziękowania dla wszystkich fanów klasycznych gier 4X:
- Master of Orion
- Stellaris
- Civilization
- Endless Space

---

**Niech gwiazdy prowadzą Cię do zwycięstwa, Komandorze!** 🚀✨
