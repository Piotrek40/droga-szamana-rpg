"""
Targowisko Trzech Dróg - tętniące życiem miasto handlowe.
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


class DistrictType(Enum):
    """Typy dzielnic miasta."""
    MARKET_SQUARE = "plac_targowy"
    CRAFTSMAN = "dzielnica_rzemieślnicza"
    NOBLE = "dzielnica_szlachecka"
    SLUMS = "slumsy"
    PORT = "port"
    TEMPLE = "dzielnica_świątynna"
    WAREHOUSE = "magazyny"


@dataclass
class Merchant:
    """Kupiec w mieście."""
    name: str
    shop_name: str
    specialty: str
    description: str
    personality: str  # chciwy, uczciwy, podejrzany, przyjazny
    inventory_quality: str  # słaba, średnia, dobra, doskonała
    price_modifier: float  # 0.5 - 2.0
    faction_alignment: str
    secrets: List[str] = field(default_factory=list)
    schedule: Dict[str, str] = field(default_factory=dict)
    
    def get_greeting(self, time: str, reputation: int) -> str:
        """Zwraca powitanie kupca."""
        if reputation > 50:
            return f"{self.name}: Witaj, przyjacielu! Co mogę dla ciebie zrobić?"
        elif reputation < -20:
            return f"{self.name}: Czego tu szukasz? Nie obsługuję takich jak ty."
        else:
            return f"{self.name}: Witaj w {self.shop_name}. Czego szukasz?"


@dataclass
class CityGuard:
    """Strażnik miejski."""
    name: str
    rank: str
    description: str
    patrol_route: List[str]
    corruption_level: int  # 0-10, 0=nieprzekupny, 10=totalnie skorumpowany
    alertness: int  # 0-10
    equipment: List[str]
    personality: str
    
    def check_papers(self, has_papers: bool, bribe_amount: int = 0) -> Tuple[bool, str]:
        """Sprawdza dokumenty lub przyjmuje łapówkę."""
        if has_papers:
            return True, f"{self.name}: Wszystko w porządku, możesz przejść."
        
        if bribe_amount >= (10 - self.corruption_level) * 10:
            return True, f"{self.name}: *chowa monety* Nie widziałem cię tu."
        
        return False, f"{self.name}: Stój! Nie masz przepustki! Aresztuję cię!"


@dataclass
class TownEvent:
    """Wydarzenie w mieście."""
    id: str
    name: str
    description: str
    time_window: Tuple[int, int]  # godziny kiedy może się wydarzyć
    location: str
    participants: List[str]
    outcomes: List[str]
    frequency: str  # codziennie, co_tydzień, rzadko, jednorazowo


class MarketDistrict:
    """Bazowa klasa dla dzielnicy miasta."""
    
    def __init__(self, name: str, district_type: DistrictType):
        self.id = ""
        self.name = name
        self.type = district_type
        self.description_dawn = ""
        self.description_morning = ""
        self.description_noon = ""
        self.description_afternoon = ""
        self.description_evening = ""
        self.description_night = ""
        
        # Mieszkańcy i sklepy
        self.merchants: List[Merchant] = []
        self.guards: List[CityGuard] = []
        self.citizens: List[Dict] = []
        self.buildings: Dict[str, str] = {}
        
        # Stan dzielnicy
        self.crowd_level = 0.5  # 0-1, poziom tłoku
        self.safety_level = 0.7  # 0-1, poziom bezpieczeństwa
        self.prosperity = 0.5  # 0-1, poziom zamożności
        
        # Efekty środowiskowe
        self.ambient_sounds: List[str] = []
        self.smells: List[str] = []
        self.notable_sights: List[str] = []
        
        # Wydarzenia
        self.events: List[TownEvent] = []
        
        # Połączenia
        self.connections: Dict[str, str] = {}
    
    def get_description(self, time_system: TimeSystem, weather: WeatherSystem) -> str:
        """Zwraca opis dzielnicy zależny od pory dnia."""
        hour = time_system.get_hour()
        
        # Wybierz opis na podstawie pory dnia
        if 5 <= hour < 8:
            desc = self.description_dawn
        elif 8 <= hour < 11:
            desc = self.description_morning
        elif 11 <= hour < 14:
            desc = self.description_noon
        elif 14 <= hour < 17:
            desc = self.description_afternoon
        elif 17 <= hour < 20:
            desc = self.description_evening
        else:
            desc = self.description_night
        
        # Dodaj informacje o tłumie
        crowd_desc = self._get_crowd_description(hour)
        
        # Dodaj efekty pogodowe
        weather_desc = self._get_weather_effects(weather)
        
        # Dodaj losowe wydarzenia
        event_desc = self._check_for_events(hour)
        
        # Dodaj atmosferę
        atmosphere = self._get_atmosphere()
        
        return f"{desc}\n\n{crowd_desc}{weather_desc}{event_desc}\n\n{atmosphere}"
    
    def _get_crowd_description(self, hour: int) -> str:
        """Opisuje poziom tłoku."""
        if self.type == DistrictType.MARKET_SQUARE:
            if 8 <= hour < 18:
                self.crowd_level = 0.9
                return "Plac jest zatłoczony - setki ludzi przepychają się między straganami.\n"
            else:
                self.crowd_level = 0.2
                return "Plac jest prawie pusty, tylko nieliczni przechodnie.\n"
        elif self.type == DistrictType.SLUMS:
            if 20 <= hour or hour < 4:
                self.crowd_level = 0.7
                return "Ciemne zaułki pełne są podejrzanych postaci.\n"
            else:
                self.crowd_level = 0.3
                return "Ulice są stosunkowo puste, tylko żebracy i pijacy.\n"
        return ""
    
    def _get_weather_effects(self, weather: WeatherSystem) -> str:
        """Zwraca opis wpływu pogody na dzielnicę."""
        current = weather.current_weather
        
        if current == WeatherType.RAIN:
            return "Deszcz przemacza wszystko, ludzie chowają się pod daszkami.\n"
        elif current == WeatherType.STORM:
            return "Burza wygnała ludzi z ulic, stragany są pozamykane.\n"
        elif current == WeatherType.SNOW:
            return "Śnieg pokrywa ulice, handel niemal zamarł.\n"
        return ""
    
    def _check_for_events(self, hour: int) -> str:
        """Sprawdza czy występuje jakieś wydarzenie."""
        for event in self.events:
            if event.time_window[0] <= hour <= event.time_window[1]:
                if random.random() < 0.3:  # 30% szans na wydarzenie
                    return f"\n🎭 {event.description}"
        return ""
    
    def _get_atmosphere(self) -> str:
        """Zwraca opis atmosfery."""
        parts = []
        
        if self.ambient_sounds:
            sound = random.choice(self.ambient_sounds)
            parts.append(f"🔊 {sound}")
        
        if self.smells:
            smell = random.choice(self.smells)
            parts.append(f"👃 {smell}")
        
        if self.notable_sights:
            sight = random.choice(self.notable_sights)
            parts.append(f"👁️ {sight}")
        
        return "\n".join(parts)


class MainMarketSquare(MarketDistrict):
    """Główny plac targowy miasta."""
    
    def __init__(self):
        super().__init__("Plac Główny", DistrictType.MARKET_SQUARE)
        self._setup_square()
    
    def _setup_square(self):
        """Konfiguruje główny plac."""
        self.description_dawn = """Plac Główny - Poranek Handlu
Pierwsze promienie słońca oświetlają mokre od rosy kamienie placu. Kupcy rozkładają 
swoje stragany, brzęk drewna i metalu wypełnia powietrze. Fontanna Trzech Braci 
w centrum placu tryska czystą wodą, a gołębie już gromadzą się wokół, czekając 
na okruchy.

Piekarze wynoszą świeże bochenki, ich zapach miesza się z wonią przypraw przywiezionych 
z południa. Służące wielkich domów już krążą między straganami, wybierając najświeższe 
produkty dla swoich panów. Strażnicy miejsc ziewają po nocnej warcie, opierając się 
o włócznie."""
        
        self.description_morning = """Plac Główny - Ranne Targowisko
Plac tętni życiem. Setki głosów zlewa się w jeden wielki gwar - kupcy wykrzykują 
swoje oferty, klienci targują się zawzięcie, dzieci biegają między straganami. 
Kolorowe płótna namiotów trzepoczą na wietrze jak chorągwie.

Przy fontannie wędrowny bard stroi lutnię, przygotowując się do występu. Herod 
miejski stoi na podwyższeniu, czytając najnowsze ogłoszenia. Wozy pełne towarów 
wciąż przyjeżdżają, a tragarze uginają się pod ciężarem skrzyń i worków.

Zapach świeżego chleba, wędzonego mięsa, owoców i kwiatów tworzy oszałamiającą 
mieszankę. Kieszonkowcy krążą w tłumie, wypatrując łatwych ofiar."""
        
        self.description_noon = """Plac Główny - Południowe Apogeum
Słońce stoi w zenicie, a plac jest zatłoczony do granic możliwości. Trudno 
przejść przez tłum - wszędzie ciała, pot, krzyki. Fontanna oferuje chwilę 
ochłody, ale i tam tłoczą się spragnieni.

Przy każdym straganie trwa zacięta walka o najlepsze towary. Egzotyczny handlarz 
pokazuje jedwabie z dalekiego wschodu, jubiler prezentuje błyszczące kamienie, 
a kowal demonstruje ostrość swoich ostrzy. Mnisi zbierają jałmużnę, a strażnicy 
próbują utrzymać porządek w tym chaosie.

Nagle rozlega się dzwon ratuszowy - czas na południowe ogłoszenia. Tłum na moment 
cichnie, wsłuchując się w głos herolda."""
        
        self.description_afternoon = """Plac Główny - Popołudniowe Okazje
Najgorszy upał minął, ale plac wciąż tętni życiem. Niektórzy kupcy zaczynają 
obniżać ceny, chcąc pozbyć się towarów przed wieczorem. To najlepszy czas 
na okazje dla cierpliwych.

Przy fontannie grupa dzieci plusk w wodzie, ku niezadowoleniu strażników. 
Pijacy wychodzą z tawern, kontynuując libacje na świeżym powietrzu. Grupa 
podróżnych właśnie przyjechała do miasta - ich wozy zaparkowane przy wjeździe 
na plac przyciągają ciekawskie spojrzenia.

W cieniu ratusza zebrała się grupa mieszczan, dyskutując o najnowszych podatkach. 
Ich głosy są gniewne, ale ostrożne - straż ma wszędzie uszy."""
        
        self.description_evening = """Plac Główny - Wieczorne Zamykanie
Zachodzące słońce barwi plac na złoto i czerwień. Kupcy pakują swoje towary, 
zwijają namioty, ładują wozy. Zmęczeni całodziennym handlem liczą zyski 
i straty.

Bardowie i aktorzy przejmują plac - rozpoczynają się wieczorne występy. 
Mieszkańcy gromadzą się wokół, rzucając monety do kapeluszy. Z tawern 
dochodzi muzyka i śmiech. Latarnie są zapalane jedna po drugiej, tworząc 
wyspy światła w nadchodzącej ciemności.

Nocni handlarze już rozkładają swoje bardziej... dyskretne towary. Strażnicy 
zmieniają wartę, świeży patrol jest bardziej czujny."""
        
        self.description_night = """Plac Główny - Nocne Sekrety
W świetle latarni i księżyca plac wygląda zupełnie inaczej. Puste stragany 
rzucają długie cienie, a fontanna szemrze samotnie. Tylko nieliczni przechodnie 
śpieszą przez plac, ich kroki odbijają się echem od kamieni.

W ciemnych zaułkach wokół placu toczą się inne interesy - szemrane transakcje, 
potajemne spotkania, niedozwolone romanse. Nocna straż patroluje regularnie, 
ale wie kiedy nie widzieć pewnych rzeczy.

Czasem przez plac przemknie zakapturzona postać, śpiesząca na spotkanie którego 
nie powinno być. Koty polują na szczury między pustymi straganami, a z oddali 
dochodzi wycie psów i krzyki z tawern."""
        
        # Kupcy
        self.merchants = [
            Merchant(
                name="Gruby Władek",
                shop_name="Władkowe Wiktuały",
                specialty="żywność",
                description="Otyły kupiec o czerwonej twarzy i głośnym śmiechu.",
                personality="chciwy",
                inventory_quality="średnia",
                price_modifier=1.2,
                faction_alignment="Gildia Kupców",
                secrets=["Rozcieńcza wino wodą", "Ma romans z żoną burmistrza"],
                schedule={"ranek": "plac", "południe": "plac", "wieczór": "tawerna"}
            ),
            Merchant(
                name="Eliza Jedwabna",
                shop_name="Jedwabie Wschodu",
                specialty="tkaniny",
                description="Elegancka kobieta o egzotycznej urodzie.",
                personality="tajemnicza",
                inventory_quality="doskonała",
                price_modifier=1.8,
                faction_alignment="niezależna",
                secrets=["Jest szpiegiem z południa", "Handluje informacjami"],
                schedule={"ranek": "sklep", "południe": "plac", "wieczór": "pałac lorda"}
            ),
            Merchant(
                name="Józef Żelazo",
                shop_name="Kuźnia Józefa",
                specialty="broń i zbroje",
                description="Potężny kowal o bliznach od ognia.",
                personality="uczciwy",
                inventory_quality="dobra",
                price_modifier=1.0,
                faction_alignment="Cech Kowali",
                secrets=["Wykuwa broń dla rebeliantów", "Syn jest w gildii złodziei"],
                schedule={"ranek": "kuźnia", "południe": "plac", "wieczór": "kuźnia"}
            )
        ]
        
        # Strażnicy
        self.guards = [
            CityGuard(
                name="Kapitan Markus",
                rank="Kapitan Straży",
                description="Wysoki mężczyzna o surowej twarzy i bliźnie przez oko.",
                patrol_route=["plac", "ratusz", "brama"],
                corruption_level=2,
                alertness=8,
                equipment=["miecz", "kolczuga", "róg alarmowy"],
                personality="surowy ale sprawiedliwy"
            ),
            CityGuard(
                name="Strażnik Piotr",
                rank="Szeregowy",
                description="Młody strażnik, wciąż pełen ideałów.",
                patrol_route=["plac", "fontanna", "stragany"],
                corruption_level=1,
                alertness=6,
                equipment=["włócznia", "skórzana zbroja"],
                personality="naiwny"
            )
        ]
        
        # Wydarzenia
        self.events = [
            TownEvent(
                id="public_execution",
                name="Publiczna Egzekucja",
                description="Na środku placu ustawiono szafot. Tłum gromadzi się, by zobaczyć egzekucję złodzieja.",
                time_window=(11, 13),
                location="centrum placu",
                participants=["Kat", "Skazaniec", "Tłum gapiów"],
                outcomes=["Egzekucja wykonana", "Ucieczka w ostatniej chwili", "Ułaskawienie"],
                frequency="co_tydzień"
            ),
            TownEvent(
                id="merchant_argument",
                name="Kłótnia Kupców",
                description="Dwóch kupców kłóci się głośno o miejsce na placu. Może dojść do bójki!",
                time_window=(9, 16),
                location="stragany",
                participants=["Kupiec 1", "Kupiec 2", "Straż"],
                outcomes=["Bójka", "Ugoda", "Interwencja straży"],
                frequency="codziennie"
            ),
            TownEvent(
                id="bardic_performance",
                name="Występ Barda",
                description="Wędrowny bard opowiada ballady o dawnych czasach, gromadząc tłum słuchaczy.",
                time_window=(17, 21),
                location="fontanna",
                participants=["Bard", "Publiczność"],
                outcomes=["Owacje", "Obrzucenie zgniłymi owocami", "Propozycja występu u lorda"],
                frequency="codziennie"
            )
        ]
        
        # Budynki
        self.buildings = {
            "ratusz": "Imponujący budynek z czerwonej cegły, siedziba władz miasta",
            "fontanna": "Fontanna Trzech Braci - symbol miasta, tryska czystą wodą",
            "tawerna_złoty_kufel": "Popularna tawerna, zawsze pełna gości",
            "bank": "Bank Kupiecki - najbezpieczniejsze miejsce na złoto",
            "świątynia": "Świątynia Światłonoścy, miejsce modlitw i schronienia"
        }
        
        # Atmosfera
        self.ambient_sounds = [
            "Gwar setek głosów zlewających się w jeden szum",
            "Wykrzykiwania kupców reklamujących swoje towary",
            "Brzęk monet przechodzących z rąk do rąk",
            "Śmiech dzieci biegających między straganami",
            "Muzyka dobiegająca z tawern",
            "Rżenie koni i turkot wozów",
            "Dzwony świątyni wybijające godziny"
        ]
        
        self.smells = [
            "Zapach świeżego pieczywa z piekarni",
            "Aromat egzotycznych przypraw",
            "Woń kwiatów ze straganów",
            "Smród końskiego łajna na bruku",
            "Zapach piwa i tytoniu z tawern",
            "Dym z kuźni i pieców"
        ]
        
        self.notable_sights = [
            "Kolorowe flagi i chorągwie trzepoczące na wietrze",
            "Błysk słońca na wypolerowanej broni w kuźni",
            "Egzotyczne ptaki w klatkach u handlarza zwierząt",
            "Akrobata wykonujący sztuczki dla gapiów",
            "Procesja mnichów przechodząca przez plac",
            "Bogato ubrani szlachcice w lektykach"
        ]


class SlumsDistrict(MarketDistrict):
    """Slumsy - najbiedniesza i najbardziej niebezpieczna dzielnica."""
    
    def __init__(self):
        super().__init__("Dolne Miasto", DistrictType.SLUMS)
        self.safety_level = 0.2
        self.prosperity = 0.1
        self._setup_slums()
    
    def _setup_slums(self):
        """Konfiguruje slumsy."""
        self.description_dawn = """Dolne Miasto - Przebudzenie Nędzy
Słońce niechętnie zagląda w wąskie zaułki slumsów. Mgła unosi się z cuchnących 
rynsztoków, mieszając się z dymem z nielicznych ognisk. Żebracy budzą się 
w bramach, otuleni łachmanami, przygotowując się do kolejnego dnia walki o przeżycie.

Szczury wielkości kotów śmiele biegają po ulicach, szukając resztek. Z walących się 
kamienic dochodzi kaszel gruźlików i płacz głodnych dzieci. Gdzieniegdzie ktoś 
opróżnia nocnik przez okno, nie dbając o przechodniów poniżej."""
        
        self.description_morning = """Dolne Miasto - Poranna Desperacja
Ulice zapełniają się nędzarzami szukającymi pracy lub żebraniną. Przy każdym rogu 
stoją kaleki - prawdziwi i udający - wyciągając ręce po jałmużnę. Dzieci 
w łachmanach biegają boso po błocie, kradnąc co się da.

W ciemnych zaułkach dealerzy sprzedają narkotyki i trucizny. Prostytutki, 
zmęczone po nocy, wracają do swoich nor. Zbiry ściągają długi, nie przebierając 
w środkach. To miejsce gdzie prawo nie sięga, a przeżywa najsilniejszy lub 
najsprytniejszy."""
        
        self.description_noon = """Dolne Miasto - Południowe Piekło
W zenicie słońca smród slumsów staje się nie do zniesienia. Gnijące śmieci, 
ludzkie odchody, choroba i rozpacz - wszystko to tworzy miazmat, który można 
kroić nożem. Muchy brzęczą wszędzie, przenosząc zarazy.

Na małym placyku toczy się nielegalna walka - dwóch mężczyzn okłada się 
pięściami dla rozrywki gapiów, którzy obstawiają zakłady. Krew miesza się 
z błotem. W mrocznych spelunkach pijacy kontynuują libacje rozpoczęte wczoraj."""
        
        self.description_afternoon = """Dolne Miasto - Popołudniowa Rozpacz
Upał sprawia, że smród staje się jeszcze bardziej dokuczliwy. Chorzy leżą 
w cieniu, zbyt słabi by się ruszyć. Matki tulą wychudzone dzieci, nie mając 
czym ich nakarmić.

Gang młodych przestępców terroryzuje przechodniów, wymuszając haracze. 
Strażnicy miejsc nie zapuszczają się tu bez poważnego powodu i licznej 
asysty. To królestwo bezprawia, gdzie jedynym prawem jest prawo pięści."""
        
        self.description_evening = """Dolne Miasto - Wieczorne Niebezpieczeństwo
Gdy słońce zachodzi, slumsy stają się jeszcze bardziej niebezpieczne. 
Uczciwe kobiety i dzieci chowają się w domach, zamykając drzwi na wszystkie 
możliwe sposoby. Na ulice wychodzą ci, którzy polują w nocy.

Meliny otwierają swoje podwoje, wabiąc desperatów alkoholem gorszej jakości 
i hazardem. Dom publiczny 'Różą' rozświetla czerwone latarnie. Zbiry 
i mordercy wychodzą na łowy. To czas gdy w slumsach ginie się najłatwiej."""
        
        self.description_night = """Dolne Miasto - Nocny Koszmar
W nocy slumsy to miejsce z najgorszych koszmarów. Ciemność jest tu gęsta, 
bo latarnie dawno zostały rozbite lub skradzione. W mroku czają się 
najgorsze szumowiny miasta.

Krzyki ofiar mieszają się z wyciem głodnych psów. Czasem błyśnie nóż, 
rozlegnie się ostatni jęk i znowu zapada cisza. Trupy znajdowane rankiem 
to codzienność - nikt nie pyta o przyczynę śmierci.

Tylko naprawdę desperaccy lub szaleni wychodzą nocą na ulice Dolnego Miasta. 
Ci, którzy przeżyją noc, mają szczęście lub są częścią problemu."""
        
        # Podejrzani mieszkańcy
        self.merchants = [
            Merchant(
                name="Szczurzy Król",
                shop_name="Czarny Rynek",
                specialty="nielegalne towary",
                description="Chudy mężczyzna o bystrych oczach i szybkich rękach.",
                personality="podejrzany",
                inventory_quality="różna",
                price_modifier=0.7,
                faction_alignment="Gildia Złodziei",
                secrets=["Prowadzi sieć szpiegów", "Ma kontakty w pałacu"],
                schedule={"noc": "melina", "świt": "kryjówka"}
            ),
            Merchant(
                name="Baba Yaga",
                shop_name="Trucizny i Eliksiry",
                specialty="alchemia",
                description="Stara wiedźma o złych oczach i bezzębnym uśmiechu.",
                personality="złośliwa",
                inventory_quality="niebezpieczna",
                price_modifier=1.5,
                faction_alignment="niezależna",
                secrets=["Otruła burmistrza", "Handluje organami"],
                schedule={"zawsze": "chata na bagnach"}
            )
        ]
        
        # Skorumpowana straż
        self.guards = [
            CityGuard(
                name="Sierżant Wilk",
                rank="Sierżant",
                description="Brutal z bliznami i złamanym nosem.",
                patrol_route=["granica_slumsów"],
                corruption_level=9,
                alertness=3,
                equipment=["pałka", "skórzana zbroja"],
                personality="brutalny i chciwy"
            )
        ]
        
        # Mroczne wydarzenia
        self.events = [
            TownEvent(
                id="gang_war",
                name="Wojna Gangów",
                description="Dwa gangi rozpochinają krwawą walkę o terytorium. Ulice spływają krwią.",
                time_window=(22, 4),
                location="główna ulica",
                participants=["Gang Szczura", "Gang Kruka", "Niewinni"],
                outcomes=["Masakra", "Rozejm", "Interwencja tajemniczego mocarza"],
                frequency="co_tydzień"
            ),
            TownEvent(
                id="plague_outbreak",
                name="Wybuch Zarazy",
                description="Tajemnicza choroba rozprzestrzenia się w slumsach. Ludzie umierają dziesiątkami.",
                time_window=(0, 24),
                location="wszędzie",
                participants=["Chorzy", "Uzdrowiciele", "Grabarze"],
                outcomes=["Epidemia", "Znalezienie lekarstwa", "Kwarantanna"],
                frequency="rzadko"
            )
        ]
        
        # Budynki
        self.buildings = {
            "arena_walk": "Nielegalna arena gdzie toczą się walki na śmierć",
            "czarny_kruk": "Najgorsza melina w mieście, tu giną ludzie",
            "dom_róży": "Dom publiczny, front dla handlu ludźmi",
            "rzeźnia": "Oficjalnie rzeźnia, nieoficjalnie miejsce tortur",
            "krypta": "Opuszczony cmentarz, siedziba kultystów"
        }
        
        # Ponura atmosfera
        self.ambient_sounds = [
            "Kaszel gruźlików i jęki chorych",
            "Płacz głodnych dzieci",
            "Kłótnie i bijatyki w zaułkach",
            "Szczekanie wygłodniałych psów",
            "Krzyki ofiar rabunków",
            "Pijackie śpiewy z melin"
        ]
        
        self.smells = [
            "Smród gnijących śmieci i odchodów",
            "Zapach choroby i śmierci",
            "Dym z nielegalnych palarnisk opium",
            "Kwaśny odór zepsutego alkoholu",
            "Metaliczny zapach krwi"
        ]
        
        self.notable_sights = [
            "Trupy leżące w rynsztokach",
            "Dzieci w łachmanach kopiące w śmieciach",
            "Zbiry ściągające haracze",
            "Prostytutki kuszące przechodniów",
            "Szczury wielkości kotów",
            "Walące się kamienice grożące zawaleniem"
        ]


class NobleDistrict(MarketDistrict):
    """Dzielnica szlachecka - bogactwo i intrygi."""
    
    def __init__(self):
        super().__init__("Wzgórze Lordów", DistrictType.NOBLE)
        self.safety_level = 0.9
        self.prosperity = 0.95
        self._setup_noble_district()
    
    def _setup_noble_district(self):
        """Konfiguruje dzielnicę szlachecką."""
        self.description_dawn = """Wzgórze Lordów - Złoty Świt
Poranne słońce złoci białe marmurowe fasady pałaców. Ogrody skąpane są w rosie, 
która lśni jak diamenty na egzotycznych kwiatach. Fontanny zaczynają swój 
codzienny taniec wody, a pawi spacerują dostojnie po trawnikach.

Służba już krząta się po posiadłościach, przygotowując wszystko na przebudzenie 
swoich panów. Wozy z najlepszymi towarami z placu targowego wjeżdżają przez 
ozdobne bramy. Straż w lśniących zbrojach stoi na posterunkach, czujna 
choć znudzona - tu rzadko dzieje się coś złego."""
        
        self.description_morning = """Wzgórze Lordów - Poranna Elegancja
Szlachta rozpoczyna dzień. Damy w jedwabnych sukniach spacerują po ogrodach 
z parasolkami chroniącymi ich delikatną cerę. Panowie w aksamitnych 
dubletach dyskutują o polityce i interesach w cieniu altanek.

Przez szerokie, wybrukowane ulice przejeżdżają powozy z herbami wielkich 
rodów. Służący w barwnych liberiach biegają z wiadomościami między pałacami. 
W ogrodach publicznych poeci komponują wiersze, a malarze szkicują portrety.

Z otwartych okien dochodzi muzyka - młode damy ćwiczą grę na klawesynie, 
a ich nauczyciele tańca prowadzą lekcje menueta."""
        
        self.description_noon = """Wzgórze Lordów - Południowy Przepych
W zenicie słońca marmur pałaców lśni oślepiająco. Szlachta chroni się 
w chłodnych wnętrzach lub pod parasolami w ogrodach. Czas na południową 
sjestę i dyskretne intrygi.

W ekskluzywnych herbaciarniach damy plotkują o najnowszych skandalach. 
Panowie grają w karty o fortuny w prywatnych klubach. Młodzież szlachecka 
popisuje się nowymi strojami i biżuterią, rywalizując o względy i wpływy.

Czasem przez dzielnicę przejedzie królewski goniec, wzbudzając spekulacje - 
jakie wieści niesie? Kto zyskał łaski, a kto popadł w niełaskę?"""
        
        self.description_afternoon = """Wzgórze Lordów - Popołudniowe Intrygi
Popołudnie to czas wizyt i tajnych spotkań. Powozy jeżdżą od pałacu do pałacu, 
przewożąc gości na herbatki i prywatne audiencje. Za zamkniętymi drzwiami 
toczą się gry o władzę i wpływy.

W ogrodach odbywają się turnieje łucznicze i szermierki dla młodych szlachciców. 
Damy obserwują z tarasów, rzucając ukradkowe spojrzenia i chusteczki swoim 
fawory- tom. Romanse kwitną, a pojedynki honorowe są umawiane.

Handlarze luksusowych towarów prezentują swoje najlepsze wyroby - jedwabie 
z wschodu, klejnoty z południa, futra z północy. Ceny są zawrotne, ale tu 
nikt nie pyta o cenę - tylko czy jest to najlepsze."""
        
        self.description_evening = """Wzgórze Lordów - Wieczór Balów
Gdy słońce zachodzi, pałace rozświetlają się tysiącami świec. To czas balów, 
bankietów i przedstawień teatralnych. Muzyka płynie z otwartych okien, 
mieszając się w symfonię bogactwa.

Powozy ustawiają się w kolejkach przed pałacami, wysadzając gości w najwspanialszych 
strojach. Jedwabie, aksamity, brylanty i perły - każdy stara się przyćmić innych. 
Służba biega z tacami pełnymi wykwintnych potraw i najlepszych win.

W ogrodach młodzi kochankowie spotykają się potajemnie w altankach, przysięgając 
sobie wieczną miłość lub knując intrygi. Starsi panowie palą cygara i omawiają 
sojusze polityczne."""
        
        self.description_night = """Wzgórze Lordów - Nocne Sekrety
Nocą, gdy bale dobiegają końca, dzielnica szlachecka pokazuje swoje drugie oblicze. 
Za fasadą elegancji kryją się mroczne sekrety - zdrada, szantaże, morderstwa 
na zlecenie.

Zakapturzone postacie przemykają między pałacami - szpiedzy, kochankowie, 
skrytobójcy. W prywatnych gabinetach toczą się hazardowe gry o majątki. 
W podziemiach niektórych pałaców odbywają się rytuały, o których lepiej nie wiedzieć.

Straż patruluje regularnie, ale wie, że pewnych rzeczy lepiej nie widzieć. 
Pieniądze i wpływy kupują milczenie. Rankiem wszystko wróci do normy - 
elegancka fasada przykryje nocne zbrodnie."""
        
        # Bogaci mieszkańcy
        self.merchants = [
            Merchant(
                name="Lord Konrad",
                shop_name="Pałac Konrada",
                specialty="wpływy polityczne",
                description="Starszy arystokrata o orlim nosie i zimnych oczach.",
                personality="arogancki",
                inventory_quality="tylko najlepsze",
                price_modifier=3.0,
                faction_alignment="Dwór Królewski",
                secrets=["Planuje zamach", "Ma nieślubnego syna w slumsach"],
                schedule={"ranek": "pałac", "południe": "klub", "wieczór": "bal"}
            ),
            Merchant(
                name="Lady Izabela",
                shop_name="Salon Lady Izabeli",
                specialty="intrygi i plotki",
                description="Piękna kobieta o tajemniczym uśmiechu.",
                personality="manipulująca",
                inventory_quality="bezcenne",
                price_modifier=5.0,
                faction_alignment="niezależna",
                secrets=["Jest szpiegiem obcego królestwa", "Otruła męża"],
                schedule={"zawsze": "wszędzie gdzie trzeba"}
            )
        ]
        
        # Elitarna straż
        self.guards = [
            CityGuard(
                name="Ser Galahad",
                rank="Kapitan Gwardii",
                description="Rycerz w lśniącej zbroi, wzór honoru.",
                patrol_route=["bramy", "pałace", "ogrody"],
                corruption_level=0,
                alertness=9,
                equipment=["miecz runiczny", "pełna zbroja płytowa", "tarcza herbowa"],
                personality="honorowy i nieprzekupny"
            )
        ]
        
        # Arystokratyczne wydarzenia
        self.events = [
            TownEvent(
                id="grand_ball",
                name="Wielki Bal",
                description="Jeden z pałaców organizuje wspaniały bal. Śmietanka towarzyska się zjeżdża.",
                time_window=(19, 24),
                location="pałac",
                participants=["Arystokraci", "Artyści", "Służba"],
                outcomes=["Sukces towarzyski", "Skandal", "Pojedynek"],
                frequency="co_tydzień"
            ),
            TownEvent(
                id="honor_duel",
                name="Pojedynek Honorowy",
                description="Dwóch szlachciców staje do pojedynku o honor damy.",
                time_window=(6, 8),
                location="ogrody",
                participants=["Szlachcic 1", "Szlachcic 2", "Sekundanci", "Dama"],
                outcomes=["Pierwsza krew", "Śmierć", "Pojednanie"],
                frequency="rzadko"
            )
        ]
        
        # Pałace i budynki
        self.buildings = {
            "pałac_konrada": "Największy pałac, quasi-forteca",
            "willa_kupiecka": "Nowobogate pokazuje bogactwo",
            "opera": "Miejsce kulturalnych wydarzeń",
            "klub_dżentelmenów": "Ekskluzywny klub tylko dla mężczyzn",
            "ogrody_publiczne": "Zadbane ogrody z egzotycznymi roślinami",
            "akademia_szermierki": "Gdzie młodzi uczą się władać bronią"
        }
        
        # Wykwintna atmosfera
        self.ambient_sounds = [
            "Delikatna muzyka klawesynu z okien",
            "Turkot eleganckich powozów",
            "Śmiech i konwersacje w ogrodach",
            "Fontanny szemrzące w ogrodach",
            "Dzwonki wzywające służbę"
        ]
        
        self.smells = [
            "Zapach egzotycznych perfum",
            "Aromat rzadkich kwiatów w ogrodach",
            "Woń wykwintnych potraw z kuchni",
            "Zapach świeżo skoszonej trawy",
            "Dym z najlepszego tytoniu"
        ]
        
        self.notable_sights = [
            "Pałace z białego marmuru lśniące w słońcu",
            "Ogrody pełne fontann i rzeźb",
            "Szlachta w wspaniałych strojach",
            "Egzotyczne zwierzęta w prywatnych menażeriach",
            "Gwardia w ceremonialnych zbrojach"
        ]


class TargowiskoTrzechDrog:
    """Główna klasa zarządzająca miastem handlowym."""
    
    def __init__(self):
        """Inicjalizacja miasta."""
        self.name = "Targowisko Trzech Dróg"
        self.districts: Dict[str, MarketDistrict] = {}
        self.current_district_name = "plac_główny"
        self.population = 3500
        
        # Ekonomia miasta
        self.treasury = 10000  # w złocie
        self.tax_rate = 0.15
        self.trade_volume = 100  # bazowy wolumen handlu
        
        # Frakcje i wpływy
        self.factions = {
            "Straż Miejska": {"influence": 60, "attitude": 0},
            "Gildia Kupców": {"influence": 80, "attitude": 0},
            "Gildia Złodziei": {"influence": 40, "attitude": 0},
            "Kościół": {"influence": 50, "attitude": 0},
            "Szlachta": {"influence": 70, "attitude": 0}
        }
        
        # Reputacja gracza w mieście
        self.player_reputation = 0  # -100 do 100
        self.player_wanted_level = 0  # 0-5
        
        # Wydarzenia globalne
        self.active_events = []
        self.event_history = []
        
        self._create_districts()
        self._setup_connections()
    
    def _create_districts(self):
        """Tworzy wszystkie dzielnice miasta."""
        self.districts["plac_główny"] = MainMarketSquare()
        self.districts["plac_główny"].id = "plac_główny"
        
        self.districts["dolne_miasto"] = SlumsDistrict()
        self.districts["dolne_miasto"].id = "dolne_miasto"
        
        self.districts["wzgórze_lordów"] = NobleDistrict()
        self.districts["wzgórze_lordów"].id = "wzgórze_lordów"
        
        # TODO: Dodać pozostałe dzielnice (port, dzielnica rzemieślnicza, świątynna)
    
    def _setup_connections(self):
        """Konfiguruje połączenia między dzielnicami."""
        self.districts["plac_główny"].connections = {
            "północ": "wzgórze_lordów",
            "południe": "brama_południowa",
            "wschód": "dzielnica_rzemieślnicza",
            "zachód": "port_rzeczny",
            "dół": "dolne_miasto"
        }
        
        self.districts["dolne_miasto"].connections = {
            "góra": "plac_główny",
            "wschód": "cmentarz",
            "zachód": "doki"
        }
        
        self.districts["wzgórze_lordów"].connections = {
            "południe": "plac_główny",
            "wschód": "pałac_królewski"
        }
    
    def get_current_district(self) -> MarketDistrict:
        """Zwraca aktualną dzielnicę."""
        return self.districts.get(self.current_district_name)
    
    def describe_current_district(self, time_system: TimeSystem, weather: WeatherSystem) -> str:
        """Opisuje aktualną dzielnicę."""
        district = self.get_current_district()
        if district:
            desc = district.get_description(time_system, weather)
            
            # Dodaj informacje o reputacji
            if self.player_reputation > 50:
                desc += "\n\n🌟 Ludzie rozpoznają cię i witają z szacunkiem."
            elif self.player_reputation < -50:
                desc += "\n\n⚠️ Ludzie unikają twojego wzroku i szepcą za twoimi plecami."
            
            # Dodaj ostrzeżenie o poszukiwaniu
            if self.player_wanted_level > 0:
                desc += f"\n\n🚨 Poziom poszukiwania: {'⭐' * self.player_wanted_level}"
            
            return desc
        return "Znajdujesz się w nieznanej części miasta."
    
    def interact_with_merchant(self, merchant_name: str) -> str:
        """Interakcja z kupcem."""
        district = self.get_current_district()
        if not district:
            return "Nie ma tu żadnych kupców."
        
        for merchant in district.merchants:
            if merchant.name.lower() == merchant_name.lower():
                return merchant.get_greeting("dzień", self.player_reputation)
        
        return f"Nie ma tu kupca o imieniu {merchant_name}."
    
    def check_guards(self, has_papers: bool = False, bribe: int = 0) -> Tuple[bool, str]:
        """Sprawdzenie przez straż."""
        district = self.get_current_district()
        if not district or not district.guards:
            return True, "Nie ma tu straży."
        
        guard = random.choice(district.guards)
        return guard.check_papers(has_papers, bribe)
    
    def update_faction_influence(self, faction: str, change: int):
        """Aktualizuje wpływy frakcji."""
        if faction in self.factions:
            self.factions[faction]["influence"] = max(0, min(100, 
                self.factions[faction]["influence"] + change))
    
    def get_market_prices(self, base_price: int) -> int:
        """Oblicza ceny rynkowe z uwzględnieniem ekonomii miasta."""
        modifier = 1.0
        
        # Wpływ wolumenu handlu
        modifier *= (self.trade_volume / 100)
        
        # Wpływ podatków
        modifier *= (1 + self.tax_rate)
        
        # Wpływ reputacji
        if self.player_reputation > 50:
            modifier *= 0.9
        elif self.player_reputation < -50:
            modifier *= 1.2
        
        return int(base_price * modifier)
    
    def get_city_status(self) -> str:
        """Zwraca status miasta."""
        status_parts = [
            f"🏰 {self.name}",
            f"👥 Populacja: {self.population}",
            f"💰 Skarbiec: {self.treasury} złota",
            f"📊 Handel: {self.trade_volume}%",
            f"⭐ Twoja reputacja: {self.player_reputation}",
            f"🚨 Poziom poszukiwania: {self.player_wanted_level}/5"
        ]
        
        # Dodaj wpływy frakcji
        status_parts.append("\n📊 Wpływy frakcji:")
        for faction, data in self.factions.items():
            status_parts.append(f"  {faction}: {data['influence']}%")
        
        return "\n".join(status_parts)