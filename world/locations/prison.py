"""
Więzienie Początku - główna lokacja startowa gry Droga Szamana RPG.
Mroczne więzienie z którego gracz musi uciec, pełne sekretów i niebezpieczeństw.
"""

import random
import json
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

# Import systemów
from world.time_system import TimeSystem
from world.weather import WeatherSystem, WeatherType


class LocationType(Enum):
    """Typy lokacji w więzieniu."""
    CELL = "cela"
    CORRIDOR = "korytarz"
    COURTYARD = "dziedziniec"
    OFFICE = "biuro"
    KITCHEN = "kuchnia"
    ARMORY = "zbrojownia"
    GUARD_POST = "posterunek"


@dataclass
class Item:
    """Przedmiot możliwy do znalezienia."""
    name: str
    description: str
    can_take: bool = True
    hidden: bool = False
    quest_item: bool = False
    examine_text: Optional[str] = None
    
    def get_examine_text(self) -> str:
        """Zwraca tekst przy dokładnym zbadaniu przedmiotu."""
        if self.examine_text:
            return self.examine_text
        return self.description


@dataclass
class Prisoner:
    """Więzień w celi."""
    name: str
    description: str
    dialogue_day: List[str] = field(default_factory=list)
    dialogue_night: List[str] = field(default_factory=list)
    has_quest: bool = False
    is_sleeping: bool = False
    mood: str = "neutralny"  # neutralny, przyjazny, wrogi, przestraszony


@dataclass
class Secret:
    """Sekret do odkrycia."""
    id: str
    name: str
    description: str
    discovery_hint: str
    discovered: bool = False
    requirements: Dict[str, Any] = field(default_factory=dict)
    rewards: List[Item] = field(default_factory=list)


@dataclass
class Guard:
    """Strażnik więzienny."""
    name: str
    description: str
    patrol_route: List[str]
    current_location: str
    alert_level: int = 0  # 0-normalny, 1-podejrzliwy, 2-alarm
    equipment: List[str] = field(default_factory=list)
    shift: str = "dzienna"  # dzienna, nocna


class Location:
    """Bazowa klasa lokacji."""
    
    def __init__(self, name: str, location_type: LocationType):
        self.id = ""  # Will be set when added to locations dict
        self.name = name
        self.type = location_type
        self.description_day = ""
        self.description_night = ""
        self.items: List[Item] = []
        self.connections: Dict[str, str] = {}  # kierunek -> nazwa_lokacji
        self.prisoners: List[Prisoner] = []
        self.guards: List[Guard] = []
        self.secrets: List[Secret] = []
        self.is_locked: bool = False
        self.light_level: float = 1.0
        self.visited: bool = False
        self.special_features: List[str] = []
        self.interactive_objects: List[str] = []  # Obiekty do interakcji
    
    def get_description(self, time_system: TimeSystem, weather_system: WeatherSystem) -> str:
        """Zwraca opis lokacji zależny od pory dnia i pogody."""
        base_desc = self.description_day if time_system.is_day() else self.description_night
        
        # Dodaj informacje o porze dnia
        time_desc = f"\n{time_system.get_time_description()}"
        
        # Dodaj pogodę jeśli lokacja jest na zewnątrz
        weather_desc = ""
        if self.type == LocationType.COURTYARD:
            weather_desc = f"\n{weather_system.get_full_weather_description()}"
        
        # Dodaj informacje o strażnikach
        guard_desc = ""
        if self.guards:
            guard_count = len([g for g in self.guards if not g.shift != time_system.get_guard_shift()])
            if guard_count > 0:
                guard_desc = f"\n\nWidzisz {guard_count} strażnik{'a' if guard_count == 1 else 'ów'} na posterunku."
        
        # Dodaj informacje o więźniach
        prisoner_desc = ""
        if self.prisoners:
            awake = [p for p in self.prisoners if not p.is_sleeping]
            if awake:
                prisoner_desc = f"\n\nW pomieszczeniu {'jest' if len(awake) == 1 else 'są'} {len(awake)} {'więzień' if len(awake) == 1 else 'więźniowie'}."
        
        return base_desc + time_desc + weather_desc + guard_desc + prisoner_desc
    
    def get_exits(self) -> str:
        """Zwraca dostępne wyjścia."""
        if not self.connections:
            return "Nie ma żadnych wyjść!"
        
        exits = []
        for direction, destination in self.connections.items():
            exits.append(f"{direction} -> {destination}")
        
        return "Wyjścia: " + ", ".join(exits)
    
    def search(self) -> List[Item]:
        """Przeszukuje lokację w poszukiwaniu przedmiotów."""
        found_items = []
        for item in self.items:
            if not item.hidden or random.random() > 0.5:  # 50% szans na znalezienie ukrytego
                found_items.append(item)
                if item.hidden:
                    item.hidden = False  # Odkryty przedmiot nie jest już ukryty
        
        return found_items
    
    def check_secrets(self, action: str) -> Optional[Secret]:
        """Sprawdza czy akcja odkrywa sekret."""
        for secret in self.secrets:
            if not secret.discovered:
                # Sprawdź czy akcja pasuje do wymagań
                if action in secret.requirements.get('actions', []):
                    secret.discovered = True
                    return secret
        return None
    
    def get_neighbors(self) -> Dict[str, str]:
        """Zwraca sąsiednie lokacje."""
        return self.connections
    
    def get_exit_description(self, direction: str) -> str:
        """Zwraca opis wyjścia w danym kierunku."""
        if direction in self.connections:
            return f"W kierunku {direction} prowadzi przejście do {self.connections[direction]}"
        return f"Nie ma wyjścia w kierunku {direction}"
    
    def get_detailed_description(self, time_system: Optional[TimeSystem] = None) -> str:
        """Zwraca szczegółowy opis lokacji."""
        if time_system and time_system.get_hour() >= 20 or (time_system and time_system.get_hour() < 6):
            desc = self.description_night if self.description_night else self.description_day
        else:
            desc = self.description_day
        
        # Dodaj opisy przedmiotów
        if self.items:
            visible_items = [item for item in self.items if not item.hidden]
            if visible_items:
                desc += "\n\nWidoczne przedmioty: " + ", ".join([item.name for item in visible_items])
        
        # Dodaj opisy więźniów
        if self.prisoners:
            desc += f"\n\nW pomieszczeniu znajduje się {len(self.prisoners)} więźniów."
        
        return desc


class PrisonCell(Location):
    """Cela więzienna."""
    
    def __init__(self, number: int):
        super().__init__(f"Cela {number}", LocationType.CELL)
        self.number = number
        self.has_window = number in [1, 3, 5]  # Niektóre cele mają okna
        self.has_bed = True
        self.has_bucket = True  # Kubełek na odchody
        
        self._setup_cell()
    
    def _setup_cell(self):
        """Konfiguruje celę na podstawie numeru."""
        if self.number == 1:
            self.description_day = """Cela numer 1 - Cela Szeptów
Ciasna, wilgotna cela o ścianach pokrytych zielonkawym mchem, który pulsuje ledwo dostrzegalnie,
jakby oddychał. Słabe światło sączy się przez wąskie okienko pod sufitem, tworząc blade smugi
w zawieszonej w powietrzu mgle kurzu i pleśni. W rogu stoi przegniłe posłanie - słoma gnije
od dekad, wydając mdły, słodkawy zapach rozkładu. Gdy się poruszasz, spod niej uciekają
bledziutkie robaki, ślepe od życia w ciemności.

Na ścianie naprzeciwko drzwi widać dziesiątki - nie, setki wydrapanych kresek. Niektóre są
świeże, inne tak stare, że kamień wokół nich pokruszył się i osypał. Pomiędzy nimi, ledwo
widoczne w półmroku, wyryte są słowa w różnych językach. Jedno zdanie powtarza się obsesyjnie:
'NIE SŁUCHAJ SZEPTÓW'. Pod spodem ktoś inny dopisał drżącą ręką: 'Już za późno'.

W powietrzu wisi zapach strachu - kwaśny, metaliczny posmak, który osiada na języku. Czasem,
gdy wiatr zawieje przez okienko, zdaje się, że ściany faktycznie szepczą... ale to pewnie
tylko echo z innych cel. Prawda?"""
            
            self.description_night = """Cela numer 1 - Cela Szeptów
Całkowita ciemność pochłania celę jak żywa istota, pulsująca i głodna. Blade światło księżyca
wślizguje się przez okienko niczym widmowy palec, kreśląc na podłodze kształt kraty - czy to
światło, czy cienie więźniów, którzy tu umarli?

Wilgoć ścieka po ścianach z cichym szelestem, jakby coś pełzło w murach. Każda kropla wody
uderza o kamienną podłogę z rytmem przypominającym bicie serca - lub ostatnie oddechy konającego.
Wydrapane znaki na ścianie znikają w cieniu, ale czasem, gdy księżyc przesunie się za chmurę,
na moment wydają się świecić bladozielonym, chorobliwym światłem.

Z korytarza dochodzi echo kroków strażnika - ciężkich, miarowych, jak kroki kata idącego po
swoją ofiarę. Brzęk kluczy jest jak śmiech szaleńca. A potem... cisza. Ta cisza jest najgorsza,
bo w niej słychać szepty. Szepty w ścianach, mówiące rzeczy, których nie chcesz usłyszeć.
Rzeczy o tobie. Rzeczy, które znają twoje najciemniejsze sekrety."""
            
            # Obiekty do zbadania - każdy kryje historię
            self.interactive_objects = [
                "ściana z kreskami",
                "tajemnicze napisy", 
                "przegniłe posłanie",
                "wąskie okienko",
                "masywne drzwi",
                "podłoga",
                "sufit",
                "kąt celi",
                "szczeliny w murze"
            ]
            
            # Dźwięki ambiente zależne od pory
            self.ambient_sounds_day = [
                "Odległe krople wody odbijają się echem",
                "Szczur przemyka gdzieś w ścianie", 
                "Wiatr wyje przez okienko",
                "Ktoś kaszle w sąsiedniej celi"
            ]
            
            self.ambient_sounds_night = [
                "Coś drapie w ścianie... od wewnątrz",
                "Ciche szepty dobiegają z kątów celi",
                "Łańcuchy brzęczą mimo braku wiatru",
                "Daleki krzyk urywa się nagle"
            ]
            
            # Zapachy i atmosfera
            self.smells = [
                "Stęchlizna i pleśń",
                "Metaliczny posmak krwi",
                "Słodkawy zapach rozkładu",
                "Kwaśny pot strachu"
            ]
            
            # Sekret: Wiadomość na ścianie
            secret_message = Secret(
                id="cell1_message",
                name="Wydrapana wiadomość",
                description="""Na ścianie, ukryta między kreskami liczącymi dni, znajduje się wiadomość
wyryta różnymi charakterami pisma, jakby pisało ją kilka osób przez lata:

'Klucz mistrza leży tam, gdzie ogień nigdy nie gaśnie. Szukaj w piecu kuchennym.
Trzeci kamień od lewej, czwarty rząd od dołu. Strzeż się Jednookiego Marka!'

Pod spodem, inną ręką: 'Marek nie żyje. Zabiłem go. Teraz klucz jest mój.'
A jeszcze niżej, ledwo widoczne: 'Głupiec. Marek był najmniejszym problemem.'

Najświeższy napis, wydrapany paznokciami: 'Nie szukajcie klucza. Niektóre drzwi
powinny pozostać zamknięte. Naczelnik nie jest człowiekiem.'""",
                discovery_hint="Przyjrzyj się uważnie wydrapanym znakom na ścianie",
                requirements={'actions': ['zbadaj ścianę', 'czytaj napisy', 'oglądaj kreski']}
            )
            self.secrets.append(secret_message)
            
            # Przedmioty - każdy ma swoją mroczną historię
            self.items.extend([
                Item("kawałek metalu", 
                     "Ostry kawałek metalu, ukryty pod słomą. Rdza nie dotknęła krawędzi.",
                     examine_text="Wygląda jakby ktoś celowo go naostrzył o kamienie. Na powierzchni widać " +
                                 "zaschniętą krew. Czyją? Czym była strażnika, czy więźnia, który próbował uciec?"),
                Item("strzęp materiału",
                     "Brudny strzęp materiału, kiedyś był częścią koszuli.",
                     examine_text="Śmierdzi stęchlizną i strachem. Na brzegu widać ślady zębów - ktoś " +
                                 "gryzł materiał, żeby nie krzyczeć podczas tortur."),
                Item("miska",
                     "Gliniania miska z zaschniętymi resztkami strawy. Coś się w niej rusza.",
                     hidden=True,
                     examine_text="W zaschniętej breji widać białe robaki. Ale to nie wszystko - na dnie " +
                                 "miski ktoś wyrył małą mapę. Wygląda jak plan tuneli pod więzieniem."),
                Item("ludzki ząb",
                     "Pojedynczy ząb leżący w kącie celi.",
                     hidden=True,
                     examine_text="Ząb trzonowy, wyrwany z korzeniem. Na powierzchni widać dziwne nacięcia - " +
                                 "jakby ktoś coś na nim zapisał. Przy bliższym przyjrzeniu się: to data... jutrzejsza.") 
            ])
            
            # Więzień
            self.prisoners.append(Prisoner(
                name="Stary Grzegorz",
                description="Wychudzony starzec o długiej siwej brodzie. Jego oczy błyszczą szaleństwem, a ręce drżą nieustannie.",
                dialogue_day=[
                    "Oni... oni przychodzą nocą. Słyszysz ich? Szepty w ścianach...",
                    "Trzydzieści lat... albo może trzy? Czas nie istnieje w tym przeklętym miejscu.",
                    "Widziałem jak zabierają ludzi do Komnat Bólu. Nigdy nie wracają tacy sami."
                ],
                dialogue_night=[
                    "*szepcze* Ciii... słyszysz? Już idą. Kroki w ciemności...",
                    "*kołysze się w przód i tył* La la la... mama mówiła że jestem grzeczny...",
                    "*nagle łapie cię za rękę* Nie pozwól im zabrać swojej duszy! NIGDY!"
                ],
                mood="szalony"
            ))
            
        elif self.number == 2:
            self.description_day = """Cela numer 2 - Cela Krwi
Ta cela nosi ślady przemocy. Ciemne plamy na kamiennej podłodze i ścianach 
świadczą o krwawej przeszłości tego miejsca. Żelazne łańcuchy zwisają z sufitu, 
a na ścianie wiszą zardzewiałe kajdany. Posłanie jest rozerwane, jakby ktoś 
szukał w nim czegoś w desperacji. Mimo dnia, w tej celi panuje nieprzyjemny chłód."""
            
            self.description_night = """Cela numer 2 - Cela Krwi
W ciemności cela wydaje się jeszcze bardziej złowroga. Cienie tańczą na ścianach, 
a łańcuchy delikatnie brzęczą mimo braku wiatru. Plamy krwi wyglądają teraz 
jak czarne kałuże. Z daleka słychać jęki innych więźniów i szczęk metalu."""
            
            # Przedmioty
            self.items.extend([
                Item("łańcuch", "Ciężki żelazny łańcuch, może służyć jako broń lub narzędzie."),
                Item("kawałek kości", "Ludzka kość, wygląda na piszczel.", hidden=True, examine_text="Na kości widać ślady zębów."),
                Item("zardzewiały gwóźdź", "Duży, zardzewiały gwóźdź wyciągnięty z deski.")
            ])
            
            # Więzień
            self.prisoners.append(Prisoner(
                name="Krwawy Tomek",
                description="Potężnie zbudowany mężczyzna pokryty bliznami. Brakuje mu lewego oka, a twarz jest zdeformowana.",
                dialogue_day=[
                    "Patrz mi w oko gdy mówisz, szczeniaku.",
                    "Zabiłem siedmiu strażników zanim mnie ujęli. Siódmy był najsłodszy.",
                    "Chcesz przeżyć? Trzymaj się z daleka od naczelnika. To demon w ludzkiej skórze."
                ],
                dialogue_night=[
                    "*groźnie* Zbliż się jeszcze raz, a użyję twoich kości jako wykałaczek.",
                    "Śnią mi się ich krzyki... Muzyka dla moich uszu.",
                    "*śmieje się cicho* Wkrótce znów będzie jatka. Czuję to w powietrzu."
                ],
                mood="wrogi",
                has_quest=True
            ))
            
        elif self.number == 3:
            self.description_day = """Cela numer 3 - Cela Przemytników
Przestronna cela, wyraźnie lepsza od pozostałych. Posłanie ma prawdziwą siennik, 
a w rogu stoi drewniana skrzynia. Ściany są stosunkowo suche, a przez okno wpada 
sporo światła. Pod oknem zauważasz dziwne zadrapania w kamieniu, jakby ktoś 
próbował coś wykuć. W powietrzu unosi się słaby zapach tytoniu."""
            
            self.description_night = """Cela numer 3 - Cela Przemytników
Nocą cela wydaje się przytulna w porównaniu do reszty więzienia. Księżycowe światło 
oświetla podłogę, a przez okno widać gwiazdy. Zadrapania pod oknem wyglądają teraz 
jak mapa czy diagram. Z zewnątrz dochodzi pohukiwanie sowy i szum wiatru."""
            
            # Sekret: Ukryty tunel
            secret_tunnel = Secret(
                id="cell3_tunnel",
                name="Ukryty tunel",
                description="""Za luźnym kamieniem w ścianie odkrywasz wąski tunel!
Prowadzi w dół, w nieznane. Czuć z niego wilgoć i pleśń, ale też powiew świeżego powietrza.
Tunel jest wąski, ale człowiek może się przez niego przecisnąć. Ktoś musiał kopać go latami.""",
                discovery_hint="Sprawdź kamienie w ścianie pod oknem",
                requirements={'actions': ['zbadaj ścianę', 'sprawdź kamienie', 'szukaj przejścia']},
                rewards=[
                    Item("mapa tuneli", "Stara mapa pokazująca sieć tuneli pod więzieniem.", quest_item=True),
                    Item("kilof", "Mały kilof używany do kopania tunelu.")
                ]
            )
            self.secrets.append(secret_tunnel)
            
            # Przedmioty
            self.items.extend([
                Item("fajka", "Drewniana fajka, wciąż pachnie tytoniem."),
                Item("sakiewka", "Skórzana sakiewka z kilkoma miedziakami.", hidden=True),
                Item("nóż", "Mały nóż do obierania, dobrze ukryty.", hidden=True, examine_text="Ostrze jest ostre mimo rdzy."),
                Item("kawałek kredy", "Może służyć do pisania na ścianach.")
            ])
            
            # Więzień
            self.prisoners.append(Prisoner(
                name="Chudy Kazik",
                description="Szczupły mężczyzna o bystrych oczach i szybkich ruchach. Wygląda na kogoś, kto wie więcej niż mówi.",
                dialogue_day=[
                    "Handel kwitnie nawet w więzieniu, przyjacielu. Masz coś na wymianę?",
                    "Strażnicy... Każdy ma swoją cenę. Pytanie tylko jaką.",
                    "*szepcze* Słyszałem że szykuje się ucieczka. Ale to nie moja działka."
                ],
                dialogue_night=[
                    "*cicho* Najlepsze interesy robi się po zmroku.",
                    "Jeśli szukasz wyjścia, możemy porozmawiać o cenie...",
                    "Znam każdy zakamarek tego więzienia. Każdy ma swoją historię."
                ],
                mood="neutralny",
                has_quest=True
            ))
            
        elif self.number == 4:
            self.description_day = """Cela numer 4 - Cela Tortur
Najmniejsza i najgorsza z cel. Ściany są pokryte zaschniętą krwią i zarysowaniami 
po paznokciach. W rogu leżą połamane narzędzia tortur. Podłoga jest nachylona 
w stronę kratki ściekowej, zaprojektowana do spływania krwi. Smród rozkładu 
i strachu wisi w powietrzu. Nie ma tu okna, tylko wieczny półmrok."""
            
            self.description_night = """Cela numer 4 - Cela Tortur
W absolutnej ciemności cela staje się prawdziwym koszmarem. Każdy dźwięk jest 
wzmocniony, każdy oddech echem odbija się od ścian. Czujesz obecność tych, 
którzy tu cierpieli. Czasem wydaje ci się, że słyszysz ich szepty i błagania."""
            
            # Przedmioty
            self.items.extend([
                Item("szczypce", "Zardzewiałe szczypce do wyrywania paznokci.", examine_text="Wciąż widać na nich ślady krwi."),
                Item("igła", "Długa metalowa igła, używana do tortur."),
                Item("dziennik kata", "Mały notes z zapiskami o torturach.", hidden=True, quest_item=True,
                     examine_text="Zawiera opisy tortur i listę ofiar. Ostatni wpis mówi o 'specjalnym więźniu w celi 5'.")
            ])
            
            # Więzień
            self.prisoners.append(Prisoner(
                name="Milczący Johan",
                description="Mężczyzna bez języka, pokryty bliznami po torturach. Komunikuje się tylko gestami.",
                dialogue_day=[
                    "*pokazuje gestem na swoje usta i kręci głową*",
                    "*rysuje palcem na ziemi znak krzyża*",
                    "*wskazuje na ścianę i robi gest duszenia*"
                ],
                dialogue_night=[
                    "*kuląc się w rogu, drży ze strachu*",
                    "*pokazuje na drzwi i robi gest przecinania gardła*",
                    "*klaszcze trzy razy i pokazuje na sufit*"
                ],
                mood="przestraszony"
            ))
            
        elif self.number == 5:
            self.description_day = """Cela numer 5 - Cela Zapomnianych
Duża cela w najgłębszej części więzienia. Ściany są grube, ale w jednym miejscu 
widać pęknięcia i osypujący się tynk. Okno jest wysoko i zakratowane podwójnie. 
W celi znajdują się ślady po kilku posłaniach - kiedyś było tu więcej więźniów. 
Teraz pozostały tylko ich wydrapane na ścianach imiona i daty."""
            
            self.description_night = """Cela numer 5 - Cela Zapomnianych
Nocą cela wydaje się ogromna i pusta. Cienie zmarłych więźniów tańczą na ścianach. 
Przez pęknięcia w murze przedostaje się chłodny wiatr, niosąc ze sobą odległe 
dźwięki z zewnątrz. Czasem słychać szczury biegające w ścianach."""
            
            # Sekret: Słaby mur
            weak_wall = Secret(
                id="cell5_wall",
                name="Osłabiony mur",
                description="""Odkrywasz, że pęknięcia w murze są głębsze niż się wydawało!
Przy odpowiednim narzędziu można by wyłamać dziurę. Za murem czuć przeciąg - 
może to droga na wolność? Ale trzeba być ostrożnym, żeby nie zawaliła się cała ściana.""",
                discovery_hint="Zbadaj pęknięcia w ścianie",
                requirements={'actions': ['zbadaj mur', 'sprawdź pęknięcia', 'postukaj w ścianę']},
                rewards=[
                    Item("młot", "Ciężki młot ukryty w murze.", examine_text="Idealny do kruszenia kamienia."),
                    Item("lina", "Stara lina schowana w szczelinie.")
                ]
            )
            self.secrets.append(weak_wall)
            
            # Przedmioty
            self.items.extend([
                Item("księga", "Stara księga modlitewna, kartki są pożółkłe.", examine_text="Między kartkami znajdziesz wyrysowany plan więzienia."),
                Item("medalion", "Srebrny medalion z wizerunkiem świętego.", hidden=True),
                Item("list", "Niedokończony list pożegnalny.", quest_item=True,
                     examine_text="'Moja droga Mario, jeśli to czytasz, znaczy że nie żyję. Skarb ukryłem w...' - reszta jest nieczytelna.")
            ])
            
            # Więzień
            self.prisoners.append(Prisoner(
                name="Szlachetny Roland",
                description="Dawny rycerz w podartych szatach. Zachował dumną postawę mimo lat niewoli.",
                dialogue_day=[
                    "Honor jest jedynym, czego nie mogą mi odebrać.",
                    "Widziałem jak to więzienie łamie najsilniejszych. Ale nie mnie.",
                    "Naczelnik więzienia to potwór. Torturuje dla przyjemności, nie informacji."
                ],
                dialogue_night=[
                    "Modlę się każdej nocy o wybawienie. Dla nas wszystkich.",
                    "Słyszałem że planują egzekucję. Nie wiem czyją.",
                    "*szepcze* Jeśli chcesz uciec, musisz działać szybko. Czas ucieka."
                ],
                mood="przyjazny",
                has_quest=True
            ))
    
    def get(self, key: str, default=None):
        """Zwraca wartość atrybutu jak w słowniku."""
        return getattr(self, key, default)


class PrisonCorridor(Location):
    """Korytarz więzienny."""
    
    def __init__(self, name: str, section: str):
        super().__init__(name, LocationType.CORRIDOR)
        self.section = section  # północny, południowy, wschodni, zachodni, centralny
        self._setup_corridor()
    
    def _setup_corridor(self):
        """Konfiguruje korytarz."""
        if self.section == "centralny":
            self.description_day = """Główny Korytarz
Szeroki korytarz biegnący przez środek więzienia. Kamienne ściany są wilgotne, 
a z sufitu zwisają pajęczyny. Co kilka metrów wiszą kopcące pochodnie, rzucające 
migotliwe światło. Podłoga jest śliska od wilgoci i brudu. W powietrzu unosi się 
mieszanka zapachów: pleśni, moczu i strachu. Słychać echo kroków strażników 
i jęki więźniów dochodzące z cel."""
            
            self.description_night = """Główny Korytarz
Nocą korytarz jest oświetlony tylko nielicznymi pochodniami. Długie cienie 
tańczą na ścianach, tworząc groteskowe kształty. Echo każdego kroku niesie się 
daleko w ciszy. Gdzieś w oddali słychać krople wody i skrzypienie żelaza. 
Czasem przemknie szczur, jego oczy błyszczą w ciemności."""
            
            # Strażnicy
            self.guards.append(Guard(
                name="Strażnik Marek 'Jednooki'",
                description="Gruby strażnik z bliznią przez oko. Znany z okrucieństwa.",
                patrol_route=["korytarz_centralny", "korytarz_północny", "korytarz_południowy"],
                current_location="korytarz_centralny",
                equipment=["miecz", "klucze", "latarnia"],
                shift="dzienna"
            ))
            
            # Przedmioty
            self.items.extend([
                Item("pochodnia", "Płonąca pochodnia na ścianie.", can_take=False),
                Item("klucz", "Mały żelazny klucz leżący w kącie.", hidden=True, quest_item=True)
            ])
            
        elif self.section == "północny":
            self.description_day = """Północny Korytarz
Wąski korytarz prowadzący do cel 1 i 2. Ściany są pokryte mchem, a sufit 
jest niski, trzeba się schylać. Z cel dochodzą stłumione głosy i kaszel. 
Na końcu korytarza widać ciężkie dębowe drzwi prowadzące do kuchni."""
            
            self.description_night = """Północny Korytarz
Prawie całkowita ciemność panuje w tym korytarzu nocą. Tylko blade światło 
z głównego korytarza pozwala cokolwiek dostrzec. Czuć intensywny zapach 
stęchlizny i rozkładu. Co jakiś czas słychać szelest - może to szczury, 
a może coś gorszego."""
            
            # Połączenia
            self.connections = {
                "południe": "korytarz_centralny",
                "wschód": "cela_1",
                "zachód": "cela_2",
                "północ": "kuchnia"
            }
            
        elif self.section == "południowy":
            self.description_day = """Południowy Korytarz
Korytarz prowadzący do cel 3 i 4. Jest lepiej oświetlony niż pozostałe, 
z oknami wysoko w ścianie. Podłoga jest wyłożona starymi kamieniami, 
niektóre są poluzowane. Na ścianach wiszą zardzewiałe kajdany."""
            
            self.description_night = """Południowy Korytarz
Księżycowe światło wpada przez wysokie okna, tworząc sieć cieni na podłodze. 
Wiatr wyje przez szczeliny, brzmi jak jęki torturowanych. Kajdany na ścianach 
brzęczą delikatnie przy każdym podmuchu."""
            
            # Połączenia
            self.connections = {
                "północ": "korytarz_centralny",
                "wschód": "cela_3",
                "zachód": "cela_4",
                "południe": "zbrojownia"
            }
            
            # Przedmioty
            self.items.extend([
                Item("kamień", "Poluzowany kamień z podłogi.", examine_text="Pod kamieniem jest mała dziura, może coś tam schować.")
            ])
            
        elif self.section == "wschodni":
            self.description_day = """Wschodni Korytarz
Długi korytarz prowadzący do celi 5 i dziedzińca. Ściany noszą ślady wilgoci,
a w niektórych miejscach widać pęknięcia. Przez wąskie okienka wpada światło
dzienne, oświetlając kurz unoszący się w powietrzu. Stąd słychać odgłosy
z dziedzińca - kroki strażników i czasem brzęk broni."""
            
            self.description_night = """Wschodni Korytarz
Nocą korytarz jest ponury i cichy. Tylko echo własnych kroków towarzyszy
przechodniom. Przez okienka widać gwiazdy i czasem błysk latarni strażnika
na murach. Przeciągi wywołują dziwne szmery, jakby ktoś szeptał w ciemności."""
            
            # Połączenia
            self.connections = {
                "zachód": "korytarz_centralny",
                "północ": "cela_5",
                "wschód": "dziedziniec"
            }
            
            # Przedmioty
            self.items.extend([
                Item("kawałek kredy", "Biała kreda, można nią pisać na ścianach."),
                Item("stary but", "Zniszczony but więzienny.", hidden=True)
            ])
            
        elif self.section == "zachodni":
            self.description_day = """Zachodni Korytarz
Korytarz prowadzący do wartowni i jadalni. Jest lepiej utrzymany niż pozostałe,
z czystszymi ścianami i jaśniejszymi pochodniami. Tu przechodzą strażnicy
zmierzający na służbę. Na ścianach wiszą rozkazy i ogłoszenia. Z południa
dochodzi zapach jedzenia z jadalni."""
            
            self.description_night = """Zachodni Korytarz
Nocą korytarz jest pełen ruchu - strażnicy zmieniają warty, niosąc latarnie
i brzęcząc kluczami. Światło z wartowni rozjaśnia część korytarza. Słychać
głosy i śmiech dochodzący zza drzwi. Czasem więźniowie przemykają do jadalni
po dodatkowe racje."""
            
            # Połączenia
            self.connections = {
                "wschód": "korytarz_centralny",
                "zachód": "wartownia",
                "południe": "jadalnia"
            }
            
            # Przedmioty
            self.items.extend([
                Item("ogłoszenie", "Kartka z rozkazem naczelnika.", can_take=False,
                     examine_text="'Każdy więzień złapany poza celą po godzinie 22 zostanie ukarany chłostą.'"),
                Item("latarnia", "Zapasowa latarnia wisząca na haku.", hidden=True)
            ])


class PrisonCourtyard(Location):
    """Dziedziniec więzienny."""
    
    def __init__(self):
        super().__init__("Dziedziniec Więzienny", LocationType.COURTYARD)
        self._setup_courtyard()
    
    def _setup_courtyard(self):
        """Konfiguruje dziedziniec."""
        self.description_day = """Dziedziniec Więzienny
Przestronny dziedziniec otoczony wysokimi murami zwieńczonymi drutem kolczastym. 
W centrum stoi szubienica, jej stryczek kołysze się na wietrze jak złowieszcze 
wahadło. W rogu dziedzińca znajduje się studnia, przykryta ciężką kratą. 
Kamienne ławki są popękane i porośnięte mchem. Na murach stoją strażnicy 
z kuszami, obserwując każdy ruch. Słońce rzadko zagląda tutaj, wysokie mury 
rzucają długie cienie."""
        
        self.description_night = """Dziedziniec Więzienny
Nocą dziedziniec wygląda jak scena z koszmaru. Szubienica rzuca długi cień 
w świetle księżyca, a stryczek skrzypi złowieszczo. Pochodnie na murach 
ledwo rozpraszają ciemność. Strażnicy są bardziej czujni, ich sylwetki 
rysują się ostro na tle gwiezdnego nieba. Z oddali dochodzi wycie wilków 
i pohukiwanie sów. Czasem błyśnie oko strażnika patrząc w dół."""
        
        # Specjalne cechy
        self.special_features.extend([
            "szubienica",
            "studnia",
            "mury_obronne",
            "wieże_strażnicze"
        ])
        
        # Strażnicy
        self.guards.extend([
            Guard(
                name="Strażnik na murze wschodni",
                description="Strażnik z kuszą pilnujący wschodniego muru.",
                patrol_route=["mur_wschodni"],
                current_location="mur_wschodni",
                equipment=["kusza", "bełty", "róg alarmowy"]
            ),
            Guard(
                name="Strażnik na murze zachodni",
                description="Strażnik z kuszą pilnujący zachodniego muru.",
                patrol_route=["mur_zachodni"],
                current_location="mur_zachodni",
                equipment=["kusza", "bełty", "róg alarmowy"]
            )
        ])
        
        # Przedmioty
        self.items.extend([
            Item("lina", "Kawałek liny zwisający ze szubienicy.", examine_text="Solidna lina, może się przydać do wspinaczki."),
            Item("kamień", "Duży kamień nadający się do rzucania."),
            Item("wiadro", "Stare wiadro przy studni.", hidden=True)
        ])
        
        # Połączenia
        self.connections = {
            "północ": "biuro_naczelnika",
            "południe": "brama_główna",
            "wschód": "korytarz_wschodni",
            "zachód": "jadalnia"
        }


class PrisonKitchen(Location):
    """Kuchnia więzienna."""
    
    def __init__(self):
        super().__init__("Kuchnia Więzienna", LocationType.KITCHEN)
        self._setup_kitchen()
    
    def _setup_kitchen(self):
        """Konfiguruje kuchnię."""
        self.description_day = """Kuchnia Więzienna
Przestronna kuchnia wypełniona zapachem gotującej się zupy i pleśni. Wielki piec 
w rogu bucha ogniem, garnki bulgoczą na palenisku. Stoły robocze są pokryte 
resztkami warzyw i okruchami chleba. W kącie piętrzą się brudne naczynia. 
Na hakach wiszą kawałki mięsa o wątpliwej świeżości. Kucharz, gruby mężczyzna 
w brudnym fartuchu, miesza w garnku drewnianą łyżką. Przez okno wpada trochę 
światła, oświetlając unoszący się w powietrzu tłusty dym."""
        
        self.description_night = """Kuchnia Więzienna
Nocą kuchnia jest prawie pusta, tylko żar w piecu daje trochę światła. 
Cienie tańczą na ścianach, a od czasu do czasu coś skwierczy w garnku. 
Szczury śmielej wychodzą ze swoich kryjówek, szukając resztek. 
Zapach stęchłego tłuszczu miesza się z dymem. W rogu śpi pijany kucharz, 
chrapiąc głośno."""
        
        # Przedmioty
        self.items.extend([
            Item("nóż kuchenny", "Ostry nóż do krojenia mięsa.", examine_text="Dobrze wyważony, może służyć jako broń."),
            Item("bochenek chleba", "Czerstwy chleb, ale nadaje się do jedzenia."),
            Item("klucz do spiżarni", "Żelazny klucz wiszący na haku.", hidden=True, quest_item=True),
            Item("tłuczek do mięsa", "Ciężki drewniany tłuczek."),
            Item("worek mąki", "Duży worek z mąką.", can_take=False)
        ])
        
        # Sekret w piecu (związany z wiadomością z celi 1)
        master_key_secret = Secret(
            id="kitchen_master_key",
            name="Klucz mistrza",
            description="""W piecu, dokładnie tam gdzie wskazywała wiadomość, znajdujesz 
ukryty schowek! Trzeci kamień od lewej, czwarty rząd od dołu jest poluzowany. 
Za nim kryje się misternie wykonany klucz - Klucz Mistrza, otwierający większość 
zamków w więzieniu!""",
            discovery_hint="Sprawdź trzeci kamień od lewej, czwarty rząd od dołu w piecu",
            requirements={'actions': ['zbadaj piec', 'sprawdź kamienie', 'trzeci kamień']},
            rewards=[
                Item("klucz mistrza", "Uniwersalny klucz do większości cel i drzwi.", quest_item=True,
                     examine_text="Misternie wykonany klucz z dziwnymi symbolami.")
            ]
        )
        self.secrets.append(master_key_secret)
        
        # Kucharz (NPC)
        self.prisoners.append(Prisoner(
            name="Gruby Władek",
            description="Otyły kucharz o czerwonej twarzy. Zawsze spocony i brudny.",
            dialogue_day=[
                "Zupa dzisiaj wodnista, ale lepsza niż nic, co nie?",
                "Nie ruszaj mięsa! To dla strażników!",
                "Czasem dodaję do zupy specjalne przyprawy... *mruga*"
            ],
            dialogue_night=[
                "*chrapie głośno*",
                "*mamrocze przez sen* Nie... nie zjadłem tego kurczaka...",
                "*budzi się na moment* Co?! Kto tu?! A... znowu ty..."
            ],
            mood="neutralny"
        ))
        
        # Połączenia
        self.connections = {
            "południe": "korytarz_północny",
            "wschód": "jadalnia",
            "zachód": "spiżarnia"
        }


class PrisonArmory(Location):
    """Zbrojownia więzienna."""
    
    def __init__(self):
        super().__init__("Zbrojownia", LocationType.ARMORY)
        self.is_locked = True
        self._setup_armory()
    
    def _setup_armory(self):
        """Konfiguruje zbrojownię."""
        self.description_day = """Zbrojownia Więzienna
Pomieszczenie pełne broni i zbroi. Na ścianach wiszą miecze, topory i kusze. 
W rogu stoją stojaki z włóczniami i halabardami. Półki uginają się pod ciężarem 
hełmów i kolczug. Wszystko jest starannie utrzymane i naoliwione. Okno jest 
małe i wysoko, zakratowane potrójnie. W centrum pomieszczenia stoi ciężki 
stół z mapami więzienia i planami patroli."""
        
        self.description_night = """Zbrojownia Więzienna
W ciemności broń na ścianach wygląda groźnie. Ostrza błyszczą w słabym świetle 
latarni. Cienie sprawiają, że zbroje wyglądają jak stojący strażnicy. 
Przez okno wpada tylko blade światło księżyca, odbijające się w metalowych 
powierzchniach. Cisza jest przerywana tylko skrzypieniem metalu."""
        
        # Przedmioty (dostępne tylko po otwarciu)
        self.items.extend([
            Item("miecz", "Dobrze wyważony miecz strażnika.", quest_item=True),
            Item("kolczuga", "Lekka kolczuga, zapewnia podstawową ochronę."),
            Item("kusza", "Mała kusza z kilkoma bełtami."),
            Item("tarcza", "Drewniana tarcza z metalowym okuciami."),
            Item("hełm", "Prosty hełm strażnika."),
            Item("mapa więzienia", "Szczegółowa mapa całego kompleksu więziennego.", quest_item=True,
                 examine_text="Pokazuje tajne przejścia i słabe punkty w murach!")
        ])
        
        # Strażnik
        self.guards.append(Guard(
            name="Zbrojmistrz Klaus",
            description="Stary weteran z bliznami po wielu bitwach. Pilnuje zbrojowni jak oka w głowie.",
            patrol_route=["zbrojownia"],
            current_location="zbrojownia",
            equipment=["miecz dwuręczny", "ciężka zbroja", "klucze do zbrojowni"],
            alert_level=1  # Zawsze podejrzliwy
        ))
        
        # Połączenia
        self.connections = {
            "północ": "korytarz_południowy"
        }


class WardenOffice(Location):
    """Biuro naczelnika więzienia."""
    
    def __init__(self):
        super().__init__("Biuro Naczelnika", LocationType.OFFICE)
        self.is_locked = True
        self._setup_office()
    
    def _setup_office(self):
        """Konfiguruje biuro naczelnika."""
        self.description_day = """Biuro Naczelnika Więzienia
Luksusowe pomieszczenie kontrastujące z resztą więzienia. Podłoga wyłożona 
jest dywanami, a ściany ozdobione trofeami - głowami dzikich zwierząt 
i bronią. Za masywnym dębowym biurkiem stoi skórzany fotel. Na biurku 
piętrzą się dokumenty, pieczęcie i kałamarz. W rogu stoi szafa pancerna. 
Przez duże okno widać cały dziedziniec. Na ścianie wisi portret naczelnika - 
mężczyzny o okrutnych oczach i wąskich ustach."""
        
        self.description_night = """Biuro Naczelnika Więzienia
Nocą biuro wygląda jeszcze bardziej złowieszczo. Trofea na ścianach rzucają 
groteskowe cienie. Portret naczelnika wydaje się patrzeć za tobą. 
Światło świec odbija się w szklanym kałamarzu, tworząc dziwne refleksy. 
Z szafy pancernej dochodzi cichy tik mechanizmu. Przez okno widać pochodnie 
na dziedzińcu i patrolujących strażników."""
        
        # Przedmioty
        self.items.extend([
            Item("pieczęć naczelnika", "Oficjalna pieczęć, może otworzyć wiele drzwi.", quest_item=True),
            Item("lista więźniów", "Dokument z nazwiskami wszystkich więźniów.", 
                 examine_text="Przy niektórych nazwiskach widnieje czerwony krzyżyk..."),
            Item("klucz do szafy", "Mały złoty kluczyk.", hidden=True, quest_item=True),
            Item("dziennik naczelnika", "Osobisty dziennik naczelnika.", quest_item=True,
                 examine_text="Opisuje plany egzekucji i eksperymenty na więźniach. Ostatni wpis mówi o 'specjalnym rytuale' o północy."),
            Item("sztylet ceremonialny", "Bogato zdobiony sztylet z rubinami.", hidden=True)
        ])
        
        # Naczelnik (boss)
        self.guards.append(Guard(
            name="Naczelnik Wilhelm 'Krwawy'",
            description="Wysoki mężczyzna w czarnym mundurze. Jego oczy są zimne jak lód, a uśmiech nie sięga oczu.",
            patrol_route=["biuro_naczelnika", "dziedziniec", "komnata_tortur"],
            current_location="biuro_naczelnika",
            equipment=["miecz runiczny", "pistolet", "klucze uniwersalne", "różdżka tortur"],
            alert_level=2  # Zawsze w stanie alarmu
        ))
        
        # Sekret w szafie
        escape_plan_secret = Secret(
            id="office_escape_plan",
            name="Plan ucieczki",
            description="""W szafie pancernej znajdujesz nie tylko złoto i klejnoty, 
ale też dokumenty opisujące słabe punkty więzienia! Jest tu mapa kanałów, 
harmonogram zmian straży i lista przekupionych strażników. To bezcenne 
informacje dla planującej ucieczkę!""",
            discovery_hint="Otwórz szafę pancerną kluczem",
            requirements={'actions': ['otwórz szafę', 'użyj klucza do szafy']},
            rewards=[
                Item("plan ucieczki", "Kompletny plan ucieczki z więzienia.", quest_item=True),
                Item("sakwa złota", "Ciężka sakwa pełna złotych monet."),
                Item("przepustka", "Oficjalna przepustka pozwalająca opuścić więzienie.", quest_item=True)
            ]
        )
        self.secrets.append(escape_plan_secret)
        
        # Połączenia
        self.connections = {
            "południe": "dziedziniec",
            "wschód": "komnata_tortur",
            "zachód": "prywatne_komnaty"
        }


class PrisonGuardPost(Location):
    """Wartownia straży więziennej."""
    
    def __init__(self):
        super().__init__("Wartownia", LocationType.GUARD_POST)
        self._setup_guard_post()
    
    def _setup_guard_post(self):
        """Konfiguruje wartownię."""
        self.description_day = """Wartownia Straży
Ciasne pomieszczenie służące jako punkt kontrolny i miejsce odpoczynku strażników.
Ściany obwieszone są bronią i tarczami, a w rogu stoi piec grzewczy, przy którym
strażnicy ogrzewają się podczas zimnych nocy. Ciężki dębowy stół zajmuje centrum
pomieszczenia, zawalony kartami do gry, kośćmi i pustymi kufli po piwie.
Na ścianie wisi tablica z rozkładem patroli i portretami poszukiwanych zbiegów.
Przez małe okienko widać korytarz i część dziedzińca."""

        self.description_night = """Wartownia Straży
Nocą wartownia tętni życiem - strażnicy zmieniają się na warcie, grzejąc się
przy piecu i popijając grzane wino. Dym z fajek i cygar tworzy gęstą mgłę pod
sufitem. Przy stole toczy się hazardowa gra w kości, a przegrani klną głośno.
Na ławce w kącie drzemie zmęczony strażnik, jego chrapanie miesza się z trzaskiem
ognia w piecu. Światło latarni rzuca długie cienie na ściany pełne broni."""

        # Strażnicy
        self.guards.extend([
            Guard(
                name="Kapitan Straży Gunter",
                description="Doświadczony dowódca o bliźnie przez całą twarz. Surowy ale sprawiedliwy.",
                patrol_route=["wartownia", "korytarz_zachodni", "dziedziniec"],
                current_location="wartownia",
                equipment=["miecz oficerski", "róg alarmowy", "klucze kapitana"],
                shift="dzienna"
            ),
            Guard(
                name="Strażnik Piotr",
                description="Młody strażnik, wciąż uczący się rzemiosła. Nerwowy i łatwo go przestraszyć.",
                patrol_route=["wartownia"],
                current_location="wartownia",
                equipment=["krótki miecz", "tarcza"],
                shift="nocna"
            )
        ])

        # Przedmioty
        self.items.extend([
            Item("kości do gry", "Komplet kości używanych przez strażników do hazardu."),
            Item("butelka wina", "Na wpół pełna butelka taniego wina.", 
                 examine_text="Mocno rozcieńczone, ale strażnicy i tak je piją."),
            Item("lista patroli", "Harmonogram dzisiejszych patroli.", quest_item=True,
                 examine_text="Strażnicy zmieniają się co 3 godziny. Najmniej strażników jest między 2 a 4 w nocy."),
            Item("klucze zapasowe", "Zapasowy komplet kluczy do cel.", hidden=True, quest_item=True),
            Item("latarnia", "Oliwna latarnia dająca jasne światło."),
            Item("pałka", "Drewniana pałka używana do pacyfikacji więźniów.")
        ])

        # Połączenia
        self.connections = {
            "wschód": "korytarz_zachodni"
        }


class PrisonPantry(Location):
    """Spiżarnia więzienna."""
    
    def __init__(self):
        super().__init__("Spiżarnia", LocationType.KITCHEN)
        self.is_locked = True  # Zwykle zamknięta
        self._setup_pantry()
    
    def _setup_pantry(self):
        """Konfiguruje spiżarnię."""
        self.description_day = """Spiżarnia Więzienna
Chłodne pomieszczenie wypełnione po brzegi zapasami żywności. Na półkach
piętrzą się worki mąki, beczki z kiszoną kapustą i solone mięso w kadziach.
W kącie stoją beczułki z piwem i octem. Sufit obwieszony jest wędzonym mięsem
i kiełbasami, niektóre pokryte już białym nalotem. Zapach stęchlizny miesza się
z ostrym aromatem przypraw i soli. Małe okienko pod sufitem zapewnia wentylację,
ale światło ledwo dociera do wszystkich zakamarków. Szczury przemykają między
workami, szukając łatwego posiłku."""

        self.description_night = """Spiżarnia Więzienna
W ciemności spiżarnia wydaje się pełna życia - szelest szczurów jest głośniejszy,
a ich czerwone oczka błyszczą w mroku. Zapach gnijącego jedzenia staje się
intensywniejszy. Cienie sprawiają, że wiszące mięsa wyglądają jak wisielcy.
Przez szpary w drzwiach wpada blade światło z kuchni. Co jakiś czas coś spada
z półki z głośnym hukiem. Wilgoć skrapla się na ścianach, tworząc kałuże na
kamiennej podłodze."""

        # Przedmioty
        self.items.extend([
            Item("ser pleśniowy", "Duża forma sera pokryta zieloną pleśnią.", 
                 examine_text="Pod pleśnią ser wygląda całkiem jadalnie."),
            Item("suszone mięso", "Twarde jak kamień paski suszonego mięsa."),
            Item("worek ziarna", "Ciężki worek z ziarnem, częściowo zjedzony przez szczury.", can_take=False),
            Item("beczka piwa", "Drewniana beczka z kwaśnym piwem.", can_take=False),
            Item("trucizna na szczury", "Mała buteleczka z czarną czaszką na etykiecie.", hidden=True,
                 examine_text="Silna trucizna. Kilka kropel wystarczy, by zabić człowieka."),
            Item("przyprawy", "Woreczek z rzadkimi przyprawami z południa.", 
                 examine_text="Warte fortunę na czarnym rynku."),
            Item("księga rachunkowa", "Notes z zapiskami o zapasach.", hidden=True,
                 examine_text="Ktoś systematycznie kradnie jedzenie. Braki są ukrywane w księgach.")
        ])

        # Sekret - ukryta skrytka
        hidden_stash = Secret(
            id="pantry_stash",
            name="Tajna skrytka",
            description="""Za luźną cegłą w ścianie odkrywasz małą skrytkę!
Ktoś ukrywał tu cenne przedmioty - prawdopodobnie kucharz handlował
z więźniami. Znajdujesz tu małą sakiewkę ze złotem i kilka cennych
przedmiotów skradzionych strażnikom.""",
            discovery_hint="Sprawdź ściany za beczkami",
            requirements={'actions': ['zbadaj ścianę', 'przesuń beczki', 'szukaj skrytki']},
            rewards=[
                Item("sakiewka złota", "Skórzany mieszek pełen złotych monet."),
                Item("pierścień strażnika", "Sygnet z herbem kapitana straży.", quest_item=True),
                Item("fiolka z antidotum", "Uniwersalne antidotum na trucizny.")
            ]
        )
        self.secrets.append(hidden_stash)

        # Połączenia
        self.connections = {
            "wschód": "kuchnia"
        }


class TortureChamber(Location):
    """Komnata tortur."""
    
    def __init__(self):
        super().__init__("Komnata Tortur", LocationType.OFFICE)
        self.is_locked = True
        self._setup_torture_chamber()
    
    def _setup_torture_chamber(self):
        """Konfiguruje komnatę tortur."""
        self.description_day = """Komnata Tortur
Przerażające pomieszczenie, gdzie więźniowie poznają prawdziwe znaczenie bólu.
W centrum stoi żelazna dziewica - pionowa trumna z kolcami od wewnątrz. Obok
znajduje się stół do rozciągania z kołowrotkami i łańcuchami. Ściany zawieszone
są narzędziami tortur: kleszczami, szpikulcami, batami i hakami. W rogu pali się
piec rozgrzewający żelazne pręty do czerwoności. Podłoga jest nachylona ku kratce
ściekowej, ciemnej od zaschniętej krwi. Mimo otwartego okna, smród śmierci i
strachu wisi w powietrzu jak gęsta mgła."""

        self.description_night = """Komnata Tortur
Nocą komnata staje się sceną z najgorszych koszmarów. Czerwona poświata z pieca
rzuca makabryczne cienie na ściany. Narzędzia tortur wyglądają jak szpony
demonów czyhające na ofiary. Z żelaznej dziewicy dochodzi cichy jęk - może to
tylko wiatr, a może echo dawnych ofiar. Krople krwi kapią rytmicznie do kratki,
tworząc hipnotyzujący rytm. Czasem rozlega się krzyk z sąsiednich cel, przypominając
o przeznaczeniu tego miejsca."""

        # Przedmioty
        self.items.extend([
            Item("kleszcze rozżarzone", "Metalowe kleszcze wciąż gorące od pieca.", 
                 examine_text="Używane do wyrywania paznokci i zębów."),
            Item("bicz z kolcami", "Skórzany bicz zakończony metalowymi kolcami."),
            Item("księga tortur", "Ilustrowany podręcznik technik tortur.", quest_item=True,
                 examine_text="Ostatni rozdział opisuje 'Rytuał Oczyszczenia' - tajemną ceremonię naczelnika."),
            Item("fiolka z kwasem", "Szklana fiolka z żrącym kwasem.", 
                 examine_text="Jedna kropla potrafi wypalić dziurę w skórze."),
            Item("maska hanby", "Żelazna maska z kolcami od wewnątrz.", hidden=True),
            Item("klucz do kajdan", "Uniwersalny klucz pasujący do wszystkich kajdan.", hidden=True, quest_item=True)
        ])

        # Kat
        self.guards.append(Guard(
            name="Mistrz Tortur Heinrich",
            description="Olbrzymi mężczyzna w skórzanym fartuchu poplamionym krwią. Jego twarz jest pozbawiona emocji.",
            patrol_route=["komnata_tortur"],
            current_location="komnata_tortur",
            equipment=["nóż do skórowania", "młot", "kleszcze"],
            alert_level=0  # Skupiony na swojej pracy
        ))

        # Więzień na stole tortur
        self.prisoners.append(Prisoner(
            name="Torturowany Więzień",
            description="Ledwo żywy człowiek przykuty do stołu tortur. Jego ciało pokryte jest ranami.",
            dialogue_day=[
                "*jęczy z bólu* Proszę... zabij mnie...",
                "*szepcze* On... on nie jest człowiekiem... naczelnik...",
                "*krzyczy* NIE! NIE WIĘCEJ! POWIEM WSZYSTKO!"
            ],
            dialogue_night=[
                "*majaczy* Widziałem... portal... demony...",
                "*płacze* Mama... chcę do mamy...",
                "*nagle łapie cię za rękę* Uciekaj! Północ... rytuał... wszyscy zginiemy!"
            ],
            mood="umierający"
        ))

        # Połączenia
        self.connections = {
            "zachód": "biuro_naczelnika",
            "południe": "lochy"
        }


class DungeonCells(Location):
    """Lochy - najgorsze cele więzienia."""
    
    def __init__(self):
        super().__init__("Lochy", LocationType.CELL)
        self._setup_dungeons()
    
    def _setup_dungeons(self):
        """Konfiguruje lochy."""
        self.description_day = """Lochy - Karcer
Najgłębsza i najmroczniejsza część więzienia. Wilgotne kamienne cele wykute
w litej skale, bez okien i prawie bez światła. Woda sączy się ze ścian, tworząc
kałuże na podłodze. Powietrze jest ciężkie i trudne do oddychania, przesycone
zapachem rozkładu i rozpaczy. W celach nie ma posłań - tylko mokra słoma i łańcuchy
w ścianach. Szczury biegają swobodnie, niektóre wielkości kotów. Z głębi lochów
dochodzą nieludzkie jęki i szaleńczy śmiech. Tu trafiają ci, których naczelnik
chce złamać całkowicie."""

        self.description_night = """Lochy - Karcer  
W nocy lochy stają się prawdziwym piekłem. Absolutna ciemność pochłania wszystko,
tylko czasem błyśnie oko szczura. Krople wody uderzające o kamień tworzą
maddening rytm. Jęki więźniów mieszają się w koszmarną symfonię cierpienia.
Czasem słychać łańcuchy i coś wielkiego poruszającego się w najgłębszych celach -
miejscach, gdzie trzymane są rzeczy, które nie powinny istnieć. Temperatura spada,
a wilgoć przenika do kości. Niektórzy mówią, że w lochach czas płynie inaczej -
godzina może trwać jak dzień."""

        # Przedmioty
        self.items.extend([
            Item("ludzkie kości", "Stos kości poprzednich więźniów.", 
                 examine_text="Niektóre noszą ślady ogryzania."),
            Item("szaleńcze zapiski", "Kawałki skóry pokryte krwawymi napisami.", quest_item=True,
                 examine_text="'NIE ŚPIJ NIE ŚPIJ NIE ŚPIJ ON PRZYCHODZI WE ŚNIE'"),
            Item("dziwny amulet", "Kamienny amulet o niepokojącym kształcie.", hidden=True,
                 examine_text="Pulsuje delikatnie i jest ciepły w dotyku. Emanuje złą energią."),
            Item("rdzewiejące kajdany", "Stare kajdany, można je złamać przy odrobinie siły."),
            Item("czaszka", "Ludzka czaszka z dziurą w czole.", 
                 examine_text="Wygląda jakby coś przebiło ją od środka.")
        ])

        # Szalony więzień
        self.prisoners.append(Prisoner(
            name="Bezimienny Szaleniec",
            description="Nagi, wychudzony człowiek o dzikich oczach. Nie wiadomo jak długo tu jest.",
            dialogue_day=[
                "*rechocze* Ściany mają oczy! OCZY! Patrzą, zawsze patrzą!",
                "*szepcze* Zjadłem ich wszystkich... byli pyszni... hehehe...",
                "Północ! O północy otwiera się brama! Widziałem! WIDZIAŁEM!"
            ],
            dialogue_night=[
                "*wyje jak zwierzę* AAAAAAAAAAHHHHHHH!",
                "*gryzie własne ręce* Krew... muszą mieć krew... inaczej przyjdą...",
                "*nagle poważnieje* Naczelnik nie jest człowiekiem. To demon. Zabij go srebrnym sztyletem."
            ],
            mood="szalony"
        ))

        # Sekret - tajne przejście
        hidden_passage = Secret(
            id="dungeon_passage",
            name="Tajne przejście",
            description="""W najciemniejszym kącie lochów odkrywasz ukryte przejście!
Za ruchomym kamieniem kryje się wąski tunel prowadzący jeszcze głębiej.
Czuć z niego dziwny, słodkawy zapach i słychać odgłosy rytualnego śpiewu.
To musi prowadzić do sekretnej komnaty naczelnika!""",
            discovery_hint="Zbadaj najciemniejszy kąt lochów",
            requirements={'actions': ['zbadaj kąt', 'szukaj przejścia', 'pchnij kamień']},
            rewards=[
                Item("srebrny sztylet", "Święcony sztylet mogący ranić demony.", quest_item=True),
                Item("księga zaklęć", "Stara księga z rytuałami ochronnymi.", quest_item=True)
            ]
        )
        self.secrets.append(hidden_passage)

        # Połączenia
        self.connections = {
            "północ": "komnata_tortur",
            "wschód": "kanały"  # Sekretne przejście do kanałów
        }


class PrivateQuarters(Location):
    """Prywatne komnaty naczelnika."""
    
    def __init__(self):
        super().__init__("Prywatne Komnaty", LocationType.OFFICE)
        self.is_locked = True
        self._setup_quarters()
    
    def _setup_quarters(self):
        """Konfiguruje prywatne komnaty."""
        self.description_day = """Prywatne Komnaty Naczelnika
Luksusowe pomieszczenie urządzone z przepychem niespodziewanym w więzieniu.
Duże łoże z baldachimem i jedwabnymi prześcieradłami dominuje przestrzeń.
Ściany pokryte są gobelinami przedstawiającymi sceny tortur i egzekucji.
W rogu stoi mahoniowa szafa pełna wykwintnych szat. Przy oknie znajduje się
toaletka z lustrem w złotej ramie i kolekcją perfum. Na nocnym stoliku leży
dziwna czarna księga emanująca złowrogą aurą. Przez duże okno wpada światło,
oświetlając bogato zdobiony dywan. Mimo luksusu, w powietrzu czuć zapach siarki."""

        self.description_night = """Prywatne Komnaty Naczelnika
Nocą komnata nabiera złowieszczego charakteru. Cienie od świec tańczą po
gobelinach, ożywiając sceny tortur. Lustro odbija światło w dziwny sposób,
czasem pokazując rzeczy, których nie ma w pokoju. Czarna księga na stoliku
zdaje się pulsować własnym, wewnętrznym światłem. Z szafy dochodzi ciche
skrzypienie, jakby ktoś się w niej ukrywał. Zapach siarki jest silniejszy,
mieszając się z wonią kadzideł. Czasem słychać szepty w nieznanym języku."""

        # Przedmioty
        self.items.extend([
            Item("czarna księga", "Księga oprawiona w ludzką skórę.", quest_item=True,
                 examine_text="'Necronomicon' - księga zakazanych rytuałów. Ostatni rozdział opisuje przywoływanie demona."),
            Item("szkatuła z biżuterią", "Pełna drogich klejnotów szkatuła."),
            Item("dziwny puchar", "Srebrny puchar z dziwnymi runami.", hidden=True,
                 examine_text="Wewnątrz są ślady zaschniętej krwi. Używany do rytualnych celów."),
            Item("list miłosny", "Perfumowany list od tajemniczej damy.", hidden=True,
                 examine_text="'Mój ukochany demonie... Wkrótce się spotkamy, gdy brama się otworzy...'"),
            Item("sztylet rytualny", "Kościany sztylet z rubinowym oczkiem.", quest_item=True),
            Item("amulet ochronny", "Złoty amulet chroniący przed złem.", hidden=True)
        ])

        # Sekret - ukryte przejście do komnaty rytualnej
        ritual_room_secret = Secret(
            id="quarters_ritual_room",
            name="Przejście do komnaty rytualnej",
            description="""Przesuwając gobelin odkrywasz ukryte drzwi!
Za nimi kryją się schody prowadzące w dół, do tajemnej komnaty rytualnej.
Czuć stamtąd siarkę i krew. Na ścianach schodów wyryte są bluźniercze symbole.
To tutaj naczelnik odprawia swoje mroczne rytuały!""",
            discovery_hint="Sprawdź gobeliny na ścianach",
            requirements={'actions': ['zbadaj gobelin', 'przesuń gobelin', 'szukaj drzwi']},
            rewards=[
                Item("klucz do komnaty rytualnej", "Ozdobny klucz z czaszką na główce.", quest_item=True),
                Item("zwój ochronny", "Magiczny zwój chroniący przed demonami.", quest_item=True)
            ]
        )
        self.secrets.append(ritual_room_secret)

        # Połączenia
        self.connections = {
            "wschód": "biuro_naczelnika",
            "dół": "komnata_rytualna"  # Sekretne przejście
        }


class PrisonGate(Location):
    """Główna brama więzienia."""
    
    def __init__(self):
        super().__init__("Brama Główna", LocationType.COURTYARD)
        self.is_locked = True  # Zawsze zamknięta
        self._setup_gate()
    
    def _setup_gate(self):
        """Konfiguruje bramę główną."""
        self.description_day = """Brama Główna Więzienia
Potężna brama z kutego żelaza, jedyne oficjalne wyjście z tego przeklętego miejsca.
Dwa masywne skrzydła bramy są wzmocnione grubymi belkami i okuciami. Po bokach
wznoszą się kamienne wieże strażnicze z łucznikami czuwającymi dzień i noc.
Przed bramą rozciąga się wąski most nad głęboką fosą. Mechanizm podnoszący most
jest widoczny w lewej wieży. Nad bramą wisi żelazna krata - dodatkowe zabezpieczenie.
Na murach widać kotły ze smołą, gotowe wylać wrzącej cieczy na intruzów.
Herb królestwa wyryty w kamieniu patrzy groźnie na wszystkich przechodzących."""

        self.description_night = """Brama Główna Więzienia
Nocą brama wygląda jak wejście do piekła. Pochodnie rzucają złowieszcze światło
na kutą stal, a cienie od krat tworzą na ziemi wzór przypominający pajęczą sieć.
Strażnicy na wieżach są bardziej czujni, ich kusze błyszczą w świetle księżyca.
Most trzeszczy przy każdym podmuchu wiatru. Z fosy dochodzi zapach stojącej wody
i rozkładu - mówią, że pływają tam ciała nieudanych uciekinierów. Czasem słychać
wycie wilków z lasu za bramą - wolność tak blisko, a jednocześnie tak daleko."""

        # Strażnicy - elita
        self.guards.extend([
            Guard(
                name="Dowódca Bramy Viktor",
                description="Weteran wielu wojen, nieugięty i nieprzekupny.",
                patrol_route=["brama_główna"],
                current_location="brama_główna",
                equipment=["miecz dwuręczny", "ciężka zbroja", "róg alarmowy", "klucze do bramy"],
                alert_level=2  # Zawsze czujny
            ),
            Guard(
                name="Łucznik na wieży wschodniej",
                description="Celny strzelec potrafiący trafić muchę z 50 metrów.",
                patrol_route=["wieża_wschodnia"],
                current_location="wieża_wschodnia",
                equipment=["długi łuk", "kołczan strzał", "sztylet"],
                alert_level=2
            ),
            Guard(
                name="Łucznik na wieży zachodniej",
                description="Drugi strzelec, równie zabójczy co pierwszy.",
                patrol_route=["wieża_zachodnia"],
                current_location="wieża_zachodnia",
                equipment=["długi łuk", "kołczan strzał", "sztylet"],
                alert_level=2
            )
        ])

        # Przedmioty
        self.items.extend([
            Item("łańcuch od mostu", "Gruby łańcuch mechanizmu podnoszącego most.", can_take=False,
                 examine_text="Przecięcie go spowodowałoby opuszczenie mostu."),
            Item("lina strażnicza", "Długa lina zwisająca z wieży.", 
                 examine_text="Mogłaby posłużyć do wspinaczki."),
            Item("kamień z herbem", "Luźny kamień z wyrytym herbem.", hidden=True,
                 examine_text="Za kamieniem jest mała skrytka z kluczem.")
        ])

        # Połączenia
        self.connections = {
            "północ": "dziedziniec",
            "południe": "droga_na_wolność"  # Cel ucieczki!
        }


class PrisonCanteen(Location):
    """Jadalnia dla więźniów."""
    
    def __init__(self):
        super().__init__("Jadalnia Więźniów", LocationType.KITCHEN)
        self._setup_canteen()
    
    def _setup_canteen(self):
        """Konfiguruje jadalnię."""
        self.description_day = """Jadalnia Więźniów
Duża sala z długimi drewnianymi stołami i ławkami, gdzie więźniowie spożywają
swoje nędzne posiłki. Stoły noszą ślady wielu lat użytkowania - zadrapania,
nacięcia i wypalenia. Na ścianach widać zaschłe plamy jedzenia z dawnych bójek.
W rogu stoi beczka z wodą o wątpliwej czystości. Okna są wysoko i zakratowane,
ledwo wpuszczając światło. Zapach kwaśnej zupy i niemytych ciał wisi w powietrzu.
Przy ścianie ustawione są drewniane miski i łyżki - każdy więzień ma swoją.
Echo rozmów odbija się od kamiennych ścian."""

        self.description_night = """Jadalnia Więźniów  
Nocą jadalnia jest pusta i upiornie cicha. Długie stoły rzucają cienie jak
groby w świetle pojedynczej pochodni. Szczury śmiało biegają po stołach,
szukając okruchów. Czasem słychać krople wody kapiące z sufitu do misek.
Ławki skrzypią od przeciągów, jakby siedziały na nich duchy zmarłych więźniów.
W kącie coś szelesci - może to tylko wiatr, a może ktoś się ukrywa."""

        # Przedmioty
        self.items.extend([
            Item("drewniana miska", "Popękana miska z resztkami zupy."),
            Item("tępa łyżka", "Drewniana łyżka, można nią kopać.", 
                 examine_text="Koniec jest dziwnie zaostrzony - ktoś próbował zrobić z niej broń."),
            Item("kawałek chleba", "Spleśniały kawałek chleba ukryty pod stołem.", hidden=True),
            Item("list grypserski", "Mały świstek papieru z tajnymi znakami.", hidden=True, quest_item=True,
                 examine_text="'Spotkanie o północy w lochach. Przynieś broń. - K'"),
            Item("szpikulec", "Zaostrzony kawałek drewna.", hidden=True)
        ])

        # Więźniowie podczas posiłków
        self.prisoners.extend([
            Prisoner(
                name="Głodny Franek",
                description="Chudy jak szkielet więzień, zawsze szukający dodatkowej porcji.",
                dialogue_day=[
                    "Masz może coś do jedzenia? Cokolwiek?",
                    "Strażnicy kradną najlepsze kawałki. Nam zostają pomyje.",
                    "Słyszałem, że w spiżarni jest prawdziwe mięso. Ale pilnują jej jak skarbu."
                ],
                dialogue_night=[
                    "*jest tylko podczas posiłków*"
                ],
                mood="głodny"
            ),
            Prisoner(
                name="Kuchenny Pomocnik",
                description="Więzień pracujący w kuchni, ma dostęp do lepszego jedzenia.",
                dialogue_day=[
                    "*szepcze* Mogę ci załatwić dodatkową porcję... za odpowiednią cenę.",
                    "Widziałem co dodają do zupy strażników. Nie chciałbyś wiedzieć.",
                    "Kucharz trzyma klucze do spiżarni pod rondelm przy piecu."
                ],
                dialogue_night=[
                    "*jest tylko podczas posiłków*"
                ],
                mood="chciwy",
                has_quest=True
            )
        ])

        # Połączenia
        self.connections = {
            "zachód": "kuchnia",
            "północ": "korytarz_zachodni",
            "wschód": "dziedziniec",
            "południe": "cele_zbiorowe"
        }


class Prison:
    """Główna klasa zarządzająca całym więzieniem."""
    
    def __init__(self):
        """Inicjalizacja więzienia."""
        self.name = "Więzienie Początku"
        self.locations: Dict[str, Location] = {}
        self._current_location_name = "cela_1"  # Prywatny atrybut dla nazwy
        self.time_system = TimeSystem()
        self.weather_system = WeatherSystem()
        
        # Statystyki więzienia
        self.alert_level = 0  # 0-normalny, 1-podwyższony, 2-alarm, 3-lockdown
        self.discovered_secrets = []
        self.prisoner_reputation = 0  # -100 do 100
        
        # Wczytaj dane lokacji z JSON
        self.location_data = self._load_locations_from_json()
        
        self._create_locations()
        self._setup_connections()
    
    def _load_locations_from_json(self) -> Dict:
        """Wczytaj dane lokacji z pliku JSON."""
        try:
            with open('data/locations.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Ostrzeżenie: Nie znaleziono pliku locations.json")
            return {'locations': {}}
    
    def _create_locations(self):
        """Tworzy wszystkie lokacje więzienia."""
        # Cele
        for i in range(1, 6):
            cell = PrisonCell(i)
            cell.id = f"cela_{i}"
            self.locations[f"cela_{i}"] = cell
        
        # Korytarze
        self.locations["korytarz_centralny"] = PrisonCorridor("Główny Korytarz", "centralny")
        self.locations["korytarz_centralny"].id = "korytarz_centralny"
        self.locations["korytarz_północny"] = PrisonCorridor("Północny Korytarz", "północny")
        self.locations["korytarz_północny"].id = "korytarz_północny"
        self.locations["korytarz_południowy"] = PrisonCorridor("Południowy Korytarz", "południowy")
        self.locations["korytarz_południowy"].id = "korytarz_południowy"
        self.locations["korytarz_wschodni"] = PrisonCorridor("Wschodni Korytarz", "wschodni")
        self.locations["korytarz_wschodni"].id = "korytarz_wschodni"
        self.locations["korytarz_zachodni"] = PrisonCorridor("Zachodni Korytarz", "zachodni")
        self.locations["korytarz_zachodni"].id = "korytarz_zachodni"
        
        # Główne pomieszczenia
        self.locations["dziedziniec"] = PrisonCourtyard()
        self.locations["dziedziniec"].id = "dziedziniec"
        self.locations["kuchnia"] = PrisonKitchen()
        self.locations["kuchnia"].id = "kuchnia"
        self.locations["zbrojownia"] = PrisonArmory()
        self.locations["zbrojownia"].id = "zbrojownia"
        self.locations["biuro_naczelnika"] = WardenOffice()
        self.locations["biuro_naczelnika"].id = "biuro_naczelnika"
        
        # Nowe lokacje
        self.locations["wartownia"] = PrisonGuardPost()
        self.locations["wartownia"].id = "wartownia"
        self.locations["spiżarnia"] = PrisonPantry()
        self.locations["spiżarnia"].id = "spiżarnia"
        self.locations["komnata_tortur"] = TortureChamber()
        self.locations["komnata_tortur"].id = "komnata_tortur"
        self.locations["lochy"] = DungeonCells()
        self.locations["lochy"].id = "lochy"
        self.locations["prywatne_komnaty"] = PrivateQuarters()
        self.locations["prywatne_komnaty"].id = "prywatne_komnaty"
        self.locations["brama_główna"] = PrisonGate()
        self.locations["brama_główna"].id = "brama_główna"
        self.locations["jadalnia"] = PrisonCanteen()
        self.locations["jadalnia"].id = "jadalnia"
    
    def _setup_connections(self):
        """Ustawia połączenia między lokacjami."""
        # Korytarz centralny
        self.locations["korytarz_centralny"].connections = {
            "północ": "korytarz_północny",
            "południe": "korytarz_południowy", 
            "wschód": "korytarz_wschodni",
            "zachód": "korytarz_zachodni"
        }
        
        # Korytarz północny
        self.locations["korytarz_północny"].connections = {
            "południe": "korytarz_centralny",
            "wschód": "cela_1",
            "zachód": "cela_2",
            "północ": "kuchnia"
        }
        
        # Korytarz południowy  
        self.locations["korytarz_południowy"].connections = {
            "północ": "korytarz_centralny",
            "wschód": "cela_3",
            "zachód": "cela_4",
            "południe": "zbrojownia"
        }
        
        # Korytarz wschodni
        self.locations["korytarz_wschodni"].connections = {
            "zachód": "korytarz_centralny",
            "północ": "cela_5",
            "wschód": "dziedziniec"
        }
        
        # Korytarz zachodni
        self.locations["korytarz_zachodni"].connections = {
            "wschód": "korytarz_centralny",
            "zachód": "wartownia"
        }
        
        # Cele
        self.locations["cela_1"].connections = {"zachód": "korytarz_północny"}
        self.locations["cela_2"].connections = {"wschód": "korytarz_północny"}
        self.locations["cela_3"].connections = {"zachód": "korytarz_południowy"}
        self.locations["cela_4"].connections = {"wschód": "korytarz_południowy"}
        self.locations["cela_5"].connections = {"południe": "korytarz_wschodni"}
    
    def get_current_location(self) -> Location:
        """Zwraca aktualną lokację jako obiekt."""
        return self.locations.get(self._current_location_name)
    
    @property
    def current_location(self) -> str:
        """Zwraca nazwę aktualnej lokacji (dla kompatybilności)."""
        return self._current_location_name
    
    @current_location.setter
    def current_location(self, value: str):
        """Ustawia nazwę aktualnej lokacji."""
        self._current_location_name = value
    
    def move(self, direction: str) -> Tuple[bool, str]:
        """Przemieszcza się w danym kierunku."""
        current = self.get_current_location()
        
        if direction not in current.connections:
            return False, "Nie możesz iść w tym kierunku."
        
        destination_name = current.connections[direction]
        destination = self.locations.get(destination_name)
        
        if destination is None:
            return False, "Ta lokacja jeszcze nie istnieje."
        
        if destination.is_locked:
            return False, "Drzwi są zamknięte. Potrzebujesz klucza."
        
        # Sprawdź alert strażników
        if self.check_guard_detection():
            self.raise_alert()
            return False, "Strażnik cię zauważył! Alarm!"
        
        self._current_location_name = destination_name
        destination.visited = True
        
        # Aktualizuj czas
        self.time_system.advance_time(5)  # 5 minut na przejście
        
        return True, f"Przechodzisz do: {destination.name}"
    
    def check_guard_detection(self) -> bool:
        """Sprawdza czy strażnicy wykryli gracza."""
        current = self.get_current_location()
        
        for guard in current.guards:
            if guard.alert_level > 0:
                # Szansa na wykrycie zależna od poziomu alarmu
                detection_chance = 0.2 * guard.alert_level
                if random.random() < detection_chance:
                    return True
        
        return False
    
    def raise_alert(self):
        """Podnosi poziom alarmu w więzieniu."""
        self.alert_level = min(3, self.alert_level + 1)
        
        # Zwiększ czujność wszystkich strażników
        for location in self.locations.values():
            for guard in location.guards:
                guard.alert_level = min(2, guard.alert_level + 1)
    
    def interact_with_prisoner(self, prisoner_name: str) -> str:
        """Interakcja z więźniem."""
        current = self.get_current_location()
        
        for prisoner in current.prisoners:
            if prisoner.name.lower() == prisoner_name.lower():
                # Wybierz dialog zależny od pory dnia
                if self.time_system.is_day():
                    dialogues = prisoner.dialogue_day
                else:
                    dialogues = prisoner.dialogue_night
                
                if dialogues:
                    return f"{prisoner.name}: {random.choice(dialogues)}"
                else:
                    return f"{prisoner.name} nie ma nic do powiedzenia."
        
        return "Nie ma tu takiego więźnia."
    
    def search_location(self) -> List[Item]:
        """Przeszukuje aktualną lokację i zwraca listę znalezionych przedmiotów."""
        current = self.get_current_location()
        items = current.search()
        return items if items else []
    
    def examine(self, target: str) -> str:
        """Bada cel (przedmiot, ścianę, etc.)."""
        current = self.get_current_location()
        
        # Sprawdź przedmioty
        for item in current.items:
            if target.lower() in item.name.lower():
                if item.examine_text:
                    return item.examine_text
                else:
                    return item.description
        
        # Sprawdź sekrety
        secret = current.check_secrets(f"zbadaj {target}")
        if secret:
            self.discovered_secrets.append(secret.id)
            rewards_text = ""
            if secret.rewards:
                current.items.extend(secret.rewards)
                rewards_text = "\nZnajdujesz: " + ", ".join([r.name for r in secret.rewards])
            return f"ODKRYŁEŚ SEKRET!\n{secret.description}{rewards_text}"
        
        return f"Nie widzisz nic specjalnego w: {target}"
    
    def get_status(self) -> str:
        """Zwraca aktualny status więzienia."""
        current = self.get_current_location()
        
        status_parts = [
            f"Lokacja: {current.name}",
            f"Czas: {self.time_system.get_time_string()} ({self.time_system.get_time_period()})",
            f"Data: {self.time_system.get_date_string()}",
            f"Pogoda: {self.weather_system.get_weather_description()}",
            f"Poziom alarmu: {self.alert_level}/3",
            f"Odkryte sekrety: {len(self.discovered_secrets)}/3"
        ]
        
        return "\n".join(status_parts)
    
    def describe_current_location(self) -> str:
        """Opisuje aktualną lokację."""
        current = self.get_current_location()
        
        description = current.get_description(self.time_system, self.weather_system)
        exits = current.get_exits()
        
        return f"{description}\n\n{exits}"
    
    def advance_time(self, minutes: int = 10):
        """Przesuwa czas do przodu."""
        self.time_system.advance_time(minutes)
        self.weather_system.update(minutes)
        
        # Aktualizuj stan więźniów
        for location in self.locations.values():
            for prisoner in location.prisoners:
                # Więźniowie śpią w nocy
                prisoner.is_sleeping = self.time_system.is_night() and \
                                     self.time_system.get_hour() >= 22 or \
                                     self.time_system.get_hour() < 5
        
        # Ruch strażników
        if self.time_system.should_guards_patrol():
            self._move_guards()
    
    def _move_guards(self):
        """Przemieszcza strażników zgodnie z ich trasami."""
        for location in self.locations.values():
            for guard in location.guards:
                if len(guard.patrol_route) > 1:
                    # Znajdź następną lokację na trasie
                    current_index = guard.patrol_route.index(guard.current_location)
                    next_index = (current_index + 1) % len(guard.patrol_route)
                    guard.current_location = guard.patrol_route[next_index]