"""
Interfejs tekstowy gry
Wyświetlanie informacji i interakcja z graczem
"""

import os


class GameInterface:
    """Interfejs tekstowy gry"""

    @staticmethod
    def clear_screen():
        """Czyści ekran konsoli"""
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def print_header(title: str):
        """Wyświetla nagłówek"""
        separator = "=" * 60
        print(f"\n{separator}")
        print(f"{title:^60}")
        print(f"{separator}\n")

    @staticmethod
    def print_separator():
        """Wyświetla separator"""
        print("-" * 60)

    @staticmethod
    def show_welcome():
        """Wyświetla ekran powitalny"""
        GameInterface.clear_screen()
        print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          WŚRÓD MILIONA GWIAZD                           ║
║                                                          ║
║          Tekstowa Gra Strategiczna SF                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Witaj, Komandorze!

Przed Tobą niezmierzona przestrzeń galaktyki. Miliony gwiazd,
tysiące planet czekających na odkrycie i kolonizację.

Czy poprowadzisz swoją cywilizację do dominacji wśród gwiazd?
        """)

    @staticmethod
    def show_main_menu():
        """Wyświetla menu główne"""
        print("\n=== MENU GŁÓWNE ===")
        print("1. Nowa gra")
        print("2. Wczytaj grę")
        print("3. Wyjście")
        print("\nWybierz opcję (1-3): ", end="")

    @staticmethod
    def show_faction_selection():
        """Wyświetla wybór frakcji"""
        print("\n=== WYBÓR FRAKCJI ===\n")
        print("1. Imperium - Potężna militarna monarchia")
        print("   Bonus: +20% siły ataku flot")
        print()
        print("2. Federacja - Pokojowa unia planet")
        print("   Bonus: +25% do produkcji zasobów")
        print()
        print("3. Korporacja - Mega-korporacja handlowa")
        print("   Bonus: +30% przychodów z kredytów")
        print()
        print("4. Piraci - Wolni łowcy galaktyczni")
        print("   Bonus: +2 do zasięgu ruchu flot")
        print()

    @staticmethod
    def show_game_menu(turn: int):
        """Wyświetla menu gry"""
        GameInterface.print_separator()
        print(f"TURA: {turn}")
        GameInterface.print_separator()
        print("\nDostępne komendy:")
        print("  status        - Pokaż status gracza")
        print("  planety       - Lista Twoich planet")
        print("  planeta <nazwa> - Szczegóły planety")
        print("  mapa          - Mapa galaktyki")
        print("  buduj <typ> <planeta> - Buduj budynek")
        print("  badania       - Status badań")
        print("  badaj <id>    - Rozpocznij badanie technologii")
        print("  floty         - Lista Twoich flot")
        print("  następna      - Następna tura")
        print("  zapisz        - Zapisz grę")
        print("  pomoc         - Pomoc")
        print("  koniec        - Zakończ grę")
        print()

    @staticmethod
    def show_help():
        """Wyświetla pomoc"""
        GameInterface.print_header("POMOC")

        print("""
=== PODSTAWY GRY ===

Celem gry jest dominacja w galaktyce poprzez ekspansję, rozwój
technologiczny i siłę militarną.

=== ZASOBY ===

Metale (⚙️)      - Podstawowy surowiec do budowy
Kryształy (💎)   - Zaawansowane komponenty technologiczne
Energia (⚡)     - Zasilanie budynków i systemów
Kredyty (💰)     - Uniwersalna waluta
Populacja (👥)   - Siła robocza Twojej cywilizacji
Antymateria (⚛️) - Rzadki zasób do napędu FTL
Deuterium (🛢️)   - Paliwo do statków

=== BUDYNKI ===

kopalnia      - Produkuje metale
rafineria     - Produkuje kryształy
elektrownia   - Produkuje energię
laboratorium  - Przyspiesza badania
stocznia      - Buduje statki
tarcza        - Obrona planetarna
farma         - Zwiększa populację

=== PRZYKŁADOWE KOMENDY ===

buduj kopalnia "Alpha Prime"  - Zbuduj kopalnię na planecie
badaj lasery_1               - Rozpocznij badanie laserów
następna                     - Przejdź do następnej tury
planeta "Alpha Prime"        - Zobacz szczegóły planety

=== STRATEGIA ===

1. Na początku skup się na rozwoju ekonomii (kopalnie, rafinerie)
2. Buduj laboratoria dla szybszego rozwoju technologicznego
3. Rozwijaj flotę gdy masz stabilne przychody
4. Kolonizuj nowe planety dla większych zasobów
        """)

    @staticmethod
    def show_building_types():
        """Wyświetla typy budynków"""
        print("\n=== TYPY BUDYNKÓW ===")
        print("kopalnia      - Kopalnia Metali")
        print("rafineria     - Rafineria Kryształów")
        print("elektrownia   - Elektrownia Fuzji")
        print("laboratorium  - Laboratorium Badawcze")
        print("stocznia      - Stocznia Kosmiczna")
        print("tarcza        - Generator Tarczy")
        print("farma         - Farma Hydroponiczna")

    @staticmethod
    def get_input(prompt: str = "> ") -> str:
        """Pobiera input od użytkownika"""
        return input(prompt).strip()

    @staticmethod
    def pause():
        """Czeka na naciśnięcie klawisza"""
        input("\nNaciśnij ENTER aby kontynuować...")

    @staticmethod
    def confirm(message: str) -> bool:
        """Prosi o potwierdzenie"""
        response = input(f"{message} (tak/nie): ").strip().lower()
        return response in ['tak', 't', 'yes', 'y']

    @staticmethod
    def show_error(message: str):
        """Wyświetla błąd"""
        print(f"\n❌ BŁĄD: {message}")

    @staticmethod
    def show_success(message: str):
        """Wyświetla sukces"""
        print(f"\n✓ {message}")

    @staticmethod
    def show_info(message: str):
        """Wyświetla informację"""
        print(f"\nℹ {message}")

    @staticmethod
    def show_game_over(victory: bool):
        """Wyświetla ekran końca gry"""
        GameInterface.clear_screen()

        if victory:
            print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║                    ZWYCIĘSTWO!                          ║
║                                                          ║
║     Twoja cywilizacja zdominowała galaktykę!            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Gratulacje, Komandorze!

Twoja wizja, strategia i determinacja doprowadziły Twoją
cywilizację do hegemonii wśród miliona gwiazd.

Historia zapamiętana złotymi zgłoskami Twoje imię!
            """)
        else:
            print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║                     PORAŻKA                             ║
║                                                          ║
║        Twoja cywilizacja upadła...                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Niestety, Komandorze...

Straciłeś wszystkie swoje planety. Twoja cywilizacja rozproszyła
się w kosmosie, a Twoje marzenia o dominacji przepadły w
ciemności między gwiazdami.

Może następnym razem...
            """)
