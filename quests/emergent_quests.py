"""
Emergentne questy dla Droga Szamana RPG
System questów powstających naturalnie ze stanu świata
"""

import random
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .quest_engine import (
    QuestSeed, EmergentQuest, QuestBranch, DiscoveryMethod,
    QuestState, ConsequenceEvent, Investigation
)


class QuestType(Enum):
    """Typy questów emergentnych"""
    SURVIVAL = "survival"           # Przetrwanie (głód, choroba)
    CONFLICT = "conflict"           # Konflikt między NPCami
    ESCAPE = "escape"               # Próba ucieczki
    CONTRABAND = "contraband"       # Przemyt
    INFORMATION = "information"     # Zbieranie informacji
    REVENGE = "revenge"             # Zemsta
    ALLIANCE = "alliance"           # Sojusze
    CORRUPTION = "corruption"       # Korupcja strażników
    MYSTERY = "mystery"             # Tajemnice więzienia
    REBELLION = "rebellion"         # Bunt więźniów


class PrisonEscapeQuest(EmergentQuest):
    """Quest ucieczki z więzienia - powstaje gdy gracz odkryje słabość w ochronie"""
    
    def __init__(self, quest_id: str, seed: QuestSeed):
        super().__init__(quest_id, seed)
        self.escape_routes: Dict[str, Dict] = {}
        self.discovered_weaknesses: List[str] = []
        self.guard_suspicion: float = 0.0
        self.accomplices: List[str] = []
        
        # Inicjalizuj trasy ucieczki
        self._initialize_escape_routes()
        
        # Inicjalizuj gałęzie rozwiązań
        self._initialize_branches()
        
        # Dialogi odkrycia
        self.discovery_dialogue = {
            "overheard": [
                "Podsłuchałeś rozmowę: 'Ta ściana... jest słabsza niż inne.'",
                "Ktoś szepce: 'O północy strażnicy śpią przy wartowni.'",
                "Słyszysz: 'Tunel pod kuchnią... prawie gotowy.'"
            ],
            "witnessed": [
                "Zauważyłeś, że strażnik zostawia klucze w przewidywalnym miejscu.",
                "Widziałeś szczura wychodzącego z dziury w ścianie.",
                "Dostrzegłeś luźną kratę w oknie."
            ],
            "found": [
                "Znalazłeś kawałek mapy więzienia z zaznaczonymi słabymi punktami.",
                "Odkryłeś narzędzia schowane w celi.",
                "Natknąłeś się na zapiski o rutynie strażników."
            ],
            "told": [
                "Starszy więzień szepcze: 'Jeśli chcesz uciec, musisz znać harmonogram.'",
                "Zaufany NPC mówi: 'Znam kogoś, kto może pomóc... za odpowiednią cenę.'",
                "Informator zdradza: 'Naczelnik ma słabość...'"
            ]
        }
    
    def _initialize_escape_routes(self):
        """Inicjalizuje możliwe trasy ucieczki"""
        self.escape_routes = {
            "tunnel": {
                "name": "Tunel pod kuchnią",
                "difficulty": 70,
                "time_required": 168,  # 7 dni kopania
                "resources_needed": ["lopata", "kilof", "wsparcie"],
                "discovery_chance": 0.1,
                "locations": ["kuchnia", "piwnica"],
                "progress": 0.0
            },
            "wall_weakness": {
                "name": "Słaby mur w celi 5",
                "difficulty": 60,
                "time_required": 120,  # 5 dni
                "resources_needed": ["narzedzia", "odwrócenie uwagi"],
                "discovery_chance": 0.15,
                "locations": ["cela_5"],
                "progress": 0.0
            },
            "guard_corruption": {
                "name": "Przekupienie strażnika",
                "difficulty": 50,
                "time_required": 48,  # 2 dni negocjacji
                "resources_needed": ["zloto_500", "informacje_kompromitujące"],
                "discovery_chance": 0.2,
                "locations": ["wartownia"],
                "progress": 0.0
            },
            "sewers": {
                "name": "Kanały ściekowe",
                "difficulty": 80,
                "time_required": 24,  # 1 dzień
                "resources_needed": ["mapa_kanalow", "lina", "pochodnia"],
                "discovery_chance": 0.05,
                "locations": ["latryna", "piwnica"],
                "progress": 0.0
            },
            "riot_distraction": {
                "name": "Bunt jako przykrywka",
                "difficulty": 90,
                "time_required": 72,  # 3 dni przygotowań
                "resources_needed": ["sojusznicy_10", "bron", "plan"],
                "discovery_chance": 0.25,
                "locations": ["dziedziniec", "stołówka"],
                "progress": 0.0
            }
        }
    
    def _initialize_branches(self):
        """Inicjalizuje gałęzie rozwiązania questa"""
        # Gałąź: Samotna ucieczka
        solo_branch = QuestBranch("solo_escape", "Ucieknij samotnie")
        solo_branch.requirements = {
            "skill": ("skradanie", 30),
            "item": "narzedzia",
            "discovered_routes": 1
        }
        solo_branch.consequences = {
            "immediate": {
                "world_state": {"prison_alert": "high", "player_wanted": True},
                "relationships": {"wszyscy_wiezniowie": -20}
            },
            "delayed": {
                24: {
                    "world_changes": {"prison_security": "extreme"},
                    "npc_reactions": {"naczelnik": "wściekły", "straznicy": "poszukiwania"},
                    "description": "Więzienie zostało zamknięte. Represje wobec pozostałych."
                }
            }
        }
        solo_branch.dialogue_options = {
            "preview": "Nikogo nie potrzebuję. Sam sobie poradzę.",
            "resolution": "Wymknąłeś się niezauważony... ale za jaką cenę?"
        }
        self.add_branch(solo_branch)
        
        # Gałąź: Ucieczka grupowa
        group_branch = QuestBranch("group_escape", "Zorganizuj ucieczkę grupową")
        group_branch.requirements = {
            "skill": ("przywodztwo", 40),
            "allies": 3,
            "discovered_routes": 2
        }
        group_branch.consequences = {
            "immediate": {
                "world_state": {"prison_riot": True, "chaos_level": "high"},
                "relationships": {"sojusznicy": 50, "straznicy": -100}
            },
            "delayed": {
                48: {
                    "world_changes": {"prison_reforms": True},
                    "new_quests": ["prison_revenge", "fugitive_life"],
                    "description": "Ucieczka wywołała reformy. Niektórzy cię szukają."
                }
            }
        }
        group_branch.dialogue_options = {
            "preview": "Razem mamy większe szanse. Pomożecie mi?",
            "resolution": "Grupa więźniów przedarła się przez mury. Jesteście wolni!"
        }
        self.add_branch(group_branch)
        
        # Gałąź: Legalna droga
        legal_branch = QuestBranch("legal_release", "Zdobądź zwolnienie")
        legal_branch.requirements = {
            "evidence": "dowody_niewinnosci",
            "reputation": ("naczelnik", 30),
            "gold": 1000
        }
        legal_branch.consequences = {
            "immediate": {
                "world_state": {"player_free": True, "legal_status": "clean"},
                "relationships": {"naczelnik": 20, "wiezniowie": -30}
            },
            "delayed": {
                168: {  # Tydzień później
                    "world_changes": {"prison_corruption_exposed": True},
                    "new_quests": ["expose_corruption", "help_inmates"],
                    "description": "Twoje zwolnienie ujawniło korupcję w więzieniu."
                }
            }
        }
        legal_branch.dialogue_options = {
            "preview": "Mam dowody swojej niewinności. Chcę oficjalnego zwolnienia.",
            "resolution": "Wrota więzienia otwierają się. Jesteś wolny... legalnie."
        }
        self.add_branch(legal_branch)
        
        # Gałąź: Zdrada współwięźniów
        betrayal_branch = QuestBranch("betray_inmates", "Zdradź plan ucieczki")
        betrayal_branch.requirements = {
            "discovered_routes": 1,
            "relationship": ("naczelnik", -20)
        }
        betrayal_branch.consequences = {
            "immediate": {
                "world_state": {"player_snitch": True},
                "relationships": {"wiezniowie": -80, "naczelnik": 40}
            },
            "delayed": {
                12: {
                    "world_changes": {"assassination_attempt": True},
                    "npc_reactions": {"wiezniowie": "zemsta"},
                    "description": "Więźniowie planują zemstę za zdradę."
                }
            }
        }
        betrayal_branch.dialogue_options = {
            "preview": "Naczelnik powinien wiedzieć o planach ucieczki...",
            "resolution": "Zdradziłeś współwięźniów. Czy było warto?"
        }
        self.add_branch(betrayal_branch)
    
    def investigate(self, action: str, target: str, player_state: Dict) -> Dict[str, Any]:
        """Prowadzenie śledztwa w sprawie ucieczki"""
        result = super().investigate(action, target, player_state)
        
        if action == "scout":
            # Rozpoznanie terenu
            if target in ["mury", "kraty", "straznicy"]:
                weakness = self._discover_weakness(target)
                if weakness:
                    self.discovered_weaknesses.append(weakness)
                    result["discoveries"].append(weakness)
                    result["dialogue"].append(f"Odkryłeś: {weakness}")
                    
                    # Zwiększ podejrzenia
                    self.guard_suspicion += 0.1
                    if self.guard_suspicion > 0.5:
                        result["warning"] = "Strażnicy zaczynają coś podejrzewać..."
        
        elif action == "recruit":
            # Rekrutacja wspólników
            if target in player_state.get("known_npcs", []):
                relationship = player_state.get("relationships", {}).get(target, 0)
                if relationship > 30:
                    if target not in self.accomplices:
                        self.accomplices.append(target)
                        result["discoveries"].append(f"ally_{target}")
                        result["dialogue"].append(f"{target} przyłącza się do planu ucieczki.")
                else:
                    result["dialogue"].append(f"{target} nie ufa ci wystarczająco.")
        
        elif action == "prepare":
            # Przygotowania do ucieczki
            route = self.escape_routes.get(target)
            if route:
                # Sprawdź zasoby
                has_resources = all(
                    res in player_state.get("inventory", [])
                    for res in route["resources_needed"]
                )
                
                if has_resources:
                    route["progress"] += 10
                    result["discoveries"].append(f"progress_{target}_{route['progress']}")
                    result["dialogue"].append(
                        f"Postęp przygotowań trasy '{route['name']}': {route['progress']}%"
                    )
                    
                    if route["progress"] >= 100:
                        result["ready"] = True
                        result["dialogue"].append(f"Trasa '{route['name']}' jest gotowa!")
                else:
                    result["dialogue"].append(f"Brakuje zasobów: {route['resources_needed']}")
        
        return result
    
    def _discover_weakness(self, target: str) -> Optional[str]:
        """Odkrywa słabości w zabezpieczeniach"""
        weaknesses = {
            "mury": [
                "Pęknięcie w północnej ścianie",
                "Luźne cegły przy kuchni",
                "Podmyte fundamenty w celi 5"
            ],
            "kraty": [
                "Przerdzewiała krata w oknie",
                "Luźne zawiasy w drzwiach",
                "Słaby zamek w magazynie"
            ],
            "straznicy": [
                "Strażnik Marek zasypia na nocnej warcie",
                "Kapitan pije w piątki",
                "Młody rekrut łatwo się rozprasza"
            ]
        }
        
        available = weaknesses.get(target, [])
        if available and random.random() < 0.3:  # 30% szans na odkrycie
            return random.choice(available)
        return None
    
    def can_attempt_escape(self) -> Tuple[bool, str]:
        """Sprawdza czy można podjąć próbę ucieczki"""
        # Sprawdź czy jakakolwiek trasa jest gotowa
        ready_routes = [
            name for name, route in self.escape_routes.items()
            if route["progress"] >= 100
        ]
        
        if not ready_routes:
            return False, "Żadna trasa ucieczki nie jest gotowa"
        
        # Sprawdź poziom podejrzeń
        if self.guard_suspicion > 0.8:
            return False, "Strażnicy są zbyt czujni"
        
        # Sprawdź czy masz wspólników (dla niektórych tras)
        if len(self.accomplices) == 0:
            return False, "Potrzebujesz przynajmniej jednego wspólnika"
        
        return True, f"Możesz spróbować uciec trasą: {ready_routes[0]}"


class ContrabandTradeQuest(EmergentQuest):
    """Quest przemytu - powstaje gdy w więzieniu brakuje podstawowych dóbr"""
    
    def __init__(self, quest_id: str, seed: QuestSeed):
        super().__init__(quest_id, seed)
        self.contraband_items: Dict[str, int] = {}
        self.trade_routes: List[str] = []
        self.supplier_trust: Dict[str, float] = {}
        self.guard_bribes: Dict[str, int] = {}
        self.market_demand: Dict[str, float] = {}
        
        self._initialize_contraband_market()
        self._initialize_branches()
        
        self.discovery_dialogue = {
            "overheard": [
                "Słyszysz szept: 'Potrzebuję lekarstwa... zapłacę ile trzeba.'",
                "Ktoś mówi: 'Strażnik Kowalski bierze łapówki za przemyt.'",
                "Więzień skarży się: 'Tydzień bez papierosów... załatwi ktoś?'"
            ],
            "witnessed": [
                "Widziałeś wymianę paczki między strażnikiem a więźniem.",
                "Zauważyłeś, jak ktoś chowa coś w tajnej skrytce.",
                "Dostrzegłeś sygnały między więźniami podczas apelu."
            ]
        }
    
    def _initialize_contraband_market(self):
        """Inicjalizuje rynek przemytu"""
        self.market_demand = {
            "lekarstwa": 0.8,
            "tytoń": 0.6,
            "alkohol": 0.7,
            "narzędzia": 0.5,
            "broń": 0.9,
            "jedzenie": 0.4,
            "informacje": 0.8
        }
        
        self.trade_routes = [
            "kuchnia_dostawy",
            "pranie_transport",
            "widzenia_przemyt",
            "straż_korupcja"
        ]
    
    def _initialize_branches(self):
        """Inicjalizuje gałęzie questa przemytu"""
        # Zostań królem przemytu
        kingpin_branch = QuestBranch("become_kingpin", "Przejmij kontrolę nad przemytem")
        kingpin_branch.requirements = {
            "gold": 500,
            "allies": 5,
            "controlled_routes": 2
        }
        kingpin_branch.consequences = {
            "immediate": {
                "world_state": {"contraband_monopoly": "player"},
                "relationships": {"wiezniowie": 30, "konkurencja": -50}
            },
            "delayed": {
                72: {
                    "world_changes": {"prison_economy": "player_controlled"},
                    "new_quests": ["defend_monopoly", "expand_network"],
                    "description": "Kontrolujesz cały przemyt. Ale konkurencja nie śpi."
                }
            }
        }
        self.add_branch(kingpin_branch)
        
        # Współpracuj ze strażą
        cooperate_branch = QuestBranch("cooperate_guards", "Dogadaj się ze strażnikami")
        cooperate_branch.requirements = {
            "bribed_guards": 3,
            "reputation": ("straż", 20)
        }
        cooperate_branch.consequences = {
            "immediate": {
                "world_state": {"smuggling_tolerated": True},
                "relationships": {"straż": 20, "wiezniowie": -10}
            }
        }
        self.add_branch(cooperate_branch)
        
        # Zniszcz sieć przemytu
        destroy_branch = QuestBranch("destroy_network", "Zniszcz sieć przemytniczą")
        destroy_branch.requirements = {
            "evidence": "dowody_przemytu",
            "relationship": ("naczelnik", 10)
        }
        destroy_branch.consequences = {
            "immediate": {
                "world_state": {"contraband_crackdown": True},
                "relationships": {"naczelnik": 40, "wiezniowie": -60}
            },
            "delayed": {
                24: {
                    "world_changes": {"prison_shortage": "critical"},
                    "new_quests": ["prison_riot", "revenge_smugglers"],
                    "description": "Braki w więzieniu wywołują napięcia."
                }
            }
        }
        self.add_branch(destroy_branch)


class PrisonGangWarQuest(EmergentQuest):
    """Quest wojny gangów - powstaje gdy napięcia między grupami rosną"""
    
    def __init__(self, quest_id: str, seed: QuestSeed):
        super().__init__(quest_id, seed)
        self.gang_tensions: Dict[str, Dict[str, float]] = {}
        self.gang_strength: Dict[str, int] = {}
        self.player_allegiance: Optional[str] = None
        self.conflict_events: List[Dict] = []
        
        self._initialize_gangs()
        self._initialize_branches()
        
        self.discovery_dialogue = {
            "witnessed": [
                "Widziałeś bójkę między członkami różnych grup.",
                "Zauważyłeś napięte spojrzenia podczas posiłku.",
                "Byłeś świadkiem gróźb między gangami."
            ],
            "told": [
                "Więzień ostrzega: 'Wybierz stronę, albo zginiesz w krzyżowym ogniu.'",
                "Lider gangu mówi: 'Przyłącz się do nas, zanim będzie za późno.'",
                "Informator szepcze: 'Wojna wybuchnie jutro o świcie.'"
            ]
        }
    
    def _initialize_gangs(self):
        """Inicjalizuje gangi więzienne"""
        self.gang_strength = {
            "północni": 15,
            "południowi": 12,
            "handlarze": 8,
            "samotni_wilki": 5
        }
        
        self.gang_tensions = {
            "północni": {"południowi": 0.8, "handlarze": 0.3},
            "południowi": {"północni": 0.8, "samotni_wilki": 0.5},
            "handlarze": {"północni": 0.3, "południowi": 0.4},
            "samotni_wilcy": {"południowi": 0.5, "handlarze": 0.2}
        }
    
    def _initialize_branches(self):
        """Inicjalizuje gałęzie rozwiązania konfliktu"""
        # Poprowadź gang do zwycięstwa
        lead_gang_branch = QuestBranch("lead_to_victory", "Poprowadź gang do zwycięstwa")
        lead_gang_branch.requirements = {
            "gang_membership": True,
            "combat_skill": 40,
            "gang_reputation": 50
        }
        lead_gang_branch.consequences = {
            "immediate": {
                "world_state": {"dominant_gang": "player_gang"},
                "relationships": {"sojuszniczy_gang": 80, "wrogie_gangi": -100}
            },
            "delayed": {
                48: {
                    "world_changes": {"prison_hierarchy": "gang_controlled"},
                    "new_quests": ["maintain_control", "gang_expansion"],
                    "description": "Twój gang kontroluje więzienie. Ale jak długo?"
                }
            }
        }
        self.add_branch(lead_gang_branch)
        
        # Wynegocjuj pokój
        peace_branch = QuestBranch("negotiate_peace", "Wynegocjuj pokój między gangami")
        peace_branch.requirements = {
            "skill": ("dyplomacja", 50),
            "neutral_reputation": True,
            "respect_all_gangs": 30
        }
        peace_branch.consequences = {
            "immediate": {
                "world_state": {"gang_truce": True},
                "relationships": {"wszystkie_gangi": 40}
            },
            "delayed": {
                168: {
                    "world_changes": {"prison_peace": True},
                    "description": "Pokój trwa. Więzienie jest spokojniejsze."
                }
            }
        }
        self.add_branch(peace_branch)
        
        # Zniszcz wszystkie gangi
        destroy_all_branch = QuestBranch("destroy_all", "Zniszcz wszystkie gangi")
        destroy_all_branch.requirements = {
            "combat_skill": 60,
            "allies": 10,
            "weapons": 5
        }
        destroy_all_branch.consequences = {
            "immediate": {
                "world_state": {"gangs_destroyed": True, "prison_chaos": True},
                "relationships": {"wszyscy": -50}
            },
            "delayed": {
                24: {
                    "world_changes": {"martial_law": True},
                    "description": "Więzienie pod zarządem wojskowym po chaosie."
                }
            }
        }
        self.add_branch(destroy_all_branch)
        
        # Graj gangi przeciwko sobie
        manipulate_branch = QuestBranch("manipulate", "Skłóć gangi między sobą")
        manipulate_branch.requirements = {
            "skill": ("manipulacja", 40),
            "information": "sekrety_gangow",
            "neutral_standing": True
        }
        manipulate_branch.consequences = {
            "immediate": {
                "world_state": {"gang_war_intensified": True},
                "relationships": {}  # Pozostań w cieniu
            },
            "delayed": {
                72: {
                    "world_changes": {"gangs_weakened": True},
                    "new_quests": ["take_advantage"],
                    "description": "Gangi wykrwawiły się. Czas to wykorzystać."
                }
            }
        }
        self.add_branch(manipulate_branch)
    
    def track_conflict_escalation(self, event: Dict) -> Dict[str, Any]:
        """Śledzi eskalację konfliktu"""
        self.conflict_events.append(event)
        
        result = {
            "escalation": False,
            "current_tension": 0,
            "warnings": []
        }
        
        # Oblicz poziom napięcia
        for gang1, tensions in self.gang_tensions.items():
            for gang2, tension in tensions.items():
                if tension > 0.7:
                    result["warnings"].append(
                        f"Krytyczne napięcie między {gang1} a {gang2}"
                    )
                    result["current_tension"] = max(result["current_tension"], tension)
        
        # Sprawdź czy wojna wybuchnie
        if result["current_tension"] > 0.9 and len(self.conflict_events) > 5:
            result["escalation"] = True
            result["war_imminent"] = True
            result["message"] = "Wojna gangów jest nieunikniona!"
        
        return result


class CorruptionExposureQuest(EmergentQuest):
    """Quest ujawnienia korupcji - powstaje gdy gracz odkryje dowody korupcji"""
    
    def __init__(self, quest_id: str, seed: QuestSeed):
        super().__init__(quest_id, seed)
        self.corruption_evidence: List[Dict] = []
        self.corrupt_officials: Dict[str, List[str]] = {}
        self.witness_testimonies: List[Dict] = []
        self.threats_received: int = 0
        
        self._initialize_corruption_network()
        self._initialize_branches()
    
    def _initialize_corruption_network(self):
        """Inicjalizuje sieć korupcji"""
        self.corrupt_officials = {
            "naczelnik": ["lapowki", "przemyt_broni", "falszowanie_raportow"],
            "glowny_straznik": ["sprzedaz_przywilejow", "wymuszenia"],
            "ksiegowy": ["defraudacja", "pranie_pieniedzy"],
            "lekarz": ["handel_lekami", "falszowanie_zwolnien"]
        }
    
    def _initialize_branches(self):
        """Inicjalizuje gałęzie questa korupcji"""
        # Ujawnij korupcję
        expose_branch = QuestBranch("expose_corruption", "Ujawnij korupcję władzom")
        expose_branch.requirements = {
            "evidence_count": 5,
            "witness_count": 3,
            "protection": True  # Ochrona przed zemstą
        }
        expose_branch.consequences = {
            "immediate": {
                "world_state": {"corruption_exposed": True, "prison_investigation": True},
                "relationships": {"uczciwa_straz": 60, "skorumpowani": -100}
            },
            "delayed": {
                168: {
                    "world_changes": {"prison_reformed": True, "new_administration": True},
                    "new_quests": ["witness_protection", "reform_helper"],
                    "description": "Więzienie przeszło gruntowną reformę."
                }
            }
        }
        self.add_branch(expose_branch)
        
        # Szantażuj skorumpowanych
        blackmail_branch = QuestBranch("blackmail", "Szantażuj skorumpowanych")
        blackmail_branch.requirements = {
            "evidence_count": 3,
            "skill": ("szantaz", 30)
        }
        blackmail_branch.consequences = {
            "immediate": {
                "world_state": {"player_blackmailer": True},
                "gold": 1000,
                "relationships": {"skorumpowani": -40}
            },
            "delayed": {
                48: {
                    "world_changes": {"assassination_attempts": True},
                    "description": "Skorumpowani próbują cię uciszyć."
                }
            }
        }
        self.add_branch(blackmail_branch)
        
        # Dołącz do korupcji
        join_branch = QuestBranch("join_corruption", "Dołącz do układu")
        join_branch.requirements = {
            "evidence_count": 2,
            "reputation": ("skorumpowani", 20)
        }
        join_branch.consequences = {
            "immediate": {
                "world_state": {"player_corrupt": True},
                "privileges": ["lepsze_jedzenie", "wiecej_spaceru", "ochrona"],
                "relationships": {"skorumpowani": 50, "uczciwa_straz": -40}
            }
        }
        self.add_branch(join_branch)


class PrisonDiseaseQuest(EmergentQuest):
    """Quest epidemii - powstaje gdy warunki sanitarne są złe"""
    
    def __init__(self, quest_id: str, seed: QuestSeed):
        super().__init__(quest_id, seed)
        self.infection_rate: float = 0.1
        self.infected_npcs: List[str] = []
        self.cured_npcs: List[str] = []
        self.medicine_sources: Dict[str, int] = {}
        self.quarantine_zones: List[str] = []
        
        self._initialize_disease()
        self._initialize_branches()
        
        self.discovery_dialogue = {
            "witnessed": [
                "Widzisz więźnia z gorączką i wysypką.",
                "Zauważasz, że coraz więcej osób kaszle.",
                "Kilku więźniów wymiotuje po posiłku."
            ],
            "environmental": [
                "Czujesz nieprzyjemny zapach choroby w celi.",
                "Wilgoć i pleśń pokrywają ściany.",
                "Szczury biegają wszędzie - mogą roznosić zarazę."
            ]
        }
    
    def _initialize_disease(self):
        """Inicjalizuje parametry choroby"""
        self.disease_properties = {
            "name": random.choice(["Więzienna gorączka", "Szara choroba", "Wilgotny kaszel"]),
            "lethality": random.uniform(0.1, 0.3),
            "spread_rate": random.uniform(0.2, 0.4),
            "incubation_days": random.randint(1, 3),
            "symptoms": ["gorączka", "kaszel", "osłabienie", "wysypka"]
        }
        
        # Początkowo zarażeni
        self.infected_npcs = [f"wiezien_{i}" for i in range(random.randint(2, 5))]
    
    def _initialize_branches(self):
        """Inicjalizuje gałęzie rozwiązania epidemii"""
        # Znajdź lekarstwo
        cure_branch = QuestBranch("find_cure", "Znajdź i rozprowadź lekarstwo")
        cure_branch.requirements = {
            "medicine": 20,
            "skill": ("medycyna", 30),
            "clean_water": True
        }
        cure_branch.consequences = {
            "immediate": {
                "world_state": {"epidemic_controlled": True},
                "relationships": {"wszyscy": 50, "lekarz": 40}
            },
            "delayed": {
                72: {
                    "world_changes": {"health_improved": True},
                    "description": "Więzienie jest zdrowsze. Jesteś bohaterem."
                }
            }
        }
        self.add_branch(cure_branch)
        
        # Wprowadź kwarantannę
        quarantine_branch = QuestBranch("quarantine", "Odizoluj chorych")
        quarantine_branch.requirements = {
            "authority": True,
            "guards_cooperation": True,
            "quarantine_space": True
        }
        quarantine_branch.consequences = {
            "immediate": {
                "world_state": {"quarantine_active": True},
                "relationships": {"chorzy": -30, "zdrowi": 20}
            },
            "delayed": {
                120: {
                    "world_changes": {"disease_contained": True},
                    "description": "Kwarantanna zadziałała, ale wielu zmarło."
                }
            }
        }
        self.add_branch(quarantine_branch)
        
        # Wykorzystaj chaos
        exploit_branch = QuestBranch("exploit_chaos", "Wykorzystaj chaos choroby")
        exploit_branch.requirements = {
            "healthy": True,
            "opportunistic": True
        }
        exploit_branch.consequences = {
            "immediate": {
                "world_state": {"chaos_exploited": True},
                "stolen_goods": ["leki", "jedzenie", "kosztownosci"],
                "relationships": {"chorzy": -60, "straznicy": -20}
            },
            "delayed": {
                48: {
                    "world_changes": {"player_pariah": True},
                    "description": "Wszyscy wiedzą, że wykorzystałeś tragedię."
                }
            }
        }
        self.add_branch(exploit_branch)
    
    def track_infection_spread(self, time_passed: int) -> Dict[str, Any]:
        """Śledzi rozprzestrzenianie się choroby"""
        result = {
            "new_infections": [],
            "deaths": [],
            "recoveries": [],
            "status": "spreading"
        }
        
        # Rozprzestrzenianie
        infection_chance = self.disease_properties["spread_rate"] * (time_passed / 24)
        new_infected_count = int(len(self.infected_npcs) * infection_chance)
        
        for i in range(new_infected_count):
            new_npc = f"wiezien_{random.randint(100, 200)}"
            if new_npc not in self.infected_npcs:
                self.infected_npcs.append(new_npc)
                result["new_infections"].append(new_npc)
        
        # Śmiertelność
        for infected in self.infected_npcs[:]:
            if random.random() < self.disease_properties["lethality"] * (time_passed / 168):
                self.infected_npcs.remove(infected)
                result["deaths"].append(infected)
        
        # Wyzdrowienia (jeśli są leki)
        if self.medicine_sources:
            recovery_rate = sum(self.medicine_sources.values()) / 100
            for infected in self.infected_npcs[:]:
                if random.random() < recovery_rate:
                    self.infected_npcs.remove(infected)
                    self.cured_npcs.append(infected)
                    result["recoveries"].append(infected)
        
        # Określ status
        if len(self.infected_npcs) > 20:
            result["status"] = "epidemic"
        elif len(self.infected_npcs) < 5:
            result["status"] = "contained"
        
        return result


class InformationGatheringQuest(EmergentQuest):
    """Quest zbierania informacji - powstaje gdy gracz szuka konkretnych danych"""
    
    def __init__(self, quest_id: str, seed: QuestSeed):
        super().__init__(quest_id, seed)
        self.target_information: str = ""
        self.information_pieces: Dict[str, Any] = {}
        self.information_sources: Dict[str, List[str]] = {}
        self.false_leads: List[str] = []
        
        self._initialize_information_network()
        self._initialize_branches()
    
    def _initialize_information_network(self):
        """Inicjalizuje sieć informacyjną"""
        self.information_sources = {
            "straznicy": ["harmonogram", "slabe_punkty", "klucze"],
            "wiezniowie": ["tunele", "sojusze", "tajemnice"],
            "personel": ["dostawy", "procedury", "dokumenty"],
            "obserwacja": ["rutyna", "zachowania", "miejsca"]
        }
        
        # Dodaj fałszywe tropy
        self.false_leads = [
            "Tunel w celi 3 (nieprawda)",
            "Strażnik Jan bierze łapówki (nieprawda)",
            "Naczelnik wyjeżdża w piątki (nieprawda)"
        ]
    
    def _initialize_branches(self):
        """Inicjalizuje gałęzie questa informacyjnego"""
        # Sprzedaj informacje
        sell_branch = QuestBranch("sell_information", "Sprzedaj informacje")
        sell_branch.requirements = {
            "complete_information": True,
            "buyer": True
        }
        sell_branch.consequences = {
            "immediate": {
                "gold": 500,
                "relationships": {"kupujacy": 30, "cel_informacji": -50}
            }
        }
        self.add_branch(sell_branch)
        
        # Wykorzystaj osobiście
        use_branch = QuestBranch("use_information", "Wykorzystaj informacje")
        use_branch.requirements = {
            "complete_information": True,
            "skill": ("planowanie", 20)
        }
        use_branch.consequences = {
            "immediate": {
                "advantage": "tactical_knowledge",
                "new_quests": ["execute_plan"]
            }
        }
        self.add_branch(use_branch)
        
        # Wymień na przysługę
        trade_branch = QuestBranch("trade_favor", "Wymień na przysługę")
        trade_branch.requirements = {
            "partial_information": True,
            "negotiation_skill": 30
        }
        trade_branch.consequences = {
            "immediate": {
                "favor_owed": True,
                "relationships": {"informator": 40}
            }
        }
        self.add_branch(trade_branch)


class RevengeQuest(EmergentQuest):
    """Quest zemsty - powstaje gdy NPC lub gracz został skrzywdzony"""
    
    def __init__(self, quest_id: str, seed: QuestSeed, 
                 wronged_party: str, perpetrator: str, offense: str):
        super().__init__(quest_id, seed)
        self.wronged_party = wronged_party
        self.perpetrator = perpetrator
        self.offense = offense
        self.revenge_plans: List[Dict] = []
        self.allies_recruited: List[str] = []
        
        self._initialize_revenge_options()
        self._initialize_branches()
    
    def _initialize_revenge_options(self):
        """Inicjalizuje opcje zemsty"""
        self.revenge_plans = [
            {
                "type": "physical",
                "name": "Brutalna konfrontacja",
                "requirements": ["strength", "weapon"],
                "risk": 0.7
            },
            {
                "type": "social",
                "name": "Zniszczenie reputacji",
                "requirements": ["information", "allies"],
                "risk": 0.3
            },
            {
                "type": "economic",
                "name": "Finansowa ruina",
                "requirements": ["access", "knowledge"],
                "risk": 0.4
            },
            {
                "type": "psychological",
                "name": "Psychologiczna tortura",
                "requirements": ["patience", "cunning"],
                "risk": 0.2
            }
        ]
    
    def _initialize_branches(self):
        """Inicjalizuje gałęzie questa zemsty"""
        # Krwawa zemsta
        violent_branch = QuestBranch("violent_revenge", "Krwawa zemsta")
        violent_branch.requirements = {
            "combat_skill": 40,
            "weapon": True,
            "opportunity": True
        }
        violent_branch.consequences = {
            "immediate": {
                "target_status": "injured_or_dead",
                "relationships": {"target": -100, "witnesses": -30},
                "wanted_level": 3
            }
        }
        self.add_branch(violent_branch)
        
        # Wybacz
        forgive_branch = QuestBranch("forgive", "Wybacz i zapomnij")
        forgive_branch.requirements = {
            "wisdom": 30,
            "emotional_strength": True
        }
        forgive_branch.consequences = {
            "immediate": {
                "karma": 50,
                "relationships": {"target": 20, "witnesses": 40},
                "inner_peace": True
            }
        }
        self.add_branch(forgive_branch)
        
        # Sprawiedliwość
        justice_branch = QuestBranch("seek_justice", "Szukaj sprawiedliwości")
        justice_branch.requirements = {
            "evidence": True,
            "authority_support": True
        }
        justice_branch.consequences = {
            "immediate": {
                "target_status": "punished_legally",
                "relationships": {"authorities": 30, "target": -40},
                "reputation": "just"
            }
        }
        self.add_branch(justice_branch)


def create_quest_seed_library() -> Dict[str, QuestSeed]:
    """Tworzy bibliotekę ziaren questów"""
    seeds = {}
    
    # Seed: Ucieczka z więzienia
    seeds["prison_escape"] = QuestSeed(
        quest_id="prison_escape",
        name="Droga do wolności",
        activation_conditions={
            "location": "wiezienie",
            "player_imprisoned": True,
            "time_in_prison": {"operator": ">", "value": 3}
        },
        discovery_methods=[
            DiscoveryMethod.OVERHEARD,
            DiscoveryMethod.FOUND,
            DiscoveryMethod.WITNESSED
        ],
        initial_clues={
            "cela_5": "Ściana wydaje się słabsza w tym miejscu...",
            "kuchnia": "Słyszałeś, że pod kuchnią jest stara piwnica",
            "dziedziniec": "Strażnicy są mniej czujni podczas zmiany warty"
        },
        time_sensitive=False,
        priority=8
    )
    
    # Seed: Handel przemytem
    seeds["contraband_trade"] = QuestSeed(
        quest_id="contraband_trade",
        name="Czarny rynek więzienny",
        activation_conditions={
            "economy.shortage": {"operator": ">", "value": 0.5},
            "location": "wiezienie"
        },
        discovery_methods=[
            DiscoveryMethod.OVERHEARD,
            DiscoveryMethod.TOLD,
            DiscoveryMethod.WITNESSED
        ],
        initial_clues={
            "stołówka": "Więźniowie szepczą o brakach podstawowych rzeczy",
            "cele": "Ktoś oferuje wysokie ceny za papierosy",
            "wartownia": "Niektórzy strażnicy wydają się... elastyczni"
        },
        time_sensitive=True,
        expiry_hours=120,
        priority=6
    )
    
    # Seed: Wojna gangów
    seeds["gang_war"] = QuestSeed(
        quest_id="gang_war",
        name="Krwawy konflikt",
        activation_conditions={
            "gang_tensions": {"operator": ">", "value": 0.7},
            "recent_violence": True
        },
        discovery_methods=[
            DiscoveryMethod.WITNESSED,
            DiscoveryMethod.TOLD,
            DiscoveryMethod.CONSEQUENCE
        ],
        initial_clues={
            "dziedziniec": "Napięcie wisi w powietrzu podczas spaceru",
            "stołówka": "Grupy siedzą osobno, wymienają wrogie spojrzenia",
            "cele": "Słychać pogróżki i planowanie zemsty"
        },
        time_sensitive=True,
        expiry_hours=48,
        priority=9
    )
    
    # Seed: Korupcja
    seeds["corruption"] = QuestSeed(
        quest_id="corruption",
        name="Brudne tajemnice",
        activation_conditions={
            "discovered_evidence": {"operator": ">=", "value": 1},
            "corruption_level": {"operator": ">", "value": 0.3}
        },
        discovery_methods=[
            DiscoveryMethod.FOUND,
            DiscoveryMethod.TOLD,
            DiscoveryMethod.STUMBLED
        ],
        initial_clues={
            "biuro_naczelnika": "Dokumenty wskazują na nieprawidłowości",
            "magazyn": "Brakuje wielu rzeczy z inwentarza",
            "wartownia": "Strażnicy rozmawiają o dodatkowych zarobkach"
        },
        time_sensitive=False,
        priority=7
    )
    
    # Seed: Epidemia
    seeds["disease_outbreak"] = QuestSeed(
        quest_id="disease_outbreak",
        name="Zaraza w murach",
        activation_conditions={
            "sanitation": {"operator": "<", "value": 0.3},
            "infected_count": {"operator": ">", "value": 2}
        },
        discovery_methods=[
            DiscoveryMethod.WITNESSED,
            DiscoveryMethod.ENVIRONMENTAL
        ],
        initial_clues={
            "cele": "Kilku więźniów ma objawy choroby",
            "latryna": "Okropne warunki sanitarne sprzyjają chorobom",
            "stołówka": "Jedzenie pachnie podejrzanie"
        },
        time_sensitive=True,
        expiry_hours=96,
        priority=8
    )
    
    # Seed: Informator
    seeds["information_network"] = QuestSeed(
        quest_id="information_network",
        name="Sieć szpiegowska",
        activation_conditions={
            "relationships.trust": {"operator": ">", "value": 2},
            "gold": {"operator": ">", "value": 50}
        },
        discovery_methods=[
            DiscoveryMethod.TOLD,
            DiscoveryMethod.OVERHEARD
        ],
        initial_clues={
            "biblioteka": "Niektóre książki zawierają ukryte wiadomości",
            "warsztat": "Rzemieślnicy wymieniają więcej niż towary",
            "kaplica": "Spowiedź to doskonałe źródło informacji"
        },
        time_sensitive=False,
        priority=5
    )
    
    # Seed: Zemsta
    seeds["revenge_plot"] = QuestSeed(
        quest_id="revenge_plot",
        name="Rachunek krzywd",
        activation_conditions={
            "player_wronged": True,
            "time_since_wrong": {"operator": ">", "value": 24}
        },
        discovery_methods=[
            DiscoveryMethod.CONSEQUENCE,
            DiscoveryMethod.TOLD
        ],
        initial_clues={
            "cele": "Ktoś planuje zemstę...",
            "dziedziniec": "Sojusznicy czekają na sygnał",
            "warsztat": "Przygotowywane są narzędzia zemsty"
        },
        time_sensitive=True,
        expiry_hours=72,
        priority=6
    )
    
    # Seed: Bunt więźniów
    seeds["prison_riot"] = QuestSeed(
        quest_id="prison_riot",
        name="Burza nadchodzi",
        activation_conditions={
            "morale": {"operator": "<", "value": 0.2},
            "guard_brutality": {"operator": ">", "value": 0.6},
            "hunger": {"operator": ">", "value": 0.7}
        },
        discovery_methods=[
            DiscoveryMethod.OVERHEARD,
            DiscoveryMethod.TOLD,
            DiscoveryMethod.WITNESSED
        ],
        initial_clues={
            "stołówka": "Więźniowie odmawiają jedzenia",
            "cele": "Słychać skandowanie i bicie w kraty",
            "dziedziniec": "Grupy zbierają się i szepczą"
        },
        time_sensitive=True,
        expiry_hours=24,
        priority=10
    )
    
    # Seed: Tajemnica więzienia
    seeds["prison_mystery"] = QuestSeed(
        quest_id="prison_mystery",
        name="Mroczna tajemnica",
        activation_conditions={
            "explored_areas": {"operator": ">", "value": 5},
            "found_clues": {"operator": ">", "value": 0}
        },
        discovery_methods=[
            DiscoveryMethod.FOUND,
            DiscoveryMethod.STUMBLED,
            DiscoveryMethod.ENVIRONMENTAL
        ],
        initial_clues={
            "piwnica": "Stare krwawe ślady prowadzą donikąd",
            "mur_wschodni": "Dziwne symbole wyryte w kamieniu",
            "stara_cela": "Pamiętnik poprzedniego więźnia"
        },
        time_sensitive=False,
        priority=4
    )
    
    # Seed: Nowy więzień
    seeds["new_prisoner"] = QuestSeed(
        quest_id="new_prisoner",
        name="Świeża krew",
        activation_conditions={
            "new_npc_arrived": True,
            "player_reputation": {"operator": ">", "value": 20}
        },
        discovery_methods=[
            DiscoveryMethod.WITNESSED,
            DiscoveryMethod.TOLD
        ],
        initial_clues={
            "brama": "Przywieziono nowego więźnia",
            "cele": "Nowy jest przerażony i szuka sojuszników",
            "stołówka": "Gangi już go obserwują"
        },
        time_sensitive=True,
        expiry_hours=48,
        priority=5
    )
    
    return seeds


def integrate_quests_with_world(quest_engine, world_state: Dict, npc_manager) -> None:
    """Integruje questy ze stanem świata i NPCami"""
    
    # Monitoruj warunki ekonomiczne
    if world_state.get("economy", {}).get("shortage_level", 0) > 0.5:
        # Aktywuj quest przemytu
        quest_engine.world_state["economy.shortage"] = 0.6
    
    # Monitoruj napięcia między NPCami
    gang_tensions = 0
    for npc in npc_manager.npcs.values():
        for rel in npc.relationships.values():
            if rel.get_overall_disposition() < -50:
                gang_tensions += 0.1
    
    if gang_tensions > 0.7:
        quest_engine.world_state["gang_tensions"] = gang_tensions
        quest_engine.world_state["recent_violence"] = True
    
    # Monitoruj zdrowie więźniów
    sick_count = sum(1 for npc in npc_manager.npcs.values() if npc.health < 50)
    if sick_count > 2:
        quest_engine.world_state["infected_count"] = sick_count
        quest_engine.world_state["sanitation"] = 0.2
    
    # Monitoruj korupcję
    bribed_guards = sum(
        1 for npc in npc_manager.npcs.values() 
        if npc.role == "guard" and "bribed" in npc.semantic_memory
    )
    if bribed_guards > 0:
        quest_engine.world_state["corruption_level"] = bribed_guards / 10
        quest_engine.world_state["discovered_evidence"] = 1
    
    # Monitoruj morale więzienia
    avg_morale = sum(
        npc.emotional_states.get("happy", 0) - npc.emotional_states.get("angry", 0)
        for npc in npc_manager.npcs.values()
    ) / len(npc_manager.npcs)
    
    quest_engine.world_state["morale"] = avg_morale
    
    # Monitoruj brutalność strażników
    guard_brutality = sum(
        1 for event in npc_manager.world_events
        if event.get("type") == "guard_violence"
    ) / max(1, len(npc_manager.world_events))
    
    quest_engine.world_state["guard_brutality"] = guard_brutality
    
    # Monitoruj głód
    avg_hunger = sum(npc.hunger for npc in npc_manager.npcs.values()) / len(npc_manager.npcs)
    quest_engine.world_state["hunger"] = avg_hunger / 100


class QuestIntegrationManager:
    """Manager integrujący questy z resztą gry"""
    
    def __init__(self, quest_engine=None, game_state=None, npc_manager=None):
        self.quest_engine = quest_engine
        self.game_state = game_state
        self.npc_manager = npc_manager
        self.quest_factory = {
            "prison_escape": PrisonEscapeQuest,
            "contraband_trade": ContrabandTradeQuest,
            "gang_war": PrisonGangWarQuest,
            "corruption": CorruptionExposureQuest,
            "disease_outbreak": PrisonDiseaseQuest,
            "information_network": InformationGatheringQuest,
            "revenge_plot": RevengeQuest
        }
        
        # Zarejestruj wszystkie ziarna questów
        self.register_all_seeds()
    
    def register_all_seeds(self):
        """Rejestruje wszystkie ziarna questów"""
        seeds = create_quest_seed_library()
        for seed in seeds.values():
            self.quest_engine.register_seed(seed)
    
    def create_quest_from_seed(self, seed: QuestSeed) -> EmergentQuest:
        """Tworzy konkretny quest z ziarna"""
        quest_class = self.quest_factory.get(seed.quest_id, EmergentQuest)
        
        if seed.quest_id == "revenge_plot":
            # Specjalne parametry dla questa zemsty
            return quest_class(
                seed.quest_id, seed,
                wronged_party="player",
                perpetrator="unknown",
                offense="betrayal"
            )
        else:
            return quest_class(seed.quest_id, seed)
    
    def update(self):
        """Aktualizuje system questów"""
        # Zsynchronizuj stan świata
        self.sync_world_state()
        
        # Aktualizuj silnik questów
        self.quest_engine.update(datetime.now())
        
        # Przetwórz konsekwencje questów
        self.process_quest_consequences()
        
        # Sprawdź nowe odkrycia
        self.check_quest_discoveries()
    
    def sync_world_state(self):
        """Synchronizuje stan świata z questami"""
        # Podstawowe dane o graczu
        if self.game_state.player:
            self.quest_engine.player_state = {
                "location": self.game_state.current_location,
                "health": self.game_state.player.health,
                "gold": self.game_state.player.gold,
                "inventory": self.game_state.player.inventory if isinstance(self.game_state.player.inventory, list) else list(self.game_state.player.inventory.keys()),
                "skills": {
                    skill.name.value: skill.level 
                    for skill in self.game_state.player.skills.skills.values()
                },
                "relationships": {},
                "completed_quests": self.quest_engine.completed_quests
            }
            
            # Relacje z NPCami
            for npc_id, npc in self.npc_manager.npcs.items():
                rel = npc.get_relationship("player")
                self.quest_engine.player_state["relationships"][npc_id] = \
                    rel.get_overall_disposition()
        
        # Stan więzienia
        self.quest_engine.world_state.update({
            "location": "wiezienie",
            "player_imprisoned": True,
            "time_in_prison": self.game_state.time_in_prison if hasattr(self.game_state, 'time_in_prison') else 10,
            "current_time": time.time()
        })
        
        # Integruj ze światem
        integrate_quests_with_world(
            self.quest_engine,
            self.quest_engine.world_state,
            self.npc_manager
        )
    
    def process_quest_consequences(self):
        """Przetwarza konsekwencje questów"""
        for consequence in self.quest_engine.consequence_queue[:]:
            if consequence.is_due(datetime.now()):
                # Zastosuj zmiany w świecie gry
                for key, value in consequence.world_changes.items():
                    if key == "prison_alert":
                        self.game_state.prison_alert_level = value
                    elif key == "player_wanted":
                        self.game_state.player_wanted = value
                    elif key == "contraband_monopoly":
                        self.game_state.contraband_controller = value
                
                # Zastosuj reakcje NPCów
                for npc_id, reaction in consequence.npc_reactions.items():
                    if npc_id in self.npc_manager.npcs:
                        npc = self.npc_manager.npcs[npc_id]
                        if reaction == "wściekły":
                            npc.modify_emotion("ANGRY", 0.8)
                        elif reaction == "poszukiwania":
                            npc.current_state = "PATROLLING"
                
                # Aktywuj nowe questy
                for seed_id in consequence.new_quest_seeds:
                    if seed_id in self.quest_engine.quest_seeds:
                        seed = self.quest_engine.quest_seeds[seed_id]
                        new_quest = self.create_quest_from_seed(seed)
                        self.quest_engine.active_quests[seed_id] = new_quest
    
    def check_quest_discoveries(self):
        """Sprawdza czy gracz odkrył nowe questy"""
        location = self.game_state.current_location
        discovery = self.quest_engine.discover_quest(location)
        
        if discovery:
            # Powiadom gracza o odkryciu
            self.game_state.add_message(
                f"[QUEST] {discovery['dialogue']}",
                message_type="quest"
            )
            
            # Dodaj wskazówki do dziennika
            for clue_location, clue_text in discovery.get('initial_clues', {}).items():
                self.game_state.add_journal_entry(
                    f"Wskazówka w {clue_location}: {clue_text}"
                )
    
    def handle_player_action(self, action: str, target: str = None) -> Dict[str, Any]:
        """Obsługuje akcje gracza związane z questami"""
        result = {"success": False, "messages": []}
        
        # Sprawdź czy akcja dotyczy aktywnego questa
        for quest_id, quest in self.quest_engine.active_quests.items():
            if quest.state in [QuestState.ACTIVE, QuestState.INVESTIGATING]:
                # Prowadź śledztwo
                if action in ["investigate", "search", "interrogate", "scout"]:
                    inv_result = quest.investigate(
                        action, target,
                        self.quest_engine.player_state
                    )
                    
                    if inv_result["success"]:
                        result["success"] = True
                        result["messages"].extend(inv_result["dialogue"])
                        
                        # Sprawdź postęp
                        progress = quest.investigation.get_completion_percentage(10)
                        result["messages"].append(
                            f"Postęp śledztwa: {progress:.0f}%"
                        )
                
                # Próba rozwiązania
                elif action == "resolve":
                    branches = self.quest_engine.get_available_branches(quest_id)
                    if branches and target in [b['id'] for b in branches]:
                        resolution = self.quest_engine.resolve_quest(quest_id, target)
                        result["success"] = resolution["success"]
                        result["messages"].append(resolution.get("dialogue", ""))
                        
                        # Informuj o konsekwencjach
                        if resolution.get("immediate_effects"):
                            result["messages"].append(
                                f"Natychmiastowe efekty: {resolution['immediate_effects']}"
                            )
                        if resolution.get("scheduled_effects"):
                            result["messages"].append(
                                f"Zaplanowano {resolution['scheduled_effects']} przyszłych konsekwencji"
                            )
        
        return result
    
    def get_active_quest_hints(self) -> List[str]:
        """Zwraca podpowiedzi dla aktywnych questów"""
        hints = []
        
        for quest in self.quest_engine.active_quests.values():
            if quest.state == QuestState.DISCOVERABLE:
                hints.append(f"Coś się dzieje w {list(quest.seed.initial_clues.keys())[0]}...")
            elif quest.state == QuestState.ACTIVE:
                hints.append(f"{quest.seed.name}: Zbierz więcej informacji")
            elif quest.state == QuestState.INVESTIGATING:
                progress = quest.investigation.get_completion_percentage(10)
                hints.append(f"{quest.seed.name}: {progress:.0f}% odkryte")
        
        return hints


# Alias dla kompatybilności wstecznej
EmergentQuestIntegration = QuestIntegrationManager