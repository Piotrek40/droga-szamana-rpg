"""
Czarny Las - pradawna puszcza pełna tajemnic i niebezpieczeństw.
Moduł lokacji dla systemu Droga Szamana RPG.
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


class ForestLocationType(Enum):
    """Typy lokacji w lesie."""
    CLEARING = "polana"
    DEEP_FOREST = "gęstwina"
    PATH = "ścieżka"
    GROVE = "gaj"
    RUINS = "ruiny"
    CAVE = "jaskinia"
    STREAM = "strumień"
    HOLLOW = "dziupla"


@dataclass
class ForestCreature:
    """Stworzenie zamieszkujące las."""
    name: str
    description: str
    danger_level: int  # 0-10
    is_hostile: bool
    is_nocturnal: bool
    loot: List[str] = field(default_factory=list)
    sounds: List[str] = field(default_factory=list)
    tracks: str = ""
    
    def get_activity(self, is_day: bool) -> str:
        """Zwraca opis aktywności stworzenia."""
        if self.is_nocturnal and is_day:
            return f"{self.name} śpi w ukryciu."
        elif not self.is_nocturnal and not is_day:
            return f"{self.name} odpoczywa."
        else:
            return f"{self.name} poluje w okolicy."


@dataclass
class ForestPlant:
    """Roślina rosnąca w lesie."""
    name: str
    description: str
    is_edible: bool
    is_poisonous: bool
    is_medicinal: bool
    harvest_season: str
    uses: List[str] = field(default_factory=list)
    location_preference: str = ""


@dataclass
class AncientSecret:
    """Starożytna tajemnica ukryta w lesie."""
    id: str
    name: str
    description: str
    discovery_conditions: Dict[str, Any]
    revelation: str
    power_granted: Optional[str] = None
    curse: Optional[str] = None
    guardians: List[str] = field(default_factory=list)


class ForestLocation:
    """Bazowa klasa dla lokacji w Czarnym Lesie."""
    
    def __init__(self, name: str, location_type: ForestLocationType):
        self.id = ""
        self.name = name
        self.type = location_type
        self.description_base = ""
        self.description_dawn = ""
        self.description_day = ""
        self.description_dusk = ""
        self.description_night = ""
        
        # Elementy środowiskowe
        self.flora: List[ForestPlant] = []
        self.fauna: List[ForestCreature] = []
        self.landmarks: List[str] = []
        self.hidden_items: List[Any] = []
        self.secrets: List[AncientSecret] = []
        
        # Stan lokacji
        self.is_corrupted = False  # Czy dotknięta Pustką
        self.mist_level = 0.0  # 0-1, poziom mgły
        self.danger_level = 3  # 1-10
        self.visited = False
        
        # Efekty środowiskowe
        self.ambient_sounds: List[str] = []
        self.smells: List[str] = []
        self.mystical_effects: List[str] = []
        
        # Połączenia
        self.connections: Dict[str, str] = {}
        self.hidden_paths: Dict[str, Tuple[str, str]] = {}  # Ukryte ścieżki (kierunek -> (cel, warunek))
    
    def get_description(self, time_system: TimeSystem, weather: WeatherSystem) -> str:
        """Zwraca opis zależny od pory dnia i pogody."""
        hour = time_system.get_hour()
        
        # Wybierz bazowy opis na podstawie pory dnia
        if 5 <= hour < 7:
            desc = self.description_dawn
        elif 7 <= hour < 17:
            desc = self.description_day
        elif 17 <= hour < 20:
            desc = self.description_dusk
        else:
            desc = self.description_night
        
        # Dodaj efekty pogodowe
        weather_desc = self._get_weather_effects(weather)
        
        # Dodaj poziom mgły
        if self.mist_level > 0.7:
            weather_desc += "\nGęsta mgła ogranicza widoczność do kilku metrów. Kształty drzew wyłaniają się jak duchy."
        elif self.mist_level > 0.3:
            weather_desc += "\nMgła snuje się między drzewami, nadając wszystkiemu nierealny wygląd."
        
        # Dodaj efekty Pustki jeśli lokacja jest skażona
        corruption_desc = ""
        if self.is_corrupted:
            corruption_desc = "\n\n⚠️ Czujesz niepokojącą obecność Pustki. Rzeczywistość wydaje się niestabilna."
        
        # Dodaj dźwięki i zapachy
        sensory_desc = self._get_sensory_description()
        
        return f"{desc}{weather_desc}{corruption_desc}\n\n{sensory_desc}"
    
    def _get_weather_effects(self, weather: WeatherSystem) -> str:
        """Zwraca opis efektów pogodowych."""
        current_weather = weather.current_weather
        
        if current_weather == WeatherType.RAIN:
            return "\n\nDeszcz bębni o liście, tworząc tysiące małych wodospadów. Ziemia zamienia się w błoto."
        elif current_weather == WeatherType.STORM:
            return "\n\nBurza szaleje nad lasem. Konary trzeszczą, a błyskawice rozświetlają ciemność."
        elif current_weather == WeatherType.SNOW:
            return "\n\nŚnieg pokrywa las białym całunem, tłumiąc wszystkie dźwięki. Świat wydaje się zamarły."
        elif current_weather == WeatherType.FOG:
            return "\n\nMgła wisi między drzewami jak zasłona, ukrywając ścieżki i niebezpieczeństwa."
        return ""
    
    def _get_sensory_description(self) -> str:
        """Zwraca opis dźwięków i zapachów."""
        desc_parts = []
        
        if self.ambient_sounds:
            sound = random.choice(self.ambient_sounds)
            desc_parts.append(f"🔊 {sound}")
        
        if self.smells:
            smell = random.choice(self.smells)
            desc_parts.append(f"👃 {smell}")
        
        if self.mystical_effects:
            effect = random.choice(self.mystical_effects)
            desc_parts.append(f"✨ {effect}")
        
        return "\n".join(desc_parts) if desc_parts else "Las jest niepokojąco cichy."
    
    def search_for_herbs(self, skill_level: int = 0) -> List[ForestPlant]:
        """Przeszukuje okolicę w poszukiwaniu ziół."""
        found_plants = []
        
        for plant in self.flora:
            # Szansa znalezienia zależy od umiejętności
            base_chance = 0.3 + (skill_level * 0.05)
            if plant.is_medicinal:
                base_chance += 0.1
            
            if random.random() < base_chance:
                found_plants.append(plant)
        
        return found_plants
    
    def check_for_danger(self) -> Optional[ForestCreature]:
        """Sprawdza czy nie czai się niebezpieczeństwo."""
        hostile_creatures = [c for c in self.fauna if c.is_hostile]
        
        if hostile_creatures and random.random() < (self.danger_level / 20):
            return random.choice(hostile_creatures)
        
        return None
    
    def reveal_secret(self, action: str, conditions: Dict[str, Any]) -> Optional[AncientSecret]:
        """Sprawdza czy akcja odkrywa tajemnicę."""
        for secret in self.secrets:
            if not secret.discovery_conditions:
                continue
                
            # Sprawdź warunki odkrycia
            conditions_met = True
            for key, value in secret.discovery_conditions.items():
                if key == "action" and action != value:
                    conditions_met = False
                elif key == "time" and conditions.get("time") != value:
                    conditions_met = False
                elif key == "item" and value not in conditions.get("inventory", []):
                    conditions_met = False
            
            if conditions_met:
                return secret
        
        return None


class DruidGrove(ForestLocation):
    """Święty krąg druidów."""
    
    def __init__(self):
        super().__init__("Krąg Druidów", ForestLocationType.GROVE)
        self._setup_grove()
    
    def _setup_grove(self):
        """Konfiguruje świętą polanę."""
        self.description_dawn = """Krąg Druidów - Świt Mocy
Poranna rosa pokrywa kamienne monolity, sprawiając że lśnią jak pokryte diamentami. 
Pierwsze promienie słońca przenikają przez korony drzew, rozpalając starożytne runy 
złotym blaskiem. Drzewo Tysiąca Lat w centrum polany budzi się do życia - jego liście 
szeleszczą mimo braku wiatru, jakby śpiewały poranną modlitwę.

Powietrze jest gęste od mocy, czujesz jak energia przepływa przez ziemię pod twoimi stopami.
Kamienie ułożone w idealny krąg pulsują delikatnie, rezonując z bijącym sercem lasu.
Między monolitami snują się cienkie nitki światła, tworząc mistyczną sieć ochronną."""
        
        self.description_day = """Krąg Druidów - Dzień Równowagi
Polana skąpana jest w filtrowanym przez liście świetle. Kamienne monolity rzucają 
precyzyjne cienie, które układają się w skomplikowany wzór na trawie - starożytny 
kalendarz i mapa gwiezdna jednocześnie. Drzewo Tysiąca Lat góruje nad wszystkim, 
jego pień szerszy niż trzy wozy, kora poorana tysiącem symboli i run.

Wokół kręgu rosną rzadkie zioła i kwiaty, niektóre nie spotykane nigdzie indziej 
w królestwie. Motyle o skrzydłach jak witraże tańczą w powietrzu, a pszczoły 
brzęczą melodię starszą niż pamięć człowieka. W centrum, u stóp wielkiego drzewa, 
znajduje się kamienny ołtarz pokryty mchem i plamami od ofiar z owoców i ziół."""
        
        self.description_dusk = """Krąg Druidów - Zmierzch Duchów
Gdy słońce chowa się za horyzontem, kamienie zaczynają świecić bladozielonym światłem 
od wewnątrz. Cienie wydłużają się i tańczą, przybierając kształty zwierząt i duchów lasu.
Drzewo Tysiąca Lat szepce w nieznanym języku, a jego liście brzęczą jak tysiące dzwoneczków.

Mgła unosi się z ziemi, ale nie wchodzi do kręgu - zatrzymuje się przy kamieniach 
jakby przed niewidzialną barierą. W tej mgle widać czasem sylwetki - duchy dawnych 
druidów pilnujących świętego miejsca. Powietrze pachnie kadzidłem i starą magią."""
        
        self.description_night = """Krąg Druidów - Noc Rytuałów
W świetle gwiazd krąg przemienia się w portal między światami. Konstelacje widoczne 
tylko z tego miejsca układają się na niebie w starożytne znaki. Kamienie pulsują 
rytmicznie, jakby oddychały, a runy płoną zimnym, błękitnym ogniem.

Drzewo Tysiąca Lat świeci od wewnątrz delikatną poświatą, jego korzenie fosforyzują 
pod ziemią, tworząc świetlistą sieć. Portal do innych wymiarów uchyla się - w powietrzu 
pojawiają się pęknięcia rzeczywistości, przez które widać inne światy, inne czasy.
Nocą to miejsce nie należy już całkowicie do tego świata."""
        
        # Flora święta
        self.flora = [
            ForestPlant(
                name="Księżycowy Kwiat",
                description="Delikatny kwiat świecący w nocy bladym światłem.",
                is_edible=False,
                is_poisonous=False,
                is_medicinal=True,
                harvest_season="pełnia",
                uses=["Leczenie ran duchowych", "Ochrona przed klątwami", "Wzmocnienie wizji"],
                location_preference="święte miejsca"
            ),
            ForestPlant(
                name="Krwawy Korzeń",
                description="Bulwa o czerwonym soku, używana w rytuałach.",
                is_edible=False,
                is_poisonous=True,
                is_medicinal=True,
                harvest_season="jesień",
                uses=["Trucizna", "Rytuały krwi", "Wzmocnienie siły"],
                location_preference="przy kamieniach"
            ),
            ForestPlant(
                name="Szept Wiatru",
                description="Trawa która szeleści nawet bez wiatru, przekazując wiadomości.",
                is_edible=False,
                is_poisonous=False,
                is_medicinal=False,
                harvest_season="wiosna",
                uses=["Komunikacja z naturą", "Wykrywanie kłamstw"],
                location_preference="centrum kręgu"
            )
        ]
        
        # Święte stworzenia
        self.fauna = [
            ForestCreature(
                name="Biały Jeleń",
                description="Majestatyczny jeleń o śnieżnobiałym futrze i złotych rogach. Duch opiekuńczy lasu.",
                danger_level=0,
                is_hostile=False,
                is_nocturnal=False,
                loot=[],
                sounds=["Dostojne ryczenie", "Tupot kopyt"],
                tracks="Ślady kopyt układające się w runiczne wzory"
            ),
            ForestCreature(
                name="Mądra Sowa",
                description="Ogromna sowa o przenikliwych złotych oczach. Widzi prawdę i przyszłość.",
                danger_level=0,
                is_hostile=False,
                is_nocturnal=True,
                loot=["Pióro mądrości"],
                sounds=["Pohukiwanie pełne znaczeń", "Szum skrzydeł"],
                tracks="Pióra niosące proroctwa"
            )
        ]
        
        # Starożytne tajemnice
        self.secrets = [
            AncientSecret(
                id="druid_initiation",
                name="Inicjacja Druida",
                description="Rytuał przyjęcia do kręgu druidów.",
                discovery_conditions={
                    "action": "medytuj",
                    "time": "pełnia",
                    "item": "liść Drzewa Tysiąca Lat"
                },
                revelation="""Drzewo przemawia do ciebie głosem tysiąca liści. Widzisz historię lasu,
                           narodziny i śmierć niezliczonych istnień. Czujesz połączenie z każdym
                           żywym stworzeniem w lesie. Jesteś teraz częścią wielkiej sieci życia.""",
                power_granted="Mowa zwierząt",
                guardians=["Stary Dąb - arcydruid"]
            ),
            AncientSecret(
                id="portal_to_void",
                name="Portal do Pustkowi",
                description="Ukryte przejście do krainy Pustki.",
                discovery_conditions={
                    "action": "użyj klucza pustki",
                    "time": "północ"
                },
                revelation="""Kamienie rozstępują się, odsłaniając wirującą czeluść czystego chaosu.
                           Za portalem widzisz Pustkowia - krainę gdzie rzeczywistość nie ma znaczenia.
                           Portal pulsuje głodem, chce cię wciągnąć.""",
                power_granted=None,
                curse="Dotyk Pustki - rzeczywistość wokół ciebie staje się niestabilna",
                guardians=["Strażnik Progu"]
            )
        ]
        
        # Efekty środowiskowe
        self.ambient_sounds = [
            "Szelest liści Drzewa Tysiąca Lat szepczących starożytne sekrety",
            "Brzęczenie pszczół tworzące melodię starszą niż cywilizacja",
            "Echo dalekiego rogu druidów wzywających do rytuału",
            "Cichy śpiew ziemi rezonującej z kamieniami mocy",
            "Trzask energii między monolitami"
        ]
        
        self.smells = [
            "Zapach kadzidła i świętych ziół",
            "Woń starego drewna i mchu",
            "Słodki aromat Księżycowych Kwiatów",
            "Metaliczny posmak magii w powietrzu",
            "Zapach świeżej rosy na trawie"
        ]
        
        self.mystical_effects = [
            "Włosy na karku stają dęba od energii miejsca",
            "Czujesz jak moc przepływa przez ziemię pod stopami",
            "Na moment widzisz aurę każdej żywej istoty wokół",
            "Słyszysz szepty duchów dawnych druidów",
            "Czas wydaje się płynąć wolniej w kręgu"
        ]
        
        # Połączenia
        self.connections = {
            "północ": "głęboki_las",
            "południe": "ścieżka_handlowa",
            "wschód": "święty_gaj",
            "zachód": "opuszczona_drwalnia"
        }
        
        self.hidden_paths = {
            "portal": ("pustkowia", "posiadanie klucza pustki"),
            "drzewo": ("kraina_snów", "wiedza druidów")
        }


class AbandonedLoggingCamp(ForestLocation):
    """Opuszczony obóz drwali."""
    
    def __init__(self):
        super().__init__("Opuszczona Drwalnia", ForestLocationType.RUINS)
        self.danger_level = 5
        self._setup_camp()
    
    def _setup_camp(self):
        """Konfiguruje opuszczony obóz."""
        self.description_dawn = """Opuszczona Drwalnia - Mglisty Świt
Poranna mgła snuje się między zrujnowanymi barakami, nadając im widmowy wygląd.
Zmurszałe drewno chat jest pokryte grubą warstwą mchu i porostów. Drzwi wiszą 
na zawiasach, skrzypiąc przy każdym podmuchu wiatru jak skargi umarłych.

Pośrodku obozu sterczą szczątki wielkiej piły tarczowej, jej zardzewiałe ostrze 
wciąż groźnie błyszczy w pierwszych promieniach słońca. Wokół walają się 
porzucone narzędzia - siekiery wbite w pnie, piły ręczne pochłonięte przez 
rdzę, łańcuchy oplecione bluszczem. Natura powoli odzyskuje to miejsce."""
        
        self.description_day = """Opuszczona Drwalnia - Dzień Zapomnienia
W świetle dnia widać pełen rozmiar zniszczenia. Dachy baraków zawaliły się, 
odsłaniając wnętrza pełne zgniłych mebli i osobistych rzeczy porzuconych 
w pośpiechu. Na ścianach wciąż wiszą portrety rodzin - twarze wyblakłe 
i nierozpoznawalne, oczy wydrapane lub wypalone.

Wielkie stosy pocięte drewna gniją pod gołym niebem, pokryte grzybami 
i mchem. Między deskami czają się pająki wielkości pięści, ich sieci 
błyszczą jak stal w słońcu. W warsztacie narzędzia wciąż leżą tak, jakby 
robotnicy mieli wrócić lada moment - ale warstwa kurzu i pajęczyn zdradza, 
że minęły lata od ostatniej zmiany."""
        
        self.description_dusk = """Opuszczona Drwalnia - Krwawy Zmierzch
Zachodzące słońce barwi obóz na czerwono, przypominając o krwawej historii 
tego miejsca. Cienie wydłużają się groteskowo, a sylwetki zniszczonych 
budynków wyglądają jak szkielety gigantycznych bestii.

Na ziemi, teraz wyraźniejsze w ukośnym świetle, widać ciemne plamy - 
ślady dawno przelanej krwi, które deszcz nie zdołał zmyć. Wiatr niesie 
dziwny zapach - mieszankę starego drewna, rdzy i czegoś słodkawego, 
gnilnego. Z lasu dochodzą pierwsze nocne odgłosy - nie wszystkie brzmią 
jak zwierzęta."""
        
        self.description_night = """Opuszczona Drwalnia - Noc Koszmarów
W ciemności obóz staje się sceną z najgorszego koszmaru. Ruiny budynków 
wyglądają jak czające się potwory, a każdy szelest może być krokiem 
czegoś, co nie powinno tu być. Księżyc rzuca blade światło przez dziury 
w dachach, tworząc na ziemi plamy jak kałuże krwi.

Czasem, gdy wiatr ucichnie, słychać dźwięki których być nie powinno - 
odgłos pracującej piły, uderzenia siekiery, a nawet głosy i śmiech. 
Ale gdy się wsłuchasz, wszystko cichnie. Tylko czerwone oczy świecą 
w ciemności z każdego kąta obozu - to mogą być szczury... mogą."""
        
        # Zmutowana flora
        self.flora = [
            ForestPlant(
                name="Krwawa Pokrzywa",
                description="Pokrzywa o czerwonych liściach, rosnąca gdzie przelano krew.",
                is_edible=False,
                is_poisonous=True,
                is_medicinal=False,
                harvest_season="zawsze",
                uses=["Trucizna paraliżująca"],
                location_preference="miejsca śmierci"
            ),
            ForestPlant(
                name="Grzyb Trupi",
                description="Fosforyzujący grzyb rosnący na zbutwiałym drewnie.",
                is_edible=False,
                is_poisonous=True,
                is_medicinal=True,
                harvest_season="jesień",
                uses=["Halucynogen", "Widzenie duchów"],
                location_preference="gnijące drewno"
            )
        ]
        
        # Niebezpieczna fauna
        self.fauna = [
            ForestCreature(
                name="Zmutowany Pająk Drewniany",
                description="Pająk wielkości psa, jego chityna wygląda jak kora drzewa.",
                danger_level=6,
                is_hostile=True,
                is_nocturnal=True,
                loot=["Jedwab pająka", "Toksyna paraliżująca"],
                sounds=["Klikanie szczękoczułek", "Szelest ośmiu nóg"],
                tracks="Lepka sieć między belkami"
            ),
            ForestCreature(
                name="Widmowy Drwal",
                description="Duch drwala wciąż wykonujący swoją pracę. Półprzezroczysty, z siekierą w ręku.",
                danger_level=7,
                is_hostile=True,
                is_nocturnal=True,
                loot=["Ektoplazma", "Widmowa siekiera"],
                sounds=["Uderzenia siekiery", "Zawodzenie"],
                tracks="Ślady stóp znikające w połowie"
            ),
            ForestCreature(
                name="Głodne Szczury",
                description="Wygłodniałe szczury wielkości kotów, polujące stadami.",
                danger_level=4,
                is_hostile=True,
                is_nocturnal=False,
                loot=["Szczurza skóra", "Zarażone mięso"],
                sounds=["Pisk", "Gryzienie drewna"],
                tracks="Małe ślady łapek wszędzie"
            )
        ]
        
        # Mroczne tajemnice
        self.secrets = [
            AncientSecret(
                id="massacre_truth",
                name="Prawda o Masakrze",
                description="Co naprawdę stało się z drwalami.",
                discovery_conditions={
                    "action": "przeczytaj dziennik",
                    "item": "dziennik brygadzisty"
                },
                revelation="""Dziennik opisuje ostatnie dni obozu. Drwale ścięli Święte Drzewo mimo 
                           ostrzeżeń druidów. W nocy las się zemścił - drzewa ożyły, korzenie 
                           dusiły śpiących, a gałęzie przebijały uciekających. Ci którzy przeżyli 
                           pierwszą noc, zwariowali i pozabijali się nawzajem. Las pochłonął ich dusze.""",
                curse="Klątwa Drwali - las jest wobec ciebie wrogi"
            ),
            AncientSecret(
                id="hidden_treasury",
                name="Ukryty Skarbiec",
                description="Schowek z zarobkami drwali.",
                discovery_conditions={
                    "action": "zbadaj piwnicę",
                    "time": "dzień"
                },
                revelation="""Pod podłogą magazynu znajdujesz ukrytą skrytkę. Pełna jest monet 
                           i kosztowności - zarobki drwali które mieli wysłać rodzinom. 
                           Między monetami leżą listy pożegnalne, nigdy nie wysłane.""",
                power_granted=None,
                guardians=["Widmowy Brygadzista"]
            )
        ]
        
        # Ponura atmosfera
        self.ambient_sounds = [
            "Skrzypienie zawiasów na wietrze jak jęki torturowanych",
            "Kroki których nie powinno być - ktoś chodzi po pustych barakach",
            "Odgłos piły tnącej drewno, choć piła nie działa od lat",
            "Szelest tysięcy pająków czających się w ciemności",
            "Echo krzyków z przeszłości niesione wiatrem"
        ]
        
        self.smells = [
            "Zapach gnijącego drewna i pleśni",
            "Metaliczny posmak krwi w powietrzu",
            "Słodkawy odór rozkładu",
            "Ostry zapach rdzy i starego żelaza",
            "Dziwny, chemiczny smród z warsztatu"
        ]
        
        self.mystical_effects = [
            "Włosy stają dęba - coś cię obserwuje",
            "Temperatura spada o kilka stopni",
            "Widzisz ruch kątem oka, ale gdy patrzysz - nic",
            "Słyszysz swoje imię szeptane z ciemności",
            "Narzędzia poruszają się same z siebie"
        ]
        
        # Niebezpieczne połączenia
        self.connections = {
            "północ": "głęboki_las",
            "południe": "ścieżka_myśliwska",
            "wschód": "krąg_druidów",
            "zachód": "łysina_wisielców"
        }
        
        self.hidden_paths = {
            "piwnica": ("podziemne_tunele", "znajomość sekretnego hasła"),
            "studnia": ("podziemne_jezioro", "lina i odwaga")
        }


class DarkForestDepths(ForestLocation):
    """Najgłębsza, najmroczniejsza część lasu."""
    
    def __init__(self):
        super().__init__("Głębia Czarnego Lasu", ForestLocationType.DEEP_FOREST)
        self.danger_level = 8
        self.is_corrupted = True  # Dotknięta Pustką
        self._setup_depths()
    
    def _setup_depths(self):
        """Konfiguruje głębię lasu."""
        self.description_dawn = """Głębia Czarnego Lasu - Fałszywy Świt
Nawet o świcie to miejsce pozostaje pogrążone w półmroku. Drzewa rosną tak gęsto 
i wysoko, że ich korony splatają się w nieprzenikalne sklepienie. Jedyne światło 
to blade, chorobliwe promienie przebijające się przez rzadkie szczeliny, barwiące 
wszystko na zielonkawo-żółty odcień.

Pnie drzew są grubsze niż budynki, ich kora czarna i popękana jak spaloną ziemia. 
Niektóre drzewa krwawią czerwoną żywicą, która kapie powoli jak krew z rany. 
Korzenie wijące się po ziemi są grube jak ludzkie ciało, pulsują jakby miały 
własne serce. Tu las jest żywy w sposób, który nie powinien być możliwy."""
        
        self.description_day = """Głębia Czarnego Lasu - Wieczny Półmrok
Dzień nie istnieje w głębi lasu. Ciemność jest gęsta, namacalna, jakby miała 
własną substancję. Mgła snuje się między drzewami, ale to nie zwykła mgła - 
porusza się pod wiatr, formuje kształty które znikają gdy na nie patrzysz.

Ziemia pod stopami jest miękka od warstw gnijących liści nagromadzonych przez 
wieki. Każdy krok wyzwala obłoki zarodników i dziwnych, fosforyzujących pyłków. 
Grzyby rosną wszędzie - na drzewach, kamieniach, nawet na kościach zwierząt. 
Niektóre pulsują własnym światłem, inne poruszają się jakby oddychały.

W oddali, zawsze w oddali, słychać dźwięki których nie potrafisz zidentyfikować. 
Coś wielkiego porusza się między drzewami, łamiąc gałęzie grube jak belki."""
        
        self.description_dusk = """Głębia Czarnego Lasu - Godzina Przebudzenia
Gdy zmierzch nadchodzi w normalnym świecie, głębia lasu budzi się naprawdę. 
Fosforyzujące grzyby rozjaśniają się, rzucając nieziemską poświatę. Oczy - 
setki par oczu - świecą w ciemności z każdej strony.

Drzewa zaczynają się poruszać mimo braku wiatru. Gałęzie wyciągają się jak 
palce, korzenie pełzną po ziemi jak węże. Szepty wypełniają powietrze - 
nie ludzkie, nie zwierzęce, ale coś pomiędzy. Mówią w językach których 
nie powinieneś rozumieć, ale rozumiesz. Mówią o głodzie, o samotności, 
o wieczności czekania."""
        
        self.description_night = """Głębia Czarnego Lasu - Noc Starożytnych
W nocy głębia należy do Nich - Starożytnych bytów które były tu przed lasem, 
przed światem, przed czasem. Ciemność staje się żywa, oddycha, pulsuje. 
Rzeczywistość jest tu cienka jak papier, a za nią czai się Pustka.

Drzewa śpiewają pieśń starszą niż gwiazdy - dysharmonijną, hipnotyzującą, 
wciągającą. Ziemia drży od kroków czegoś ogromnego, co nigdy się nie pokazuje. 
Portale do innych wymiarów otwierają się i zamykają losowo, pokazując krajobrazy 
których ludzki umysł nie potrafi pojąć.

Jeśli przeżyjesz noc w głębi, już nigdy nie będziesz taki sam. Las zostawi 
na tobie swoje piętno - w snach będziesz słyszał jego wołanie, w ciszy 
jego szepty. Niektórzy mówią, że to błogosławieństwo. Inni - że przekleństwo."""
        
        # Flora Pustki
        self.flora = [
            ForestPlant(
                name="Kwiat Pustki",
                description="Czarny kwiat który pochłania światło wokół siebie.",
                is_edible=False,
                is_poisonous=True,
                is_medicinal=False,
                harvest_season="zawsze",
                uses=["Rytuały Pustki", "Otwieranie portali"],
                location_preference="skażone miejsca"
            ),
            ForestPlant(
                name="Drzewo Krwi",
                description="Małe drzewo którego sok jest czerwony jak krew.",
                is_edible=False,
                is_poisonous=False,
                is_medicinal=True,
                harvest_season="pełnia",
                uses=["Eliksir nieśmiertelności", "Pakt z demonami"],
                location_preference="miejsca śmierci"
            ),
            ForestPlant(
                name="Szepczący Mech",
                description="Mech który szepcze sekrety tym którzy się wsłuchają.",
                is_edible=False,
                is_poisonous=False,
                is_medicinal=False,
                harvest_season="zawsze",
                uses=["Poznanie tajemnic", "Utrata rozumu"],
                location_preference="starożytne drzewa"
            )
        ]
        
        # Potwory Pustki
        self.fauna = [
            ForestCreature(
                name="Cień Pożeracz",
                description="Żywy cień który pożera inne cienie, pozostawiając ofiary bez odbicia.",
                danger_level=9,
                is_hostile=True,
                is_nocturnal=True,
                loot=["Esencja cienia", "Kryształ Pustki"],
                sounds=["Szelest który nie istnieje", "Echo krzyku którego nie było"],
                tracks="Brak śladów, tylko zimno"
            ),
            ForestCreature(
                name="Starożytny Strażnik",
                description="Istota starsza niż las, wykonana z kory, mchu i gniewu.",
                danger_level=10,
                is_hostile=True,
                is_nocturnal=False,
                loot=["Kora Starożytnego", "Serce Lasu"],
                sounds=["Trzask łamanych drzew", "Ryk wstrząsający ziemią"],
                tracks="Głębokie wyrwy w ziemi"
            ),
            ForestCreature(
                name="Widmowa Samica",
                description="Duch kobiety która zgubiła się w lesie. Wabi podróżnych na zgubę.",
                danger_level=7,
                is_hostile=True,
                is_nocturnal=True,
                loot=["Łzy Widma", "Przekleństwo"],
                sounds=["Płacz dziecka", "Wołanie o pomoc", "Śpiew kołysanki"],
                tracks="Ślady bosych stóp prowadzące w kółko"
            )
        ]
        
        # Zakazane tajemnice
        self.secrets = [
            AncientSecret(
                id="heart_of_darkness",
                name="Serce Ciemności",
                description="Źródło mocy Czarnego Lasu.",
                discovery_conditions={
                    "action": "złóż ofiarę",
                    "item": "krew niewiniątka",
                    "time": "nów"
                },
                revelation="""Ziemia rozstępuje się, odsłaniając pulsujące, czarne serce wielkości 
                           domu. To Serce Lasu - starożytny artefakt który daje lasowi życie 
                           i świadomość. Bije rytmem który czujesz w kościach. Oferuje ci 
                           pakt - moc za duszę, nieśmiertelność za człowieczeństwo.""",
                power_granted="Władza nad lasem",
                curse="Stajesz się częścią lasu na zawsze",
                guardians=["Starożytny Strażnik", "Las Sam W Sobie"]
            ),
            AncientSecret(
                id="void_gateway",
                name="Brama Pustki",
                description="Główne przejście do wymiaru Pustki.",
                discovery_conditions={
                    "action": "wypowiedz zakazane imię",
                    "time": "północ"
                },
                revelation="""Rzeczywistość pęka jak szkło. Za szczeliną nie ma nic - dosłownie NIC. 
                           Pustka patrzy na ciebie nie-oczami, mówi nie-głosem. Oferuje 
                           koniec wszystkiego - bólu, strachu, istnienia. Musisz tylko wejść.""",
                power_granted="Dotyk Pustki",
                curse="Powolna utrata człowieczeństwa",
                guardians=["Strażnicy Pustki"]
            )
        ]
        
        # Przerażająca atmosfera
        self.ambient_sounds = [
            "Śpiew drzew w języku strachu",
            "Kroki czegoś ogromnego zawsze za tobą",
            "Twoje własne krzyki z przyszłości",
            "Szepty zmarłych wołających po imieniu",
            "Bicie Serca Lasu wstrząsające ziemią",
            "Cisza tak głęboka że słyszysz własną krew"
        ]
        
        self.smells = [
            "Zapach rozkładu i wilgotnej ziemi",
            "Metaliczny posmak strachu",
            "Słodki zapach trującego pyłku",
            "Smród siarki z portali",
            "Woń starego, złego czasu",
            "Zapach twojej własnej śmierci"
        ]
        
        self.mystical_effects = [
            "Czas płynie inaczej - minuty jak godziny",
            "Widzisz własną śmierć kątem oka",
            "Rzeczywistość faluje jak woda",
            "Słyszysz myśli drzew - są głodne",
            "Czujesz jak las próbuje wejść do twojego umysłu",
            "Twój cień żyje własnym życiem"
        ]
        
        # Niebezpieczne połączenia
        self.connections = {
            "powrót": "gęsty_las"  # Tylko jedno wyjście, jeśli znajdziesz drogę
        }
        
        self.hidden_paths = {
            "serce": ("serce_lasu", "pakt z lasem"),
            "pustka": ("wymiar_pustki", "utrata człowieczeństwa"),
            "portal": ("inne_miejsce_i_czas", "łut szczęścia")
        }


class CzarnyLas:
    """Główna klasa zarządzająca Czarnym Lasem."""
    
    def __init__(self):
        """Inicjalizacja systemu Czarnego Lasu."""
        self.name = "Czarny Las"
        self.locations: Dict[str, ForestLocation] = {}
        self.current_location_name = "skraj_lasu"
        
        # Stan lasu
        self.corruption_level = 0.3  # 0-1, poziom skażenia Pustką
        self.druid_favor = 0  # -100 do 100, przychylność druidów
        self.forest_anger = 0  # 0-100, gniew lasu
        self.discovered_secrets = []
        
        self._create_locations()
        self._setup_connections()
    
    def _create_locations(self):
        """Tworzy wszystkie lokacje w lesie."""
        # Główne lokacje
        self.locations["krąg_druidów"] = DruidGrove()
        self.locations["krąg_druidów"].id = "krąg_druidów"
        
        self.locations["opuszczona_drwalnia"] = AbandonedLoggingCamp()
        self.locations["opuszczona_drwalnia"].id = "opuszczona_drwalnia"
        
        self.locations["głębia_lasu"] = DarkForestDepths()
        self.locations["głębia_lasu"].id = "głębia_lasu"
        
        # Future: Dodać więcej lokacji (święty gaj, łysina wisielców, jaskinia, etc.)
    
    def _setup_connections(self):
        """Konfiguruje połączenia między lokacjami."""
        # Połączenia są już zdefiniowane w poszczególnych lokacjach
        pass
    
    def get_current_location(self) -> ForestLocation:
        """Zwraca aktualną lokację."""
        return self.locations.get(self.current_location_name)
    
    def describe_current_location(self, time_system: TimeSystem, weather: WeatherSystem) -> str:
        """Opisuje aktualną lokację z uwzględnieniem czasu i pogody."""
        location = self.get_current_location()
        if location:
            return location.get_description(time_system, weather)
        return "Znajdujesz się w nieznanej części lasu."
    
    def search_area(self, skill_level: int = 0) -> Dict[str, Any]:
        """Przeszukuje okolicę."""
        location = self.get_current_location()
        results = {
            "herbs": [],
            "danger": None,
            "items": []
        }
        
        if location:
            results["herbs"] = location.search_for_herbs(skill_level)
            results["danger"] = location.check_for_danger()
            
            # Szansa na znalezienie ukrytych przedmiotów
            if random.random() < 0.2 + (skill_level * 0.05):
                if location.hidden_items:
                    found_item = random.choice(location.hidden_items)
                    results["items"].append(found_item)
                    location.hidden_items.remove(found_item)
        
        return results
    
    def interact_with_location(self, action: str, inventory: List[str]) -> Optional[str]:
        """Interakcja z lokacją."""
        location = self.get_current_location()
        if not location:
            return None
        
        conditions = {
            "inventory": inventory,
            "corruption": self.corruption_level,
            "druid_favor": self.druid_favor
        }
        
        # Sprawdź czy akcja odkrywa tajemnicę
        secret = location.reveal_secret(action, conditions)
        if secret and secret.id not in self.discovered_secrets:
            self.discovered_secrets.append(secret.id)
            
            # Zastosuj efekty odkrycia
            if secret.power_granted:
                # Future: Dodaj moc do gracza
                pass
            if secret.curse:
                # Future: Zastosuj klątwę
                self.corruption_level = min(1.0, self.corruption_level + 0.1)
            
            return secret.revelation
        
        return None
    
    def get_forest_status(self) -> str:
        """Zwraca status lasu."""
        status_parts = [
            f"🌲 Poziom skażenia: {self.corruption_level * 100:.0f}%",
            f"🍃 Przychylność druidów: {self.druid_favor}",
            f"😠 Gniew lasu: {self.forest_anger}",
            f"🔮 Odkryte tajemnice: {len(self.discovered_secrets)}"
        ]
        
        return "\n".join(status_parts)