"""
System klas postaci dla Droga Szamana RPG.
Każda klasa to nie tylko statystyki - to filozofia życia, sposób postrzegania świata.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
import random

from player.skills import SkillName


class ClassName(Enum):
    """Dostępne klasy postaci."""
    WOJOWNIK = "wojownik"
    LOTRZYK = "łotrzyk"
    LOWCA = "łowca"
    RZEMIESLNIK = "rzemieślnik"
    MAG = "mag"


@dataclass
class ClassAbility:
    """Unikalna zdolność klasowa."""
    name: str
    description: str
    cooldown: int = 0  # Czas odnowienia w turach
    stamina_cost: float = 10
    mana_cost: float = 0
    requirements: Dict[str, Any] = field(default_factory=dict)
    effect: Optional[Callable] = None
    level_required: int = 1
    mastery_bonus: float = 0.0  # Bonus z doświadczenia (0-1)


@dataclass 
class ClassPhilosophy:
    """Filozofia i światopogląd klasy."""
    core_belief: str  # Główne przekonanie
    code_of_honor: List[str]  # Kodeks postępowania
    taboos: List[str]  # Czego klasa unika
    world_view: str  # Jak postrzega świat
    growth_path: str  # Ścieżka rozwoju
    training_progress: int = 0  # Postęp w treningu filozofii 0-100


class CharacterClass:
    """Bazowa klasa dla wszystkich klas postaci."""
    
    def __init__(self):
        self.name = ""
        self.description = ""
        self.lore = ""  # Historia i pochodzenie klasy
        self.philosophy = None
        
        # Poziom i doświadczenie klasy
        self.level = 1
        self.experience = 0
        
        # Modyfikatory bazowych atrybutów
        self.attribute_modifiers = {
            'strength': 0,
            'agility': 0,
            'endurance': 0,
            'intelligence': 0,
            'willpower': 0
        }
        
        # Umiejętności preferowane (szybszy rozwój)
        self.preferred_skills: List[SkillName] = []
        
        # Umiejętności zakazane lub bardzo trudne
        self.restricted_skills: List[SkillName] = []
        
        # Unikalne zdolności klasy
        self.abilities: Dict[str, ClassAbility] = {}
        
        # Specjalne mechaniki klasy
        self.special_mechanics: Dict[str, Any] = {}
        
        # Poziom mistrzostwa w klasie (0-100)
        self.mastery_level = 0
        
        # Doświadczenia formujące klasę
        self.formative_experiences: List[str] = []
        
    def get_skill_learning_rate(self, skill: SkillName) -> float:
        """
        Zwraca modyfikator szybkości nauki umiejętności.
        
        Returns:
            Mnożnik szybkości nauki (0.5 - 2.0)
        """
        if skill in self.preferred_skills:
            return 1.5 + (self.mastery_level / 200)  # Do 2.0 przy mistrzostwie
        elif skill in self.restricted_skills:
            return 0.5 - (self.mastery_level / 400)  # Do 0.25 przy mistrzostwie
        return 1.0
    
    def can_use_ability(self, ability_name: str, character) -> Tuple[bool, str]:
        """
        Sprawdza czy postać może użyć zdolności.
        
        Returns:
            (czy_może, komunikat)
        """
        if ability_name not in self.abilities:
            return False, "Nie znasz tej zdolności."
        
        ability = self.abilities[ability_name]
        
        # Sprawdź poziom
        if character.level < ability.level_required:
            return False, f"Wymagany poziom: {ability.level_required}"
        
        # Sprawdź staminę
        if character.stamina < ability.stamina_cost:
            return False, "Brak staminy!"
        
        # Sprawdź manę (dla magów)
        if hasattr(character, 'mana') and character.mana < ability.mana_cost:
            return False, "Brak many!"
        
        # Sprawdź cooldown
        if hasattr(character, 'ability_cooldowns'):
            if character.ability_cooldowns.get(ability_name, 0) > 0:
                return False, f"Zdolność odnowi się za {character.ability_cooldowns[ability_name]} tur."
        
        return True, "OK"
    
    def on_level_up(self, character):
        """Wywoływane przy awansie poziomu."""
        self.mastery_level = min(100, self.mastery_level + 5)
        
    def on_combat_start(self, character):
        """Wywoływane na początku walki."""
        pass
    
    def on_kill(self, character, enemy):
        """Wywoływane po zabiciu wroga."""
        pass


class Wojownik(CharacterClass):
    """
    Wojownik - Żelazna Pięść Losu
    
    Ci, którzy wybrali drogę miecza, wiedzą że siła to nie brutalność,
    lecz zdyscyplinowana moc służąca ochronie słabszych.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Wojownik"
        self.description = "Mistrz broni i pancerza, pierwsza linia obrony przed ciemnością."
        
        self.lore = """
        Wojownicy to spadkobiercy starożytnego Zakonu Żelaznej Straży.
        Gdy Imperium upadło, to oni stali na straży ostatnich bastionów cywilizacji.
        Każdy wojownik nosi w sercu przysięgę: "Moja tarcza dla bezbronnych,
        mój miecz przeciw ciemności, moje życie za honor."
        """
        
        self.philosophy = ClassPhilosophy(
            core_belief="Siła istnieje by chronić tych, którzy sami nie mogą się obronić",
            code_of_honor=[
                "Nigdy nie atakuj bezbronnego",
                "Stań w obronie słabszego, nawet kosztem życia",
                "Broń jest ostatecznością, nie pierwszym wyborem",
                "Honor ważniejszy niż życie, ale nie ważniejszy niż niewinni"
            ],
            taboos=[
                "Trucizna to broń tchórza",
                "Atak od tyłu hańbi wojownika",
                "Rabowanie poległych wrogów bez potrzeby"
            ],
            world_view="Świat to pole bitwy między porządkiem a chaosem. Jestem murem przeciw ciemności.",
            growth_path="Od rekruta przez weterana do legendy. Każda blizna to lekcja, każda bitwa to test charakteru."
        )
        
        self.attribute_modifiers = {
            'strength': 3,
            'agility': -1,
            'endurance': 2,
            'intelligence': 0,
            'willpower': 1
        }
        
        self.preferred_skills = [
            SkillName.MIECZE,
            SkillName.WALKA_WRECZ,
            SkillName.WYTRZYMALOSC,
            SkillName.KOWALSTWO
        ]
        
        self.restricted_skills = [
            SkillName.SKRADANIE,
            SkillName.ALCHEMIA
        ]
        
        # Unikalne zdolności wojownika
        self.abilities = {
            "berserk": ClassAbility(
                name="Szał Bitewny",
                description="Popadasz w kontrolowany szał. +50% obrażeń, -25% obrony na 3 tury.",
                cooldown=10,
                stamina_cost=30,
                level_required=1
            ),
            "tarcza_woli": ClassAbility(
                name="Tarcza Woli",
                description="Twoja determinacja tworzy niemal namacalną barierę. Ignorujesz ból przez 2 tury.",
                cooldown=15,
                stamina_cost=20,
                level_required=3
            ),
            "ostatni_bastion": ClassAbility(
                name="Ostatni Bastion",
                description="Gdy twoje HP spadnie poniżej 20%, zyskujesz +100% do obrony i nie możesz zostać oszołomiony.",
                cooldown=0,  # Pasywna
                stamina_cost=0,
                level_required=5
            )
        }
        
        self.special_mechanics = {
            "armor_mastery": True,  # Podwójna skuteczność pancerza
            "pain_resistance": 0.8,  # Redukcja wpływu bólu
            "weapon_mastery_rate": 1.5  # Szybsze uczenie się broni
        }


class Lotrzyk(CharacterClass):
    """
    Łotrzyk - Cień w Mroku
    
    Mistrzowie tego, czego nie widać. Ich bronią jest podstęp,
    a tarczą - umiejętność zniknięcia w cieniu.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Łotrzyk"
        self.description = "Mistrz cieni i iluzji, ekspert od niemożliwego."
        
        self.lore = """
        Bractwo Cienia istnieje od zawsze, choć niewielu wie o jego istnieniu.
        Łotrzykowie to nie zwykli złodzieje - to artyści oszustwa, filozofowie kłamstwa,
        poeci nocy. Mówi się, że potrafią ukraść cień człowieka, a on nawet nie zauważy.
        Ich kodeks jest prosty: "Nie istnieję, więc nie mogę być winny."
        """
        
        self.philosophy = ClassPhilosophy(
            core_belief="Prawda jest iluzją, rzeczywistość to tylko kwestia perspektywy",
            code_of_honor=[
                "Nigdy nie zdradź Bractwa",
                "Krew niewinnych plami cień - unikaj niepotrzebnego zabijania",
                "Informacja jest cenniejsza niż złoto",
                "Najlepszy łotrzyk to ten, o którym nikt nie wie"
            ],
            taboos=[
                "Bezpośrednia konfrontacja gdy można jej uniknąć",
                "Zostawianie śladów",
                "Praca za darmo",
                "Lojalność wobec władzy"
            ],
            world_view="Świat to teatr, a ja gram wszystkie role. Prawda jest tym, w co ludzie wierzą.",
            growth_path="Od kieszonkowca przez mistrza włamań do legendy, której imienia nikt nie zna."
        )
        
        self.attribute_modifiers = {
            'strength': -1,
            'agility': 4,
            'endurance': 0,
            'intelligence': 2,
            'willpower': 0
        }
        
        self.preferred_skills = [
            SkillName.SKRADANIE,
            SkillName.WALKA_WRECZ,
            SkillName.PERSWAZJA,
            SkillName.HANDEL
        ]
        
        self.restricted_skills = [
            SkillName.KOWALSTWO,
            SkillName.WYTRZYMALOSC
        ]
        
        self.abilities = {
            "niewidzialnosc": ClassAbility(
                name="Płaszcz Cieni",
                description="Stapiaasz się z cieniem. Przeciwnicy mają 75% szans na chybienie przez 2 tury.",
                cooldown=8,
                stamina_cost=25,
                level_required=1
            ),
            "cios_w_plecy": ClassAbility(
                name="Sztylet w Mroku",
                description="Jeśli przeciwnik cię nie widzi, zadajesz potrójne obrażenia z 50% szansą na krwawienie.",
                cooldown=5,
                stamina_cost=15,
                level_required=2
            ),
            "dymna_bomba": ClassAbility(
                name="Zasłona Dymu",
                description="Rzucasz bombę dymną. Wszyscy w walce mają -50% celności na 3 tury.",
                cooldown=12,
                stamina_cost=10,
                level_required=3
            ),
            "kieszonkowiec": ClassAbility(
                name="Zwinne Palce",
                description="Podczas walki możesz ukraść przedmiot z 30% szansą.",
                cooldown=0,  # Pasywna
                stamina_cost=0,
                level_required=1
            )
        }
        
        self.special_mechanics = {
            "critical_chance": 0.25,  # +25% szans na cios krytyczny
            "dodge_bonus": 0.20,  # +20% do uniku
            "sneak_attack_damage": 2.0,  # x2 obrażeń przy ataku z zaskoczenia
            "lockpicking_bonus": True,  # Może otwierać zamki bez kluczy
        }


class Lowca(CharacterClass):
    """
    Łowca - Strażnik Puszczy
    
    Samotni wędrowcy, którzy wybrali dziką naturę zamiast cywilizacji.
    Rozumieją mowę wiatru i ślady zwierząt.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Łowca"
        self.description = "Mistrz survivalu i tropienia, jeden z naturą."
        
        self.lore = """
        Łowcy to ostatni z Leśnych Strażników, starożytnego zakonu który
        chronił granice między światem ludzi a dzikimi ostępami.
        Każdy łowca przechodzi Próbę Głuszy - rok samotnie w dziczy,
        tylko z nożem. Ci którzy wracają, nie są już tylko ludźmi -
        stają się częścią lasu, rozumieją jego szepty i gniew.
        """
        
        self.philosophy = ClassPhilosophy(
            core_belief="Natura nie jest okrutna ani dobra - jest uczciwa. Zabij lub giń, ale z szacunkiem",
            code_of_honor=[
                "Nie zabijaj więcej niż potrzebujesz",
                "Szanuj drapieżnika, nawet gdy go pokonasz",
                "Las daje i zabiera - przyjmij oba dary",
                "Cywilizacja osłabia, dzicz hartuje"
            ],
            taboos=[
                "Marnowanie upolowanej zwierzyny",
                "Niszczenie natury bez potrzeby",
                "Życie w murach miasta dłużej niż to konieczne",
                "Walka bez honoru z dzikim zwierzęciem"
            ],
            world_view="Miasta to klatki, prawdziwe życie jest w dziczy. Jestem wilkiem wśród owiec.",
            growth_path="Od nowicjusza przez tropiciela do ducha lasu, którego nawet zwierzęta się boją."
        )
        
        self.attribute_modifiers = {
            'strength': 1,
            'agility': 2,
            'endurance': 2,
            'intelligence': 0,
            'willpower': 0
        }
        
        self.preferred_skills = [
            SkillName.LUCZNICTWO,
            SkillName.SKRADANIE,
            SkillName.MEDYCYNA,
            SkillName.WYTRZYMALOSC
        ]
        
        self.restricted_skills = [
            SkillName.HANDEL,
            SkillName.KOWALSTWO
        ]
        
        self.abilities = {
            "celny_strzal": ClassAbility(
                name="Oko Sokoła",
                description="Twój następny strzał trafia w słaby punkt. Ignoruje pancerz i zadaje +100% obrażeń.",
                cooldown=6,
                stamina_cost=20,
                level_required=1
            ),
            "pulapka": ClassAbility(
                name="Sidła Myśliwego",
                description="Zastawiasz pułapkę. Przeciwnik ma 60% szans na unieruchomienie na 2 tury.",
                cooldown=10,
                stamina_cost=15,
                level_required=2
            ),
            "wezwanie_zwierzat": ClassAbility(
                name="Zew Dziczy",
                description="Wzywasz dzikie zwierzę do pomocy w walce na 5 tur.",
                cooldown=20,
                stamina_cost=30,
                level_required=4
            ),
            "instynkt_lowcy": ClassAbility(
                name="Instynkt Drapieżnika",
                description="Wyczuwasz słabość. +50% szans na krytyczne trafienie przeciwko rannemu wrogowi.",
                cooldown=0,  # Pasywna
                stamina_cost=0,
                level_required=3
            )
        }
        
        self.special_mechanics = {
            "track_invisible": True,  # Może tropić niewidzialnych wrogów
            "nature_healing": 1.5,  # +50% do regeneracji w naturze
            "beast_empathy": True,  # Dzikie zwierzęta są mniej agresywne
            "survival_expert": True,  # Nie traci HP z głodu/pragnienia tak szybko
            "ranged_mastery": 1.3  # +30% do obrażeń dystansowych
        }


class Rzemieslnik(CharacterClass):
    """
    Rzemieślnik - Kuźnia Przeznaczenia
    
    Twórcy i wynalazcy, którzy wierzą że prawdziwa moc leży nie w sile mięśni,
    ale w sile umysłu i precyzji rąk.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Rzemieślnik"
        self.description = "Mistrz kreacji, potrafi stworzyć cuda z najprostszych materiałów."
        
        self.lore = """
        Gildia Mistrzów powstała gdy pierwszy człowiek wykuł pierwszy miecz.
        Rzemieślnicy to nie tylko kowale czy stolarze - to alchemicy materii,
        filozofowie formy, poeci przedmiotów. Wierzą że każdy przedmiot ma duszę,
        a zadaniem rzemieślnika jest ją obudzić. Ich największe dzieła stają się
        legendami - miecze które nie tępieją, zbroje które rosną z właścicielem,
        eliksiry które leczą duszę.
        """
        
        self.philosophy = ClassPhilosophy(
            core_belief="Ręce które potrafią tworzyć są cenniejsze niż te które tylko niszczą",
            code_of_honor=[
                "Twoje dzieło to twój podpis - nigdy nie twórz byle czego",
                "Sekret mistrza umiera z mistrzem, chyba że znajdzie godnego ucznia",
                "Przedmiot stworzony do zła przyniesie zło twórcy",
                "Cena dzieła to nie tylko materiały, ale i dusza włożona w tworzenie"
            ],
            taboos=[
                "Kopiowanie cudzych dzieł bez dodania własnej iskry",
                "Tworzenie broni masowej zagłady",
                "Sprzedawanie sekretów Gildii",
                "Niszczenie dzieł innych mistrzów bez potrzeby"
            ],
            world_view="Świat to warsztat, a ja jestem narzędziem w rękach przeznaczenia. Tworzę więc jestem.",
            growth_path="Od czeladnika przez mistrza do żywej legendy, której dzieła przetrwają wieki."
        )
        
        self.attribute_modifiers = {
            'strength': 1,
            'agility': 0,
            'endurance': 1,
            'intelligence': 3,
            'willpower': 0
        }
        
        self.preferred_skills = [
            SkillName.KOWALSTWO,
            SkillName.ALCHEMIA,
            SkillName.HANDEL,
            SkillName.MEDYCYNA
        ]
        
        self.restricted_skills = [
            SkillName.SKRADANIE,
            SkillName.LUCZNICTWO
        ]
        
        self.abilities = {
            "naprawa_w_walce": ClassAbility(
                name="Błyskawiczna Naprawa",
                description="Naprawiasz swoją broń lub zbroję w trakcie walki, przywracając 50% wytrzymałości.",
                cooldown=10,
                stamina_cost=15,
                level_required=1
            ),
            "ulepszenie_tymczasowe": ClassAbility(
                name="Improwizowane Ulepszenie",
                description="Ulepszasz broń sojusznika na 5 tur (+30% obrażeń).",
                cooldown=15,
                stamina_cost=20,
                level_required=2
            ),
            "bomba_alchemiczna": ClassAbility(
                name="Ładunek Wybuchowy",
                description="Rzucasz improwizowaną bombę zadającą obrażenia obszarowe.",
                cooldown=8,
                stamina_cost=10,
                level_required=3
            ),
            "arcydzielo": ClassAbility(
                name="Dotyk Mistrza",
                description="Twoje następne dzieło będzie miało legendarne właściwości.",
                cooldown=100,  # Raz na "dzień"
                stamina_cost=50,
                level_required=5
            )
        }
        
        self.special_mechanics = {
            "craft_quality_bonus": 1.5,  # +50% do jakości wytwarzanych przedmiotów
            "repair_efficiency": 2.0,  # x2 efektywność napraw
            "material_efficiency": 0.75,  # Zużywa 25% mniej materiałów
            "identify_items": True,  # Automatycznie identyfikuje przedmioty
            "craft_speed": 1.5  # +50% szybkość craftingu
        }


class Mag(CharacterClass):
    """
    Mag - Tkacz Rzeczywistości
    
    Ci którzy ujrzeli prawdziwą naturę rzeczywistości i nauczyli się ją kształtować.
    Magia to nie dar - to przekleństwo które można zamienić w moc.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Mag"
        self.description = "Władca energii i manipulator rzeczywistości, chodzący między światami."
        
        self.lore = """
        Kolegium Arkanów upadło 500 lat temu, gdy Wielki Eksperyment rozdarł
        zasłonę między światami. Z tysięcy magów przeżyło siedmiu. Każdy mag
        nosi w sobie echo tej katastrofy - szepty z Pustki, które obiecują
        nieograniczoną moc za cenę duszy. Prawdziwy mag to nie ten kto włada
        największą mocą, ale ten kto potrafi jej nie użyć. Magia to żywy ogień -
        ogrzeje cię lub spali, zależy jak blisko się zbliżysz.
        """
        
        self.philosophy = ClassPhilosophy(
            core_belief="Rzeczywistość to sugestia dla tych którzy znają prawdziwe Słowa Mocy",
            code_of_honor=[
                "Wiedza magiczna to odpowiedzialność - nie dziel się nią z niegodnymi",
                "Pustka kusi, ale kto jej ulegnie, przestaje być sobą",
                "Magia ma cenę - zawsze. Kto twierdzi inaczej, kłamie lub jest głupcem",
                "Szanuj Tkankę Rzeczywistości - jej zniszczenie zniszczy wszystko"
            ],
            taboos=[
                "Nekromancja - martwi powinni spoczywać",
                "Kontrola umysłu - wolna wola jest święta",
                "Pakty z demonami - cena zawsze przewyższa korzyść",
                "Używanie magii krwi bez absolutnej konieczności"
            ],
            world_view="Rzeczywistość to iluzja, magia to prawda. Jestem tym który widzi struny i potrafi na nich grać.",
            growth_path="Od adepta przez mistrza do archimaga. Każde zaklęcie to krok bliżej boskości... lub szaleństwa."
        )
        
        self.attribute_modifiers = {
            'strength': -2,
            'agility': 0,
            'endurance': -1,
            'intelligence': 4,
            'willpower': 4
        }
        
        self.preferred_skills = [
            SkillName.ALCHEMIA,
            SkillName.MEDYCYNA,
            SkillName.PERSWAZJA,
            SkillName.HANDEL  # Handel magicznymi artefaktami
        ]
        
        self.restricted_skills = [
            SkillName.KOWALSTWO,
            SkillName.MIECZE,
            SkillName.WYTRZYMALOSC
        ]
        
        self.abilities = {
            "pocisk_mocy": ClassAbility(
                name="Kula Ognia",
                description="Miotasz kulą czystej energii. Zadaje obrażenia magiczne ignorujące pancerz.",
                cooldown=3,
                stamina_cost=5,
                mana_cost=10,
                level_required=1
            ),
            "tarcza_many": ClassAbility(
                name="Bariera Arkanów",
                description="Tworzysz magiczną barierę pochłaniającą 50% obrażeń na 3 tury.",
                cooldown=10,
                stamina_cost=10,
                mana_cost=20,
                level_required=2
            ),
            "teleportacja": ClassAbility(
                name="Przeskok Przestrzeni",
                description="Teleportujesz się za przeciwnika, zyskując przewagę taktyczną.",
                cooldown=15,
                stamina_cost=15,
                mana_cost=25,
                level_required=3
            ),
            "wybuch_many": ClassAbility(
                name="Nova Arkanów",
                description="Eksplodujesz czystą energią, zadając masywne obrażenia obszarowe.",
                cooldown=20,
                stamina_cost=30,
                mana_cost=50,
                level_required=5
            ),
            "meditacja": ClassAbility(
                name="Medytacja Mocy",
                description="Regenerujesz 30% many przez 3 tury, ale nie możesz się poruszać.",
                cooldown=8,
                stamina_cost=0,
                mana_cost=0,
                level_required=1
            )
        }
        
        self.special_mechanics = {
            "mana_pool": True,  # Ma dodatkowy zasób - manę
            "mana_regen": 2.0,  # Regeneruje 2 many na turę
            "spell_power": 1.5,  # +50% do obrażeń magicznych
            "magic_resistance": 0.3,  # 30% odporności na magię
            "arcane_sight": True,  # Widzi niewidzialne i magiczne aury
            "ritual_casting": True,  # Może wykonywać rytuały poza walką
            "enchanting": True  # Może zaklinać przedmioty
        }
    
    def on_combat_start(self, character):
        """Mag zaczyna walkę z pełną barierą many."""
        if hasattr(character, 'mana'):
            character.mana = min(character.max_mana, character.mana + 10)


class ClassManager:
    """Manager systemu klas."""
    
    def __init__(self):
        self.available_classes = {
            ClassName.WOJOWNIK: Wojownik(),
            ClassName.LOTRZYK: Lotrzyk(),
            ClassName.LOWCA: Lowca(),
            ClassName.RZEMIESLNIK: Rzemieslnik(),
            ClassName.MAG: Mag()
        }
    
    def get_class(self, class_name: ClassName) -> CharacterClass:
        """Zwraca instancję klasy."""
        return self.available_classes.get(class_name)
    
    def get_class_description(self, class_name: ClassName) -> str:
        """Zwraca pełny opis klasy dla wyboru."""
        char_class = self.get_class(class_name)
        if not char_class:
            return "Nieznana klasa"
        
        lines = [
            f"═══ {char_class.name.upper()} ═══",
            "",
            char_class.description,
            "",
            "HISTORIA:",
            char_class.lore,
            "",
            "FILOZOFIA:",
            f"• {char_class.philosophy.core_belief}",
            "",
            "MODYFIKATORY:",
            f"  Siła: {char_class.attribute_modifiers['strength']:+d}",
            f"  Zręczność: {char_class.attribute_modifiers['agility']:+d}",
            f"  Wytrzymałość: {char_class.attribute_modifiers['endurance']:+d}",
            f"  Inteligencja: {char_class.attribute_modifiers['intelligence']:+d}",
            f"  Siła Woli: {char_class.attribute_modifiers['willpower']:+d}",
            "",
            "PREFEROWANE UMIEJĘTNOŚCI:",
        ]
        
        for skill in char_class.preferred_skills:
            lines.append(f"  • {skill.value}")
        
        lines.extend([
            "",
            "UNIKALNE ZDOLNOŚCI:"
        ])
        
        for ability in list(char_class.abilities.values())[:3]:  # Pokaż pierwsze 3
            lines.append(f"  • {ability.name}: {ability.description}")
        
        return "\n".join(lines)
    
    def list_all_classes(self) -> str:
        """Zwraca listę wszystkich dostępnych klas."""
        lines = ["═══ DOSTĘPNE KLASY ═══", ""]
        
        for class_name in ClassName:
            char_class = self.get_class(class_name)
            lines.append(f"{class_name.value.upper()}: {char_class.description}")
        
        lines.append("")
        lines.append("Wpisz 'info [nazwa_klasy]' aby dowiedzieć się więcej.")
        
        return "\n".join(lines)