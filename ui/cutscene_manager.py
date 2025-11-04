"""
System zarządzania cutscenami i narracją dla Droga Szamana RPG
Obsługuje wieloetapowe sceny wprowadzające z efektami wizualnymi
"""

import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass


@dataclass
class CutsceneFrame:
    """Pojedyncza klatka cutscene"""
    text: str
    delay: float = 2.0  # Opóźnienie po wyświetleniu (sekundy)
    clear_screen: bool = False  # Czy wyczyścić ekran przed pokazaniem
    wait_for_input: bool = False  # Czy czekać na Enter
    effect: str = "none"  # "none", "fade", "typewriter"


class CutsceneManager:
    """Manager do wyświetlania cutscene i narracji"""

    def __init__(self, interface=None):
        """
        Args:
            interface: GameInterface do wyświetlania tekstu
        """
        self.interface = interface
        self.skip_cutscenes = False

    def play_cutscene(self, frames: List[CutsceneFrame], skippable: bool = True):
        """
        Odtwarza cutscene z listy klatek

        Args:
            frames: Lista CutsceneFrame do wyświetlenia
            skippable: Czy można pominąć cutscene (ESC lub 's')
        """
        if self.skip_cutscenes:
            return

        for i, frame in enumerate(frames):
            # Wyczyść ekran jeśli potrzeba
            if frame.clear_screen and self.interface:
                self.interface.clear()

            # Wyświetl tekst z efektem
            if frame.effect == "typewriter":
                self._typewriter_effect(frame.text)
            elif frame.effect == "fade":
                self._fade_effect(frame.text)
            else:
                if self.interface:
                    self.interface.print(frame.text)
                else:
                    print(frame.text)

            # Czekaj na input lub delay
            if frame.wait_for_input:
                if skippable and i < len(frames) - 1:
                    prompt = "\n[Enter aby kontynuować, 's' aby pominąć]"
                else:
                    prompt = "\n[Naciśnij Enter aby kontynuować]"

                if self.interface:
                    user_input = self.interface.get_input(prompt)
                else:
                    user_input = input(prompt)

                if user_input.lower() == 's' and skippable:
                    self.skip_cutscenes = True
                    return
            else:
                time.sleep(frame.delay)

    def _typewriter_effect(self, text: str, speed: float = 0.03):
        """Efekt maszynowy - litera po literze"""
        for char in text:
            if self.interface:
                self.interface.print(char, end='', flush=True)
            else:
                print(char, end='', flush=True)
            time.sleep(speed)
        if self.interface:
            self.interface.print()  # Nowa linia na końcu
        else:
            print()

    def _fade_effect(self, text: str):
        """Efekt zanikania - stopniowe pojawianie się"""
        lines = text.split('\n')
        for line in lines:
            if self.interface:
                self.interface.print(line)
            else:
                print(line)
            time.sleep(0.5)

    def reset_skip(self):
        """Resetuj flagę pomijania cutscene"""
        self.skip_cutscenes = False


def create_prison_intro_cutscene() -> List[CutsceneFrame]:
    """
    Tworzy cutscene wprowadzającą do więzienia
    Wieloetapowa, klimatyczna narracja

    Returns:
        Lista CutsceneFrame dla intro
    """
    frames = []

    # FRAME 1: Ciemność i ból
    frames.append(CutsceneFrame(
        text="""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                          DROGA SZAMANA                               ║
║                            PROLOG                                    ║
║                     "Przebudzenie w Ciemności"                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""",
        delay=2.0,
        clear_screen=True,
        effect="fade"
    ))

    # FRAME 2: Pierwsze odczucia
    frames.append(CutsceneFrame(
        text="""
Ciemność.

Głęboka, przytłaczająca, absolutna ciemność.

To pierwsze co czujesz. Nie, popraw się - drugie.
Pierwsze to ból. Rozrywający czaszkę, pulsujący ból.
""",
        delay=3.0,
        effect="typewriter"
    ))

    # FRAME 3: Budzenie się
    frames.append(CutsceneFrame(
        text="""
Powoli, bardzo powoli, odzyskujesz świadomość.

Otwierasz oczy. Światło - blade, zimne - przenika przez zakratowane okno,
oślepiając cię na moment. Mrugasz. Raz. Drugi. Trzeci.

Gdzie jesteś?
""",
        delay=3.0,
        effect="typewriter"
    ))

    # FRAME 4: Percepcja otoczenia
    frames.append(CutsceneFrame(
        text="""
Leżysz na zimnej, kamiennej podłodze. Każdy kamień wbija się w twoje
obolałe ciało. Czujesz zapach - pleśń, wilgoć, pot, strach.

W ustach metaliczny posmak. Krwi? Chyba krwi.

Próbujesz wstać. Twoje mięśnie protestują, jakby przez ostatnie dni
robiłeś tylko to - leżał na tym przeklętym kamieniu.
""",
        delay=3.0,
        effect="typewriter"
    ))

    # FRAME 5: Realizacja - więzienie
    frames.append(CutsceneFrame(
        text="""
Siadasz. Patrzysz wokół siebie.

Cela. Mała. Ciemna. Trzy metry na trzy. Może mniej. Może więcej.
Trudno powiedzieć gdy ściany zdają się napierać z każdej strony.

Kraty w oknie. Solidne, stalowe kraty.
Drzwi - masywne, żelazne, pozamykane.

Więzienie. Jesteś w więzieniu.
""",
        delay=3.5,
        effect="typewriter",
        wait_for_input=True
    ))

    # FRAME 6: Dźwięki życia
    frames.append(CutsceneFrame(
        text="""
W oddali słychać odgłosy.

Jęki. Przekleństwa. Czyjeś szlochanie - ciche, stłumione.
Kroki strażników po kamiennym korytarzu. Brzęk łańcuchów.
Gdzieś ktoś się kłóci. Gdzieś ktoś śmieje się - nerwowo, histerycznie.

Więzienie żyje. Tętni własnym, chorym życiem.
A ty jesteś jego częścią.
""",
        delay=3.0,
        effect="typewriter"
    ))

    # FRAME 7: Próba przypomnienia
    frames.append(CutsceneFrame(
        text="""
Kim jesteś? Dlaczego tu jesteś?

Próbujesz przypomnieć sobie... cokolwiek.

Twoje imię? Tak, to pamiętasz. Ale co jeszcze?
Jak się tu znalazłeś? Za co cię aresztowano?
Co robiłeś... wczoraj? Przedwczoraj? Tydzień temu?

Pustka. Lodowata, przerażająca pustka w głowie.
""",
        delay=3.5,
        effect="typewriter",
        wait_for_input=True
    ))

    # FRAME 8: Determinacja
    frames.append(CutsceneFrame(
        text="""
Ale jedno wiesz na pewno.

Musisz stąd uciec.

Nie możesz zostać w tym miejscu. Nie możesz zgniść w tej celi,
zapomniany przez bogów i ludzi. Musisz przeżyć.

Musisz znaleźć odpowiedzi. Musisz znaleźć drogę.
""",
        delay=3.0,
        effect="typewriter"
    ))

    # FRAME 9: Pierwszy krok
    frames.append(CutsceneFrame(
        text="""
Wstajesz. Powoli. Ostrożnie.

Każdy mięsień boli. Nogi drżą. Głowa wiruje.
Ale stoisz.

To twój pierwszy krok na długiej drodze.
Drodze Szamana.

"Przygoda zaczyna się TERAZ..."
""",
        delay=2.0,
        effect="typewriter",
        wait_for_input=True
    ))

    # FRAME 10: Początek gry
    frames.append(CutsceneFrame(
        text="""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║  💡 WSKAZÓWKA: Wpisz 'rozejrzyj' aby przyjrzeć się swojej celi      ║
║                Wpisz 'pomoc' aby zobaczyć dostępne komendy          ║
║                Wpisz 'status' aby sprawdzić swój stan               ║
║                                                                       ║
║  Pamiętaj: W tym świecie uczysz się przez praktykę, nie przez XP.   ║
║            Każda akcja ma konsekwencje. Każda decyzja się liczy.    ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""",
        delay=2.0,
        wait_for_input=True,
        clear_screen=False
    ))

    return frames


def create_tutorial_hints() -> Dict[str, str]:
    """
    Tworzy słownik z kontekstowymi wskazówkami tutorialowymi

    Returns:
        Dict[context_id, hint_text]
    """
    return {
        "first_look": """
💡 TUTORIAL: Rozglądanie się
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dobrze! Zawsze warto się rozejrzeć w nowym miejscu.
Możesz znaleźć ukryte przedmioty, sekrety, lub zauważyć coś ważnego.

Inne przydatne komendy:
  • 'zbadaj [przedmiot]' - dokładnie obejrzyj coś
  • 'przeszukaj [miejsce]' - szukaj ukrytych rzeczy
  • 'idź [kierunek]' - przemieszczaj się między lokacjami
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",

        "first_inventory": """
💡 TUTORIAL: Ekwipunek
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Twój ekwipunek to wszystko co posiadasz.
W więzieniu każdy przedmiot może być cenny - nawet kawałek chleba.

Przydatne komendy:
  • 'użyj [przedmiot]' - użyj przedmiotu
  • 'wyposażenie' - zobacz co masz na sobie
  • 'daj [przedmiot] [npc]' - podaruj coś komuś
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",

        "first_npc": """
💡 TUTORIAL: NPCe i Rozmowy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NPCe w tej grze żyją własnym życiem. Mają własne cele, wspomnienia,
i emocje. Pamiętają twoje czyny - zarówno dobre jak i złe.

Jak rozmawiać:
  • 'rozmawiaj [npc]' - rozpocznij rozmowę
  • Wybierz numer opcji dialogowej (1, 2, 3...)
  • Niektóre opcje wymagają określonych statystyk lub relacji

Wskazówka: Warto poznać innych więźniów. W więzieniu sojusznicy to życie.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",

        "first_quest": """
💡 TUTORIAL: Questy i Zadania
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Odkryłeś swój pierwszy quest!

Questy w tej grze nie pojawiają się jako markers. Powstają EMERGENTNIE
z sytuacji. Możesz odkryć quest przez:
  • Podsłuchanie rozmów
  • Znalezienie przedmiotu lub wskazówki
  • Rozmowę z NPCem
  • Obserwację wydarzeń

Sprawdź questy komendą: 'questy' lub 'zadania'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",

        "first_combat": """
💡 TUTORIAL: Walka i Ból
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UWAGA: Walka w tej grze jest śmiertelnie poważna!

• Ból wpływa na WSZYSTKIE twoje akcje
• Kontuzje nie znikają magicznie - musisz się leczyć
• Śmierć ma REALNE konsekwencje
• Ucieczka jest często mądrzejsza niż walka

Pamiętaj: Nie jesteś nieśmiertelnym bohaterem. Jesteś więźniem.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",

        "first_skill_use": """
💡 TUTORIAL: Use-Based Learning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
W tej grze NIE MA poziomów ani XP!

Uczysz się przez praktykę:
  • Im częściej używasz miecza, tym lepszy stajesz się w walce mieczem
  • Im więcej gotuj, tym lepsze posiłki przygotujesz
  • Im więcej kradniesz, tym lepszy złodziej z ciebie

Każde użycie umiejętności = mały wzrost. Prawdziwa nauka!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",

        "first_secret": """
💡 TUTORIAL: Sekrety i Eksploracja
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Świetnie! Znalazłeś sekret!

Więzienie kryje wiele tajemnic:
  • Ukryte przejścia
  • Schowane przedmioty
  • Zapomniane komnaty
  • Tajemnicze znaki

Eksploruj dokładnie każdą lokację. Badaj podejrzane rzeczy.
Rozmawiaj z NPCami. Czasem najtemniejze zakamarki kryją największe skarby.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    }


class TutorialManager:
    """Manager systemu tutoriali"""

    def __init__(self, interface=None):
        self.interface = interface
        self.shown_hints = set()
        self.hints = create_tutorial_hints()
        self.tutorial_enabled = True

    def show_hint(self, hint_id: str, force: bool = False):
        """
        Pokaż wskazówkę tutorialową

        Args:
            hint_id: ID wskazówki z create_tutorial_hints()
            force: Czy pokazać nawet jeśli już była pokazana
        """
        if not self.tutorial_enabled and not force:
            return

        if hint_id in self.shown_hints and not force:
            return

        if hint_id not in self.hints:
            return

        hint_text = self.hints[hint_id]

        if self.interface:
            self.interface.print(hint_text)
        else:
            print(hint_text)

        self.shown_hints.add(hint_id)

    def disable_tutorial(self):
        """Wyłącz system tutoriali"""
        self.tutorial_enabled = False

    def enable_tutorial(self):
        """Włącz system tutoriali"""
        self.tutorial_enabled = True

    def reset(self):
        """Zresetuj pokazane hinty"""
        self.shown_hints.clear()
