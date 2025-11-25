"""
Definicje emergentnych questów więziennych z pełnymi dialogami i ścieżkami.
Każdy quest ma wiele rozwiązań, konsekwencje i naturalne odkrycia.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from quests.quest_engine import (
    QuestSeed, EmergentQuest, QuestBranch, DiscoveryMethod,
    ConsequenceEvent, QuestState
)


class PrisonFoodConflictQuest(EmergentQuest):
    """Quest: Konflikt o jedzenie - aktywuje się gdy zapasy spadną poniżej 10."""
    
    def __init__(self):
        seed = QuestSeed(
            quest_id="prison_food_conflict",
            name="Głód w celach",
            activation_conditions={
                'prison.food_supplies': {'operator': '<', 'value': 10},
                'player.location': 'prison'
            },
            discovery_methods=[
                DiscoveryMethod.OVERHEARD,
                DiscoveryMethod.WITNESSED,
                DiscoveryMethod.ENVIRONMENTAL
            ],
            initial_clues={
                'prison_corridor': 'Słychać podniesione głosy dobiegające z cel. Ktoś krzyczy o jedzeniu.',
                'prison_cafeteria': 'Kuchnia jest prawie pusta. Strażnicy wyglądają na zaniepokojonych.',
                'cell_block_a': 'Więźniowie szepczą między sobą, niektórzy ukrywają małe porcje jedzenia.'
            },
            time_sensitive=True,
            expiry_hours=48,
            priority=8
        )
        super().__init__("prison_food_conflict", seed)
        
        # Dialogi odkrycia
        self.discovery_dialogue = {
            'overheard': [
                "Podsłuchujesz rozmowę strażników:\n'Zapasy się kończą. Jeśli nie dostaniemy dostawy, będzie bunt.'",
                "Słyszysz jak Brutus warczy:\n'Kto ukrywa żarcie, ten nie dożyje rana!'"
            ],
            'witnessed': [
                "Widzisz jak dwóch więźniów bije się o kawałek chleba. Strażnicy tylko patrzą.",
                "Dostrzegasz jak młody więzień zemdlał z głodu. Nikt mu nie pomaga."
            ],
            'environmental': [
                "Atmosfera w więzieniu jest napięta. Wszyscy są głodni i zdesperowani.",
                "Zauważasz że porcje jedzenia są coraz mniejsze. Niektórzy więźniowie już drugi dzień nic nie jedli."
            ]
        }
        
        # Tworzenie gałęzi rozwiązań
        self._create_branches()
        
    def _create_branches(self):
        """Tworzy wszystkie możliwe ścieżki rozwiązania."""
        
        # ŚCIEŻKA 1: Kradzież z magazynu strażników
        stealth_branch = QuestBranch(
            "stealth_theft",
            "Wykradnij jedzenie z magazynu strażników"
        )
        stealth_branch.add_requirement('skill', ('stealth', 5))
        stealth_branch.add_requirement('item', 'lockpick')
        stealth_branch.dialogue_options = {
            'preview': "Mógłbym się zakraść do magazynu strażników...",
            'resolution': "Udało ci się wykraść zapasy. Rozdajesz je potajemnie współwięźniom. Zyskujesz ich szacunek, ale ryzykujesz gniew strażników.",
            'npc_brutus': "Brutus kiwa głową z uznaniem: 'Masz jaja, szamanie. Pamiętaj tylko, że nie widziałem nic.'",
            'npc_guard': "Strażnik podejrzliwie się rozgląda: 'Ktoś był w magazynie... Znajdę skurwysyna.'"
        }
        stealth_branch.add_consequence('world_state', {
            'prison.food_supplies': 25,
            'prison.guard_alert_level': 8,
            'prison.tension': -20
        })
        stealth_branch.add_consequence('relationships', {
            'Brutus': 15,
            'prisoners': 20,
            'guards': -30
        })
        stealth_branch.add_consequence('delayed', {
            24: {
                'description': 'Strażnicy przeprowadzają rewizję cel',
                'world_changes': {'prison.security': 'high'},
                'npc_reactions': {
                    'guard_captain': 'Ktokolwiek to zrobił, znajdę go i będzie żałował!'
                }
            }
        })
        self.add_branch(stealth_branch)
        
        # ŚCIEŻKA 2: Negocjacje z naczelnikiem
        diplomacy_branch = QuestBranch(
            "diplomacy_warden",
            "Przekonaj naczelnika do sprowadzenia dostaw"
        )
        diplomacy_branch.add_requirement('skill', ('persuasion', 7))
        diplomacy_branch.add_requirement('reputation', ('guards', 0))
        diplomacy_branch.dialogue_options = {
            'preview': "Mógłbym spróbować porozmawiać z naczelnikiem...",
            'resolution': "Naczelnik zgadza się przyspieszyć dostawy. 'Nie chcę buntu na mojej zmianie' - mówi.",
            'dialogue_warden': [
                "Gracz: 'Panie naczelniku, sytuacja jest krytyczna. Więźniowie są zdesperowani.'",
                "Naczelnik: 'Wiem o problemie. Ale skąd mam wziąć jedzenie?'",
                "Gracz: 'Może uda się dogadać z lokalnym kupcem? Zapłacić później?'",
                "Naczelnik: 'Hmm... Zobaczę co da się zrobić. Ale ty będziesz odpowiedzialny za spokój do tego czasu.'",
                "Gracz: 'Poradzę sobie. Dziękuję.'",
                "Naczelnik: 'Nie dziękuj. Jeśli wybuchnie bunt, pierwszy pójdziesz do karceru.'"
            ]
        }
        diplomacy_branch.add_consequence('world_state', {
            'prison.food_supplies': 40,
            'prison.tension': -30,
            'prison.warden_debt': 500
        })
        diplomacy_branch.add_consequence('relationships', {
            'warden': 10,
            'prisoners': 15,
            'Brutus': -5  # Brutus uważa to za słabość
        })
        diplomacy_branch.add_consequence('delayed', {
            72: {
                'description': 'Kupiec przychodzi po zapłatę',
                'world_changes': {'prison.merchant_waiting': True},
                'new_quests': ['merchant_debt_quest']
            }
        })
        self.add_branch(diplomacy_branch)
        
        # ŚCIEŻKA 3: Organizacja polowania
        survival_branch = QuestBranch(
            "organize_hunt",
            "Zorganizuj potajemne polowanie poza murami"
        )
        survival_branch.add_requirement('skill', ('survival', 6))
        survival_branch.add_requirement('skill', ('leadership', 5))
        survival_branch.dialogue_options = {
            'preview': "Może uda się zorganizować wyprawę łowiecką...",
            'resolution': "Przekonujesz kilku zaufanych więźniów i jednego przekupnego strażnika. Nocą wymykacie się na polowanie.",
            'hunt_dialogue': [
                "Gracz do więźniów: 'Słuchajcie, znam las. Możemy upolować zwierzynę.'",
                "Więzień 1: 'To samobójstwo! Strażnicy nas zabiją!'",
                "Gracz: 'Nie jeśli jeden z nich będzie z nami. Znam takiego, co lubi złoto.'",
                "Więzień 2: 'A co jeśli to pułapka?'",
                "Gracz: 'To zdychamy z głodu albo próbujemy. Wybór należy do was.'",
                "Brutus: 'Szaman ma rację. Lepiej zginąć walcząc niż z głodu jak pies.'"
            ]
        }
        survival_branch.add_consequence('world_state', {
            'prison.food_supplies': 30,
            'prison.illegal_activity': True,
            'forest.wildlife': -2
        })
        survival_branch.add_consequence('relationships', {
            'Brutus': 25,
            'prisoners': 30,
            'corrupt_guard': 20,
            'guards': -15
        })
        survival_branch.add_consequence('delayed', {
            48: {
                'description': 'Więźniowie chcą powtórzyć wyprawę',
                'world_changes': {'prison.hunt_demand': True},
                'npc_reactions': {
                    'prisoners': 'To było niesamowite! Kiedy znowu idziemy?',
                    'Brutus': 'Szaman pokazał nam drogę do wolności... i mięsa!'
                }
            },
            168: {  # Tydzień później
                'description': 'Strażnicy odkrywają ślady nielegalnych polowań',
                'world_changes': {'prison.investigation': True},
                'new_quests': ['hunting_investigation_quest']
            }
        })
        self.add_branch(survival_branch)
        
        # ŚCIEŻKA 4: Handel z więźniami
        trade_branch = QuestBranch(
            "prisoner_trade",
            "Zorganizuj system wymiany i racjonowania"
        )
        trade_branch.add_requirement('skill', ('barter', 4))
        trade_branch.add_requirement('reputation', ('prisoners', 10))
        trade_branch.dialogue_options = {
            'preview': "Może uda się lepiej zarządzać tym co mamy...",
            'resolution': "Organizujesz sprawiedliwy system podziału. Ci którzy mają ukryte zapasy dzielą się za przysługi.",
            'trade_setup': [
                "Gracz: 'Posłuchajcie! Jeśli będziemy walczyć między sobą, wszyscy zginiemy!'",
                "Głos z tłumu: 'Łatwo mówić jak się ma pełny brzuch!'",
                "Gracz: 'Proponuję układ. Ci co mają zapasy, podzielą się. W zamian dostaną ochronę i przysługi.'",
                "Więzień z zapasami: 'A co jeśli odmówię?'",
                "Brutus: 'To ja osobiście sprawdzę co ukrywasz w swojej pryczy.'",
                "Gracz: 'Spokojnie Brutus. Nikt nie będzie zmuszany. Ale ci co pomogą, będą pamiętani.'",
                "Więzień z zapasami: '...Dobra. Mam trochę suszonego mięsa. Ale chcę dodatkowy koc i ochronę.'",
                "Gracz: 'Zgoda. Kto jeszcze?'"
            ]
        }
        trade_branch.add_consequence('world_state', {
            'prison.food_supplies': 18,
            'prison.tension': -15,
            'prison.trade_system': True
        })
        trade_branch.add_consequence('relationships', {
            'prisoners': 20,
            'Brutus': 10,
            'wealthy_prisoners': -10
        })
        trade_branch.add_consequence('delayed', {
            36: {
                'description': 'System handlu się rozwija',
                'world_changes': {'prison.economy': 'barter_system'},
                'npc_reactions': {
                    'prisoners': 'Ten system działa! Szaman wie co robi.'
                }
            }
        })
        self.add_branch(trade_branch)
        
        # ŚCIEŻKA 5: Siłowe przejęcie zapasów
        violence_branch = QuestBranch(
            "force_redistribution", 
            "Siłą zabierz zapasy tym którzy ukrywają"
        )
        violence_branch.add_requirement('skill', ('intimidation', 6))
        violence_branch.add_requirement('skill', ('combat', 5))
        violence_branch.dialogue_options = {
            'preview': "Niektórzy ukrywają jedzenie. Może czas to zmienić...",
            'resolution': "Z pomocą Brutusa i jego ludzi zabieracie ukryte zapasy. Krew się leje, ale głodni dostają jedzenie.",
            'violence_scene': [
                "Gracz: 'Brutus, wiem kto ukrywa żarcie. Czas wyrównać rachunki.'",
                "Brutus: 'Nareszcie ktoś z jajami! Kogo bierzemy na celownik?'",
                "Gracz: 'Celę 4B, 7A i tego grubasa z pralni. Mają zapasy na tygodnie.'",
                "Brutus: 'Hehe, grubasek będzie płakał. Idziemy!'",
                "",
                "[Scena przemocy]",
                "Więzień: 'Nie! To moje! Uczciwie na to zarobiłem!'",
                "Brutus: *cios pięścią* 'Teraz jest nasze. Masz problem?'",
                "Gracz: 'Dość Brutus. Zabieramy jedzenie, nie życie.'",
                "Brutus: 'Jak chcesz szamanie. Ale następnym razem...'",
                "",
                "Gracz do innych: 'Jedzenie będzie rozdzielone sprawiedliwie. Ale kto spróbuje ukrywać, skończy jak oni.'"
            ]
        }
        violence_branch.add_consequence('world_state', {
            'prison.food_supplies': 22,
            'prison.violence_level': 8,
            'prison.fear': 7
        })
        violence_branch.add_consequence('relationships', {
            'Brutus': 30,
            'violent_prisoners': 25,
            'peaceful_prisoners': -20,
            'victims': -50
        })
        violence_branch.add_consequence('delayed', {
            12: {
                'description': 'Ofiary knują zemstę',
                'world_changes': {'prison.revenge_plot': True},
                'npc_reactions': {
                    'victim_1': 'Szaman i Brutus za to zapłacą...'
                }
            },
            96: {
                'description': 'Próba otrucia twojego jedzenia',
                'world_changes': {'player.poisoning_attempt': True},
                'new_quests': ['poisoning_revenge_quest']
            }
        })
        self.add_branch(violence_branch)
        
        # ŚCIEŻKA 6: Rytuał przywołania obfitości (magiczna)
        magic_branch = QuestBranch(
            "abundance_ritual",
            "Odpraw rytuał szamański przywołujący obfitość"
        )
        magic_branch.add_requirement('skill', ('shamanism', 8))
        magic_branch.add_requirement('item', 'ritual_components')
        magic_branch.dialogue_options = {
            'preview': "Duchy mogą nam pomóc... jeśli odprawię właściwy rytuał...",
            'resolution': "Odprawiasz starożytny rytuał. Następnego ranka strażnicy znajdują tajemnicze pudła z jedzeniem przed bramą.",
            'ritual_scene': [
                "Szykujesz się do rytuału w celi. Inni więźniowie patrzą z mieszanką strachu i nadziei.",
                "",
                "Gracz: 'Duchy przodków, słuchajcie mego wołania!'",
                "Brutus szepcze: 'Czy to naprawdę zadziała?'",
                "Gracz: 'Milcz! *zapala kadzidło* Ofiaruję wam dym i krew, przynieście nam pożywienie!'",
                "",
                "[Cela wypełnia się dziwnym światłem. Temperatura spada.]",
                "",
                "Głos z Zaświatów: 'Szamanie... twoja prośba została wysłuchana... ale wszystko ma swoją cenę...'",
                "Gracz: 'Jestem gotów zapłacić.'",
                "Głos: 'Pamiętaj te słowa... gdy przyjdzie czas...'",
                "",
                "[Następnego ranka]",
                "Strażnik: 'Co do cholery?! Skąd się wzięły te skrzynie?!'",
                "Naczelnik: 'Nieważne skąd! Sprawdźcie czy nie są zatrute i rozdajcie więźniom.'",
                "Brutus do gracza: 'Szaman... jesteś prawdziwym czarownikiem. Ale co miał na myśli ten głos?'"
            ]
        }
        magic_branch.add_consequence('world_state', {
            'prison.food_supplies': 50,
            'prison.supernatural_events': True,
            'player.spirit_debt': True
        })
        magic_branch.add_consequence('relationships', {
            'prisoners': 40,
            'Brutus': 35,
            'guards': -10,  # Boją się
            'spirits': 20
        })
        magic_branch.add_consequence('delayed', {
            168: {  # Tydzień później
                'description': 'Duchy przychodzą po zapłatę',
                'world_changes': {'player.spirit_summons': True},
                'new_quests': ['spirit_debt_quest'],
                'npc_reactions': {
                    'spirit_messenger': 'Czas spłacić dług, szamanie...'
                }
            }
        })
        self.add_branch(magic_branch)
    
    def _get_npc_dialogue(self, npc: str, attitude: str) -> str:
        """Zwraca specyficzne dialogi NPC dla tego questa."""
        dialogues = {
            'Brutus': {
                'friendly': "Brutus: 'Szamanie, głód sprawia że ludzie robią głupie rzeczy. Jeśli masz plan, jestem z tobą.'",
                'neutral': "Brutus: 'Hmm, szaman się kręci. Coś kombinujesz? Lepiej żeby to było coś mądrego.'",
                'hostile': "Brutus: 'Spadaj szamanie. Nie mam czasu na twoje gadki gdy moi ludzie głodują.'"
            },
            'guard_captain': {
                'friendly': "Kapitan: 'Wiem że jesteś rozsądny. Pomóż mi utrzymać porządek, a zobaczę co da się zrobić.'",
                'neutral': "Kapitan: 'Więzień nie powinien się wtrącać w sprawy zaopatrzenia.'",
                'hostile': "Kapitan: 'Jeszcze słowo a trafisz do karceru! Mam dość kłopotów!'"
            },
            'hungry_prisoner': {
                'friendly': "Więzień: 'Szamanie, błagam, moje dzieci... jeśli umrę, nie będą miały nikogo...'",
                'neutral': "Więzień: 'Słyszałem że potrafisz rzeczy... może możesz coś zrobić?'",
                'hostile': "Więzień: 'Ty też pewnie coś ukrywasz! Wszyscy jesteście tacy sami!'"
            }
        }
        
        if npc in dialogues and attitude in dialogues[npc]:
            return dialogues[npc][attitude]
        return f"{npc} mamrocze coś o głodzie i desperacji."


class GuardKeysLostQuest(EmergentQuest):
    """Quest: Zgubione klucze strażnika - losowo co 3 dni."""
    
    def __init__(self):
        seed = QuestSeed(
            quest_id="guard_keys_lost",
            name="Zgubione klucze",
            activation_conditions={
                'days_passed': {'operator': '>=', 'value': 3},
                'random_chance': {'operator': '>', 'value': 0.3}
            },
            discovery_methods=[
                DiscoveryMethod.OVERHEARD,
                DiscoveryMethod.WITNESSED,
                DiscoveryMethod.FOUND
            ],
            initial_clues={
                'wartownia': 'Strażnik nerwowo przeszukuje kieszenie i rozgląda się.',
                'dziedziniec': 'Coś metalowego błyszczy w kącie dziedzińca.',
                'jadalnia': 'Słychać brzęk metalu w koszu z brudnym praniem.'
            },
            time_sensitive=True,
            expiry_hours=24,
            priority=6
        )
        super().__init__("guard_keys_lost", seed)
        
        self.discovery_dialogue = {
            'overheard': [
                "Słyszysz spanikowanego strażnika:\n'Kurwa, gdzie są moje klucze?! Kapitan mnie zabije!'",
                "Dwóch strażników szepcze:\n'Jenkins zgubił klucze. Jeśli dowódca się dowie...'"
            ],
            'witnessed': [
                "Widzisz jak strażnik Jenkins gorączkowo przeszukuje dziedziniec.",
                "Zauważasz że jeden strażnik nie może otworzyć celi. Wygląda na przerażonego."
            ],
            'found': [
                "Potykasz się o coś metalowego. To pęk kluczy z symbolem straży!",
                "W pralni znajdujesz klucze do cel. Ktoś musiał je zgubić."
            ]
        }
        
        self._create_branches()
        
    def _create_branches(self):
        """Tworzy ścieżki rozwiązania questa kluczy."""
        
        # ŚCIEŻKA 1: Zwróć klucze strażnikowi
        return_branch = QuestBranch(
            "return_keys",
            "Zwróć klucze strażnikowi Jenkins"
        )
        return_branch.dialogue_options = {
            'preview': "Powinienem oddać klucze. Jenkins wygląda na zdesperowanego.",
            'resolution': "Oddajesz klucze wdzięcznemu strażnikowi. Zyskujesz jego wdzięczność.",
            'return_scene': [
                "Gracz: 'Jenkins, szukasz czegoś?'",
                "Jenkins: *rozgląda się nerwowo* 'Nie... znaczy tak... ale to nie twoja sprawa więźniu!'",
                "Gracz: *pokazuje klucze* 'Może tego?'",
                "Jenkins: *oczy się rozszerzają* 'Gdzie... gdzie je znalazłeś?!'",
                "Gracz: 'Nieważne. Bierz zanim ktoś zauważy.'",
                "Jenkins: *chwyta klucze* 'Dzięki... Jestem ci winien przysługę. Dużą przysługę.'",
                "Gracz: 'Pamiętaj o tym gdy będę czegoś potrzebował.'",
                "Jenkins: 'Tak... jasne. Tylko... nikomu nie mów, dobrze?'"
            ]
        }
        return_branch.add_consequence('world_state', {
            'guard_jenkins.has_keys': True,
            'guard_jenkins.owes_favor': True
        })
        return_branch.add_consequence('relationships', {
            'Jenkins': 50,
            'guards': 10
        })
        return_branch.add_consequence('delayed', {
            72: {
                'description': 'Jenkins oferuje pomoc',
                'npc_reactions': {
                    'Jenkins': 'Hej, pamiętasz jak mi pomogłeś? Mogę załatwić ci dodatkową porcję...'
                }
            }
        })
        self.add_branch(return_branch)
        
        # ŚCIEŻKA 2: Wykorzystaj klucze do ucieczki
        escape_branch = QuestBranch(
            "use_for_escape",
            "Użyj kluczy do próby ucieczki"
        )
        escape_branch.add_requirement('skill', ('stealth', 7))
        escape_branch.add_requirement('skill', ('athletics', 6))
        escape_branch.dialogue_options = {
            'preview': "Te klucze to moja szansa na wolność...",
            'resolution': "Używasz kluczy do otwarcia cel, ale ucieczka kończy się niepowodzeniem. Tracisz klucze i wolność.",
            'escape_attempt': [
                "Czekasz do nocy. Gdy wszystko cichnie, używasz kluczy.",
                "",
                "*Otwierasz swoją celę*",
                "Przekradasz się korytarzem. Serce bije jak szalone.",
                "",
                "*Otwierasz kolejne drzwi*",
                "Jeszcze tylko jedna brama...",
                "",
                "Głos z ciemności: 'Naprawdę myślałeś że to takie proste?'",
                "Kapitan straży: 'Jenkins doniósł że zgubił klucze. Czekaliśmy.'",
                "",
                "*Strażnicy otaczają cię*",
                "Kapitan: 'Do karceru z nim! Miesiąc o chlebie i wodzie!'",
                "",
                "Gdy cię prowadzą, słyszysz Brutusa: 'Głupiec... Trzeba było ze mną gadać.'"
            ]
        }
        escape_branch.add_consequence('world_state', {
            'player.in_solitary': True,
            'prison.security': 'maximum',
            'guard_keys.lost': False
        })
        escape_branch.add_consequence('relationships', {
            'guards': -50,
            'Jenkins': -30,
            'Brutus': -20,
            'prisoners': 15  # Szacunek za odwagę
        })
        escape_branch.add_consequence('delayed', {
            720: {  # 30 dni karceru
                'description': 'Wychodzisz z karceru',
                'world_changes': {'player.in_solitary': False},
                'npc_reactions': {
                    'Brutus': 'Wyglądasz jak śmierć. Następnym razem pomyśl zanim zrobisz coś głupiego.'
                }
            }
        })
        self.add_branch(escape_branch)
        
        # ŚCIEŻKA 3: Sprzedaj klucze Brutusowi
        sell_branch = QuestBranch(
            "sell_to_brutus",
            "Sprzedaj klucze Brutusowi"
        )
        sell_branch.add_requirement('reputation', ('Brutus', -10))
        sell_branch.dialogue_options = {
            'preview': "Brutus na pewno zapłaci dobrze za takie klucze...",
            'resolution': "Sprzedajesz klucze Brutusowi. Zyskujesz przysługi ale Jenkins będzie miał kłopoty.",
            'negotiation': [
                "Gracz: 'Brutus, mam coś co może cię zainteresować.'",
                "Brutus: 'Mów szamanie, nie mam czasu.'",
                "Gracz: *pokazuje klucze* 'Klucze strażnika. Otwierają każdą celę.'",
                "Brutus: *oczy błyszczą* 'Ho ho! Gdzie je wziąłeś?'",
                "Gracz: 'Nieważne. Interesuje cię handel?'",
                "Brutus: 'Co chcesz za nie?'",
                "Gracz: 'Ochronę. I informacje gdy coś się szykuje.'",
                "Brutus: 'Zgoda. Ale jeśli mnie wydasz...'",
                "Gracz: 'Nie wyddam. Masz moje słowo szamana.'",
                "Brutus: *bierze klucze* 'Dobry jesteś szamanie. Jenkins będzie płakał haha!'"
            ]
        }
        sell_branch.add_consequence('world_state', {
            'brutus.has_keys': True,
            'guard_jenkins.in_trouble': True,
            'prison.contraband_level': 8
        })
        sell_branch.add_consequence('relationships', {
            'Brutus': 40,
            'Jenkins': -60,
            'guards': -20
        })
        sell_branch.add_consequence('delayed', {
            24: {
                'description': 'Jenkins zostaje ukarany',
                'world_changes': {'guard_jenkins.demoted': True},
                'npc_reactions': {
                    'Jenkins': 'To ty! Ty mi to zrobiłeś! Pożałujesz tego!'
                }
            },
            48: {
                'description': 'Brutus używa kluczy',
                'world_changes': {'prison.brutus_escape_plan': True},
                'new_quests': ['brutus_escape_conspiracy']
            }
        })
        self.add_branch(sell_branch)
        
        # ŚCIEŻKA 4: Podrzuć klucze wrogowi
        frame_branch = QuestBranch(
            "frame_enemy",
            "Podrzuć klucze wrogowi żeby go wrobić"
        )
        frame_branch.add_requirement('skill', ('deception', 5))
        frame_branch.dialogue_options = {
            'preview': "Mogę wykorzystać to żeby pozbyć się wroga...",
            'resolution': "Podrzucasz klucze wrogowi i donosisz strażnikom. Twój wróg trafia do karceru.",
            'frame_scene': [
                "Wkradasz się do celi swojego wroga gdy śpi.",
                "*Wsuwasz klucze pod jego pryczę*",
                "",
                "Później tego dnia...",
                "Gracz do strażnika: 'Panie strażniku, widziałem jak Szczur chował coś pod łóżkiem.'",
                "Strażnik: 'Szczur? Ten złodziejaszek? Sprawdzimy to.'",
                "",
                "[Rewizja w celi Szczura]",
                "Strażnik: 'No no, co my tu mamy? Klucze Jenkinsa!'",
                "Szczur: 'To nie moje! Ktoś mi podrzucił!'",
                "Strażnik: 'Jasne, a ja jestem królową Anglii. Do karceru!'",
                "Szczur gdy go prowadzą: 'TO TY SZAMANIE! WIEM ŻE TO TY! ZEMSTA!'"
            ]
        }
        frame_branch.add_consequence('world_state', {
            'enemy.in_solitary': True,
            'guard_keys.recovered': True
        })
        frame_branch.add_consequence('relationships', {
            'enemy': -100,
            'enemy_gang': -40,
            'guards': 5
        })
        frame_branch.add_consequence('delayed', {
            360: {  # 15 dni później
                'description': 'Wróg wraca z karceru',
                'world_changes': {'enemy.seeking_revenge': True},
                'npc_reactions': {
                    'enemy': 'Szamanie... przygotuj się na piekło.'
                },
                'new_quests': ['enemy_revenge_quest']
            }
        })
        self.add_branch(frame_branch)
        
        # ŚCIEŻKA 5: Zrób kopie kluczy
        copy_branch = QuestBranch(
            "make_copies",
            "Zrób kopie kluczy zanim je zwrócisz"
        )
        copy_branch.add_requirement('skill', ('crafting', 6))
        copy_branch.add_requirement('item', 'wax_or_clay')
        copy_branch.dialogue_options = {
            'preview': "Jeśli zrobię odlewy, będę miał kopie...",
            'resolution': "Robisz woskowe odlewy kluczy. Zwracasz oryginały ale zachowujesz możliwość zrobienia kopii.",
            'copying_process': [
                "W warsztacie więziennym znajdujesz wosk ze świec.",
                "Ostrożnie robisz odlewy każdego klucza.",
                "",
                "Gracz do siebie: 'Perfekcyjne. Teraz tylko znaleźć metal...'",
                "",
                "Oddajesz klucze Jenkinsowi:",
                "Jenkins: 'Dzięki! Uratowałeś mi skórę!'",
                "Gracz: 'Nie ma sprawy. Każdy może się pomylić.'",
                "Jenkins: 'Jesteś w porządku jak na więźnia.'",
                "",
                "Później, w celi:",
                "Brutus: 'Widziałem co robiłeś w warsztacie. Mądry ruch.'",
                "Gracz: 'Nie wiem o czym mówisz.'",
                "Brutus: 'Jasne, jasne. Gdy zrobisz kopie, pogadamy o współpracy.'"
            ]
        }
        copy_branch.add_consequence('world_state', {
            'player.has_key_molds': True,
            'guard_keys.returned': True
        })
        copy_branch.add_consequence('relationships', {
            'Jenkins': 40,
            'Brutus': 20
        })
        copy_branch.add_consequence('delayed', {
            96: {
                'description': 'Możliwość wykucia kopii',
                'world_changes': {'forge.keys_available': True},
                'new_quests': ['forge_keys_quest']
            }
        })
        self.add_branch(copy_branch)
        
        # ŚCIEŻKA 6: Wymień klucze na informacje
        information_branch = QuestBranch(
            "trade_for_info",
            "Wymień klucze na cenne informacje"
        )
        information_branch.add_requirement('skill', ('investigation', 4))
        information_branch.dialogue_options = {
            'preview': "Ktoś na pewno da mi coś cennego za te klucze...",
            'resolution': "Wymieniasz klucze na informacje o planowanym transporcie więźniów.",
            'info_trade': [
                "Znajdujesz Kruka - więźnia który wie wszystko o wszystkich.",
                "",
                "Gracz: 'Kruk, mam propozycję.'",
                "Kruk: 'Słucham szamanie. Co masz?'",
                "Gracz: *pokazuje klucze* 'Klucze Jenkinsa. Za właściwą informację są twoje.'",
                "Kruk: *przygląda się* 'Autentyczne... Czego chcesz wiedzieć?'",
                "Gracz: 'Coś co pomoże mi się stąd wydostać. Legalnie.'",
                "Kruk: 'Hmm... Za trzy dni będzie transport. Przenoszą trzech do lżejszego więzienia.'",
                "Gracz: 'Kto decyduje kto jedzie?'",
                "Kruk: 'Naczelnik. Ale można go... przekonać. Szczególnie jeśli ma się haki.'",
                "Gracz: 'Jakie haki?'",
                "Kruk: *bierze klucze* 'Naczelnik ma dług hazardowy. 2000 złotych. U Grubego Eda w mieście.'",
                "Gracz: 'Dzięki Kruk.'",
                "Kruk: 'Nie ma za co. A Jenkins... cóż, sam sobie poradzi.'"
            ]
        }
        information_branch.add_consequence('world_state', {
            'player.knows_transport': True,
            'player.knows_warden_debt': True,
            'raven.has_keys': True
        })
        information_branch.add_consequence('relationships', {
            'Raven': 30,
            'information_network': 20
        })
        information_branch.add_consequence('delayed', {
            72: {
                'description': 'Transport więźniów',
                'world_changes': {'prison.transport_day': True},
                'new_quests': ['prisoner_transport_quest']
            }
        })
        self.add_branch(information_branch)


class HoleInWallQuest(EmergentQuest):
    """Quest: Wykopana dziura w murze - gdy gracza nie ma 2 dni w celi."""
    
    def __init__(self):
        seed = QuestSeed(
            quest_id="hole_in_wall",
            name="Tunel w murze",
            activation_conditions={
                'player.absent_from_cell_days': {'operator': '>=', 'value': 2},
                'prison.security': {'operator': '!=', 'value': 'maximum'}
            },
            discovery_methods=[
                DiscoveryMethod.FOUND,
                DiscoveryMethod.TOLD,
                DiscoveryMethod.ENVIRONMENTAL
            ],
            initial_clues={
                'player_cell': 'Twoja prycza została przesunięta. Za nią widać ślady kopania.',
                'adjacent_cell': 'Z sąsiedniej celi słychać ciche skrobanie.',
                'prison_wall': 'Przy murze leży kupka gruzu przykryta szmatami.'
            },
            time_sensitive=True,
            expiry_hours=36,
            priority=7
        )
        super().__init__("hole_in_wall", seed)
        
        self.discovery_dialogue = {
            'found': [
                "Wracasz do celi i zauważasz że ktoś przy niej majstrował. Za pryczą znajdujesz rozpoczęty tunel!",
                "Potykasz się o luźne kamienie. Ktoś kopie tunel!"
            ],
            'told': [
                "Współwięzień szepcze: 'Ktoś wykorzystał twoją nieobecność. Sprawdź za łóżkiem.'",
                "Brutus: 'Szamanie, ktoś grzebie w twojej celi. Lepiej to sprawdź.'"
            ],
            'environmental': [
                "Mur w twojej celi wygląda inaczej. Jakby ktoś go naruszył.",
                "Czujesz przeciąg którego wcześniej nie było."
            ]
        }
        
        self._create_branches()
        
    def _create_branches(self):
        """Tworzy ścieżki rozwiązania questa tunelu."""
        
        # ŚCIEŻKA 1: Kontynuuj kopanie
        continue_branch = QuestBranch(
            "continue_digging",
            "Kontynuuj kopanie tunelu"
        )
        continue_branch.add_requirement('skill', ('strength', 5))
        continue_branch.add_requirement('skill', ('stealth', 6))
        continue_branch.dialogue_options = {
            'preview': "Ktoś zaczął, ja dokończę...",
            'resolution': "Kontynuujesz kopanie. Po tygodniu tunel jest gotowy, ale musisz zdecydować co dalej.",
            'digging_scenes': [
                "Noc 1:",
                "Kopiesz ostrożnie, używając łyżki i kawałka metalu.",
                "Gruz chowasz w kieszeniach i rozrzucasz na dziedzińcu.",
                "",
                "Noc 3:",
                "Tunel ma już metr. Trafiasz na twardszy kamień.",
                "Współwięzień: 'Słychać hałas. Uważaj.'",
                "Gracz: 'Wiem. Pomożesz mi?'",
                "Współwięzień: 'Za udział w ucieczce? Jasne!'",
                "",
                "Noc 5:",
                "Brutus: 'Wiem co robisz szamanie.'",
                "Gracz: 'I co z tego?'",
                "Brutus: 'Chcę udział. Albo donosę.'",
                "Gracz: 'Dobra. Ale pomagasz kopać.'",
                "",
                "Noc 7:",
                "Tunel przebił się na drugą stronę!",
                "Prowadzi do kanałów pod więzieniem.",
                "Brutus: 'Kiedy uciekamy?'",
                "Gracz: 'Musimy to zaplanować. Jedna szansa.'"
            ]
        }
        continue_branch.add_consequence('world_state', {
            'prison.tunnel_complete': True,
            'prison.escape_route': True
        })
        continue_branch.add_consequence('relationships', {
            'Brutus': 30,
            'fellow_prisoners': 25
        })
        continue_branch.add_consequence('delayed', {
            24: {
                'description': 'Planowanie ucieczki',
                'world_changes': {'prison.escape_planning': True},
                'new_quests': ['great_escape_quest']
            }
        })
        self.add_branch(continue_branch)
        
        # ŚCIEŻKA 2: Zgłoś strażnikom
        report_branch = QuestBranch(
            "report_tunnel",
            "Zgłoś tunel strażnikom"
        )
        report_branch.dialogue_options = {
            'preview': "To zbyt niebezpieczne. Muszę to zgłosić.",
            'resolution': "Zgłaszasz tunel. Strażnicy są wdzięczni, ale więźniowie uważają cię za donosiciela.",
            'report_scene': [
                "Gracz do strażnika: 'Muszę z kimś porozmawiać. To ważne.'",
                "Strażnik: 'Co chcesz więźniu?'",
                "Gracz: 'W mojej celi ktoś kopie tunel.'",
                "Strażnik: *oczy się rozszerzają* 'Co?! Pokaż!'",
                "",
                "[W celi]",
                "Kapitan: 'Dobra robota więźniu. Gdyby nie ty, mielibyśmy masową ucieczkę.'",
                "Gracz: 'Nie chcę kłopotów. Chcę tylko odbyć karę.'",
                "Kapitan: 'Doceniam to. Dostaniesz lepszą celę. I dodatkowe porcje.'",
                "",
                "[Później]",
                "Brutus: 'Donosiciel... Nie spodziewałem się tego po tobie szamanie.'",
                "Gracz: 'To nie była moja dziura.'",
                "Brutus: 'Nieważne. Jesteś skończony wśród nas.'"
            ]
        }
        report_branch.add_consequence('world_state', {
            'prison.tunnel_discovered': True,
            'prison.security': 'high',
            'player.marked_as_snitch': True
        })
        report_branch.add_consequence('relationships', {
            'guards': 40,
            'warden': 30,
            'prisoners': -60,
            'Brutus': -50
        })
        report_branch.add_consequence('delayed', {
            48: {
                'description': 'Próba zemsty więźniów',
                'world_changes': {'player.targeted': True},
                'npc_reactions': {
                    'prisoners': 'Donosiciele nie żyją długo...'
                }
            }
        })
        self.add_branch(report_branch)
        
        # ŚCIEŻKA 3: Zasypać i ukryć
        hide_branch = QuestBranch(
            "hide_tunnel",
            "Zasypać tunel i ukryć ślady"
        )
        hide_branch.add_requirement('skill', ('crafting', 4))
        hide_branch.dialogue_options = {
            'preview': "Muszę to zasypać zanim ktoś zauważy...",
            'resolution': "Zasypujesz tunel i masKujesz ślady. Nikt się nie dowiaduje.",
            'hiding_process': [
                "Pracujesz całą noc zasypując tunel.",
                "Używasz wody i błota żeby spojić kamienie.",
                "",
                "Brutus wchodzi: 'Co tu robisz szamanie?'",
                "Gracz: 'Naprawiam mur. Ktoś tu grzebał.'",
                "Brutus: 'Grzebał? Kto?'",
                "Gracz: 'Nie wiem. Ale nie chcę żeby mnie o to oskarżyli.'",
                "Brutus: 'Mądre. Pomogę ci.'",
                "",
                "[Wspólnie ukrywacie ślady]",
                "Brutus: 'Nigdy tego nie było, jasne?'",
                "Gracz: 'Jakiego tunelu?'",
                "Brutus: 'Dokładnie. Dobry z ciebie kumpel szamanie.'"
            ]
        }
        hide_branch.add_consequence('world_state', {
            'prison.tunnel_hidden': True,
            'prison.security_unchanged': True
        })
        hide_branch.add_consequence('relationships', {
            'Brutus': 20
        })
        hide_branch.add_consequence('delayed', {
            168: {
                'description': 'Ktoś próbuje znowu kopać',
                'world_changes': {'prison.new_tunnel_attempt': True}
            }
        })
        self.add_branch(hide_branch)
        
        # ŚCIEŻKA 4: Zastawić pułapkę
        trap_branch = QuestBranch(
            "set_trap",
            "Zastawić pułapkę na tego kto kopie"
        )
        trap_branch.add_requirement('skill', ('traps', 5))
        trap_branch.add_requirement('item', 'rope_or_wire')
        trap_branch.dialogue_options = {
            'preview': "Złapię gnoja który grzebie w mojej celi...",
            'resolution': "Zastawiasz pułapkę. Łapiesz więźnia który kopał tunel.",
            'trap_scene': [
                "Ustawiasz cienki drut i dzwonek z łyżki.",
                "Przykrywasz tunel tak jakby nic się nie stało.",
                "Czekasz...",
                "",
                "Trzecia noc:",
                "*BRZĘK!*",
                "Łapiesz intruza za gardło.",
                "To Szczur - drobny złodziejaszek.",
                "",
                "Szczur: 'Puść! Puść!'",
                "Gracz: 'Kopałeś w MOJEJ celi?'",
                "Szczur: 'Myślałem że cię przeniesli! Przysięgam!'",
                "Gracz: 'Co planujesz?'",
                "Szczur: 'Ucieczkę! Za tydzień! Możesz się przyłączyć!'",
                "",
                "Opcje:",
                "- Puścić go i przyłączyć się",
                "- Zmusić do pracy na ciebie",
                "- Wydać strażnikom"
            ]
        }
        trap_branch.add_consequence('world_state', {
            'caught_digger': 'Szczur',
            'tunnel_discovered_by_player': True
        })
        trap_branch.add_consequence('relationships', {
            'Szczur': -20
        })
        trap_branch.add_consequence('delayed', {
            1: {
                'description': 'Musisz zdecydować co ze Szczurem',
                'new_quests': ['szczur_decision_quest']
            }
        })
        self.add_branch(trap_branch)
        
        # ŚCIEŻKA 5: Sprzedać informację
        sell_info_branch = QuestBranch(
            "sell_tunnel_info",
            "Sprzedać informację o tunelu"
        )
        sell_info_branch.add_requirement('skill', ('barter', 5))
        sell_info_branch.dialogue_options = {
            'preview': "Ktoś zapłaci dobrze za taką informację...",
            'resolution': "Sprzedajesz informację o tunelu różnym stronom. Chaos wybucha.",
            'selling_info': [
                "Najpierw idziesz do Brutusa:",
                "Gracz: 'Brutus, w mojej celi jest tunel.'",
                "Brutus: 'Co?! Kto go kopie?'",
                "Gracz: 'Nie wiem. Ale za odpowiednią cenę, tunel może być twój.'",
                "Brutus: 'Ile?'",
                "Gracz: 'Ochrona na miesiąc i pół swoich papierosów.'",
                "Brutus: 'Zgoda.'",
                "",
                "Potem do Kruka:",
                "Gracz: 'Kruk, mam informację wartą fortunę.'",
                "Kruk: 'Mów.'",
                "Gracz: 'Tunel. W mojej celi. Ale Brutus o nim wie.'",
                "Kruk: 'Sprzedałeś to dwóm stronom?'",
                "Gracz: 'Biznes to biznes.'",
                "Kruk: 'Będzie wojna. Ale dobrze. Dam ci sztylet za to info.'",
                "",
                "Na koniec do skorumpowanego strażnika:",
                "Gracz: 'Panie Wilson, gdyby pan wiedział o tunelu...'",
                "Wilson: 'Ile chcesz?'",
                "Gracz: '100 złotych.'",
                "Wilson: 'Dostaniesz 50 i nie zabiję cię.'",
                "Gracz: 'Umowa.'"
            ]
        }
        sell_info_branch.add_consequence('world_state', {
            'prison.tunnel_known': True,
            'prison.gang_war_brewing': True,
            'player.gold': 50
        })
        sell_info_branch.add_consequence('relationships', {
            'Brutus': 10,
            'Raven': 5,
            'Wilson': 15,
            'other_prisoners': -30
        })
        sell_info_branch.add_consequence('delayed', {
            12: {
                'description': 'Wojna o tunel',
                'world_changes': {'prison.gang_war': True},
                'new_quests': ['tunnel_war_quest']
            }
        })
        self.add_branch(sell_info_branch)
        
        # ŚCIEŻKA 6: Rozszerzyć tunel
        expand_branch = QuestBranch(
            "expand_tunnel",
            "Przekształcić tunel w sieć przejść"
        )
        expand_branch.add_requirement('skill', ('engineering', 7))
        expand_branch.add_requirement('skill', ('leadership', 6))
        expand_branch.dialogue_options = {
            'preview': "Ten tunel to początek. Mogę stworzyć całą sieć...",
            'resolution': "Organizujesz więźniów do stworzenia sieci tuneli. Więzienie staje się labiryntem.",
            'expansion_project': [
                "Zwołujesz tajne spotkanie:",
                "Gracz: 'Panowie, mamy tunel. Ale to za mało.'",
                "Więzień 1: 'Co proponujesz?'",
                "Gracz: 'Sieć. Tunele łączące cele, magazyny, może nawet wyjście.'",
                "Brutus: 'To szaleństwo! Lata pracy!'",
                "Gracz: 'Albo miesiące, jeśli wszyscy pomogą.'",
                "",
                "Tydzień 1:",
                "20 więźniów kopie na zmianę.",
                "System wywózki gruzu działa perfekcyjnie.",
                "",
                "Tydzień 2:",
                "Pierwsze połączenia między celami gotowe.",
                "Można się przemieszczać niezauważenie.",
                "",
                "Tydzień 3:",
                "Tunel do kuchni ukończony.",
                "Tunel do warsztatu w budowie.",
                "",
                "Tydzień 4:",
                "Strażnicy zauważają że więźniowie są zmęczeni.",
                "Kapitan: 'Coś się dzieje. Czuję to.'",
                "",
                "Gracz do więźniów: 'To dopiero początek naszego królestwa pod ziemią.'"
            ]
        }
        expand_branch.add_consequence('world_state', {
            'prison.tunnel_network': True,
            'prison.underground_kingdom': True,
            'prison.prisoner_morale': 9
        })
        expand_branch.add_consequence('relationships', {
            'prisoners': 50,
            'Brutus': 40
        })
        expand_branch.add_consequence('delayed', {
            720: {  # Miesiąc później
                'description': 'Odkrycie sieci tuneli',
                'world_changes': {'prison.tunnel_discovered': True},
                'new_quests': ['tunnel_network_defense']
            }
        })
        self.add_branch(expand_branch)


# NOTE: PrisonDiseaseQuest przeniesiona do emergent_quests.py (unikanie duplikatu)
# Bogate dialogi z tej klasy mogą być później dodane do emergent_quests.py


class PrisonerRevoltQuest(EmergentQuest):
    """Quest: Bunt więźniów - gdy relacje z Brutusem < -50."""
    
    def __init__(self):
        seed = QuestSeed(
            quest_id="prisoner_revolt",
            name="Bunt w więzieniu",
            activation_conditions={
                'relationships.Brutus': {'operator': '<', 'value': -50},
                'prison.tension': {'operator': '>', 'value': 7}
            },
            discovery_methods=[
                DiscoveryMethod.OVERHEARD,
                DiscoveryMethod.WITNESSED,
                DiscoveryMethod.CONSEQUENCE
            ],
            initial_clues={
                'prison_yard': 'Grupy więźniów szepczą agresywnie. Brutus coś planuje.',
                'cafeteria': 'Napięcie przy posiłkach. Więźniowie gromadzą improwizowaną broń.',
                'cell_block_b': 'Ktoś napisał na ścianie: "JUTRO WOLNOŚĆ LUB ŚMIERĆ"'
            },
            time_sensitive=True,
            expiry_hours=24,
            priority=10
        )
        super().__init__("prisoner_revolt", seed)
        
        self.discovery_dialogue = {
            'overheard': [
                "Słyszysz Brutusa: 'Jutro o świcie. Bierzemy strażników i szamana!'",
                "Dwóch więźniów szepcze: 'Brutus powiedział - albo z nami, albo przeciw nam.'"
            ],
            'witnessed': [
                "Widzisz jak więźniowie ostrzą samoróbki. Brutus kieruje przygotowaniami.",
                "Strażnicy są nerwowi. Czują że coś wisi w powietrzu."
            ],
            'consequence': [
                "Twoje wrogie relacje z Brutusem doprowadziły do tego. Bunt jest nieunikniony.",
                "Brutus wykorzystał twoją słabość. Więźniowie są przeciwko tobie."
            ]
        }
        
        self._create_branches()
        
    def _create_branches(self):
        """Tworzy ścieżki rozwiązania buntu."""
        
        # ŚCIEŻKA 1: Dołącz do buntu
        join_revolt_branch = QuestBranch(
            "join_revolt",
            "Dołącz do buntu mimo wrogości"
        )
        join_revolt_branch.add_requirement('skill', ('persuasion', 8))
        join_revolt_branch.add_requirement('skill', ('combat', 6))
        join_revolt_branch.dialogue_options = {
            'preview': "Może uda się przekonać Brutusa że jestem po jego stronie...",
            'resolution': "Przekonujesz Brutusa i dołączasz do buntu. Razem przejmujecie więzienie.",
            'joining_scene': [
                "Podchodzisz do Brutusa przed buntem:",
                "Gracz: 'Brutus, wiem co planujesz.'",
                "Brutus: *chwyta za nóż* 'Przyszedłeś donieść?'",
                "Gracz: 'Przyszedłem dołączyć.'",
                "Brutus: 'Ha! Ty? Zdrajca?'",
                "Gracz: 'Miałem swoje powody. Ale teraz widzę - tylko razem możemy wygrać.'",
                "Brutus: 'Dlaczego miałbym ci ufać?'",
                "Gracz: 'Bo znam słabe punkty straży. I mogę rzucić zaklęcia bojowe.'",
                "Brutus: *myśli* 'Jeden fałszywy ruch i jesteś martwy.'",
                "Gracz: 'Zgoda.'",
                "",
                "[BUNT]",
                "Świt. Sygnał.",
                "Więźniowie atakują strażników.",
                "Gracz rzuca zaklęcie ogłuszające.",
                "",
                "Brutus: 'Teraz! Na zbrojownię!'",
                "Razem przejmujecie broń.",
                "",
                "Walka z kapitanem straży:",
                "Kapitan: 'Ty! Wiedziałem że jesteś zdrajcą!'",
                "Gracz i Brutus walczą ramię w ramię.",
                "",
                "Po godzinie - więzienie zdobyte.",
                "Brutus: 'Dobrze walczyłeś szamanie. Może się mylę co do ciebie.'",
                "Gracz: 'Teraz co? Jesteśmy panami więzienia.'",
                "Brutus: 'Teraz... negocjujemy naszą wolność.'"
            ]
        }
        join_revolt_branch.add_consequence('world_state', {
            'prison.controlled_by': 'prisoners',
            'prison.guards_captured': True,
            'prison.revolt_successful': True
        })
        join_revolt_branch.add_consequence('relationships', {
            'Brutus': 70,
            'prisoners': 60,
            'guards': -100
        })
        join_revolt_branch.add_consequence('delayed', {
            24: {
                'description': 'Wojsko otacza więzienie',
                'world_changes': {'prison.under_siege': True},
                'new_quests': ['siege_negotiation_quest']
            }
        })
        self.add_branch(join_revolt_branch)
        
        # ŚCIEŻKA 2: Ostrzeż strażników
        warn_guards_branch = QuestBranch(
            "warn_guards",
            "Ostrzeż strażników o buncie"
        )
        warn_guards_branch.dialogue_options = {
            'preview': "Muszę ostrzec straż. Będzie masakra.",
            'resolution': "Ostrzegasz strażników. Bunt jest stłumiony, ale więźniowie cię nienawidzą.",
            'warning_scene': [
                "Biegniesz do kapitana:",
                "Gracz: 'Kapitanie! Brutus planuje bunt! Jutro świt!'",
                "Kapitan: 'Co?! Skąd wiesz?'",
                "Gracz: 'Słyszałem. Mają broń, plan. Musicie być gotowi!'",
                "Kapitan: 'Dobra robota więźniu. Zajmiemy się tym.'",
                "",
                "[Noc]",
                "Strażnicy potajemnie się zbroją.",
                "Dodatkowe oddziały czekają ukryte.",
                "",
                "[Świt]",
                "Brutus: 'ATAK!'",
                "Więźniowie ruszają...",
                "...prosto w pułapkę.",
                "",
                "Strażnicy z tarczami i pałkami.",
                "Gaz łzawiący.",
                "Więźniowie nie mają szans.",
                "",
                "Brutus widzi ciebie przy strażnikach:",
                "Brutus: 'TY! ZDRAJCA! ZABIJĘ CIĘ!'",
                "",
                "Po wszystkim:",
                "Kapitan: 'Uratowałeś życia strażników. Nie zapomnę tego.'",
                "Ale w oczach więźniów jesteś skończony."
            ]
        }
        warn_guards_branch.add_consequence('world_state', {
            'prison.revolt_failed': True,
            'prison.lockdown': True,
            'prison.brutus_in_solitary': True
        })
        warn_guards_branch.add_consequence('relationships', {
            'guards': 70,
            'warden': 50,
            'prisoners': -100,
            'Brutus': -200
        })
        warn_guards_branch.add_consequence('delayed', {
            168: {
                'description': 'Próba zabójstwa przez więźniów',
                'world_changes': {'assassination_attempt': True},
                'new_quests': ['survive_assassination_quest']
            }
        })
        self.add_branch(warn_guards_branch)
        
        # ŚCIEŻKA 3: Przejmij przywództwo buntu
        take_over_branch = QuestBranch(
            "take_over_revolt",
            "Przejmij przywództwo buntu od Brutusa"
        )
        take_over_branch.add_requirement('skill', ('leadership', 8))
        take_over_branch.add_requirement('skill', ('intimidation', 7))
        take_over_branch.dialogue_options = {
            'preview': "Mogę obalić Brutusa i sam poprowadzić bunt...",
            'resolution': "Wyzywasz Brutusa na pojedynek. Wygrywasz i prowadzisz lepszy, mądrzejszy bunt.",
            'takeover_scene': [
                "Stajesz przed zgromadzonymi więźniami:",
                "Gracz: 'Brutus! Wyzywam cię na pojedynek o przywództwo!'",
                "Brutus: 'Co?! Ty gnoju!'",
                "Gracz: 'Prowadzisz nas na rzeź. Ja mam lepszy plan.'",
                "Więźniowie: *szmer*",
                "Brutus: 'Dobra. Tutaj, teraz. Do pierwszej krwi!'",
                "",
                "[POJEDYNEK]",
                "Krąg więźniów.",
                "Brutus atakuje z furią.",
                "Ty używasz szamańskich sztuczek.",
                "",
                "Oślepiasz go proszkiem.",
                "Uderzasz kolanem w brzuch.",
                "Brutus pada.",
                "",
                "Gracz: 'Teraz ja prowadzę. Kto ze mną?'",
                "Więźniowie: 'SZAMAN! SZAMAN!'",
                "",
                "Do Brutusa: 'Możesz być moim zastępcą. Albo wrogiem.'",
                "Brutus: *pluje krwią* 'Zastępcą... na razie.'",
                "",
                "Nowy plan:",
                "Gracz: 'Nie atakujemy. Negocjujemy z pozycji siły.'",
                "Gracz: 'Weźmiemy zakładników, nie zabimy nikogo.'",
                "Gracz: 'Żądamy reform, nie krwi.'",
                "",
                "Bunt przebiega bez ofiar.",
                "Żądania więźniów są wysłuchane."
            ]
        }
        take_over_branch.add_consequence('world_state', {
            'prison.revolt_leader': 'player',
            'prison.peaceful_revolt': True,
            'prison.reforms_promised': True
        })
        take_over_branch.add_consequence('relationships', {
            'prisoners': 80,
            'Brutus': -30,  # Urażona duma
            'guards': -20,
            'warden': 10  # Docenia brak przemocy
        })
        take_over_branch.add_consequence('delayed', {
            72: {
                'description': 'Negocjacje z władzami',
                'world_changes': {'reform_negotiations': True},
                'new_quests': ['prison_reform_quest']
            }
        })
        self.add_branch(take_over_branch)
        
        # ŚCIEŻKA 4: Sabotuj bunt
        sabotage_branch = QuestBranch(
            "sabotage_revolt",
            "Potajemnie sabotuj przygotowania do buntu"
        )
        sabotage_branch.add_requirement('skill', ('stealth', 7))
        sabotage_branch.add_requirement('skill', ('sabotage', 6))
        sabotage_branch.dialogue_options = {
            'preview': "Mogę pokrzyżować ich plany nie ujawniając się...",
            'resolution': "Sabotażujesz broń i plany. Bunt się nie udaje, ale nikt nie wie że to ty.",
            'sabotage_actions': [
                "Noc przed buntem:",
                "",
                "1. Psująasz samoróbki:",
                "Wyginasz ostrza, poluzowujesz rękojeści.",
                "",
                "2. Zmienisz ukryte sygnały:",
                "Przestawiasz znaki które mają dać sygnał.",
                "",
                "3. Trujesz zapasy buntowników:",
                "Środek przeczyszczający w ich specjalnych racjach.",
                "",
                "4. Blokujesz kluczowe przejścia:",
                "Zastawiasz meble tak by utrudnić ruch.",
                "",
                "[RANEK BUNTU]",
                "Brutus daje sygnał... ale połowa więźniów ma biegunkę.",
                "Broń się łamie przy pierwszym użyciu.",
                "Więźniowie mylą sygnały, atakują w złym czasie.",
                "",
                "Brutus: 'Co się dzieje?! Zdrada!'",
                "",
                "Strażnicy łatwo tłumią chaotyczny bunt.",
                "",
                "Później:",
                "Brutus: 'Ktoś nas wydał! Znajdę gnoja!'",
                "Ty udajesz zaskoczenie: 'Niemożliwe! Kto mógł?'",
                "",
                "Nikt nie podejrzewa cichego szamana."
            ]
        }
        sabotage_branch.add_consequence('world_state', {
            'prison.revolt_failed': True,
            'prison.saboteur_unknown': True,
            'prison.paranoia': 8
        })
        sabotage_branch.add_consequence('relationships', {
            'Brutus': -60,  # Wściekły na zdrajcę
            'prisoners': -30,  # Rozczarowani
            'guards': 0  # Nie wiedzą o twojej roli
        })
        sabotage_branch.add_consequence('delayed', {
            96: {
                'description': 'Brutus rozpoczyna śledztwo',
                'world_changes': {'brutus_investigation': True},
                'npc_reactions': {
                    'Brutus': 'Znajdę zdrajcę. I wtedy...'
                }
            }
        })
        self.add_branch(sabotage_branch)
        
        # ŚCIEŻKA 5: Wywołaj większy chaos
        escalate_branch = QuestBranch(
            "escalate_chaos",
            "Przekształć bunt w totalny chaos"
        )
        escalate_branch.add_requirement('skill', ('chaos_magic', 6))
        escalate_branch.add_requirement('skill', ('deception', 7))
        escalate_branch.dialogue_options = {
            'preview': "Niech wszyscy walczą ze wszystkimi...",
            'resolution': "Podżegasz wszystkie strony. Więzienie pogrąża się w totalnym chaosie.",
            'chaos_escalation': [
                "Przygotowania:",
                "",
                "Do strażników: 'Brutus planuje spalić więzienie!'",
                "Do Brutusa: 'Strażnicy sprowadzili wojsko!'",
                "Do neutralnych: 'Musicie się bronić przed obiema stronami!'",
                "",
                "Podkładasz ogień w magazynie.",
                "Otwierasz cele szaleńców.",
                "Rzucasz zaklęcie szału bojowego.",
                "",
                "[BUNT ZACZYNA SIĘ]",
                "Brutus atakuje.",
                "Strażnicy kontratakują.",
                "Ogień się rozprzestrzenia.",
                "Szaleńcy atakują wszystkich.",
                "",
                "Krzyki, dym, panika.",
                "",
                "Naczelnik: 'Ewakuacja! Ratujcie się!'",
                "Brutus: 'To pułapka! Zabijać wszystkich!'",
                "",
                "W chaosie, wykradasz się:",
                "Gracz otwiera główną bramę.",
                "Więźniowie uciekają we wszystkie strony.",
                "",
                "Ty spokojnie wychodzisz.",
                "Za tobą płonące więzienie.",
                "",
                "Wolność... ale za jaką cenę?"
            ]
        }
        escalate_branch.add_consequence('world_state', {
            'prison.destroyed': True,
            'prison.mass_escape': True,
            'player.escaped': True,
            'death_toll': 47
        })
        escalate_branch.add_consequence('relationships', {
            'everyone': -100,  # Wszyscy cię nienawidzą
            'chaos_gods': 50  # Ale duchy chaosu są zadowolone
        })
        escalate_branch.add_consequence('delayed', {
            720: {  # Miesiąc później
                'description': 'Łowcy nagród szukają ciebie',
                'world_changes': {'bounty_on_player': 10000},
                'new_quests': ['fugitive_life_quest']
            }
        })
        self.add_branch(escalate_branch)
        
        # ŚCIEŻKA 6: Mediacja pokojowa
        mediate_branch = QuestBranch(
            "mediate_peace",
            "Spróbuj mediacji między stronami"
        )
        mediate_branch.add_requirement('skill', ('diplomacy', 9))
        mediate_branch.add_requirement('skill', ('empathy', 7))
        mediate_branch.dialogue_options = {
            'preview': "Może uda się zapobiec rozlewowi krwi...",
            'resolution': "Organizujesz negocjacje. Znajdujesz kompromis który ratuje życia.",
            'mediation_process': [
                "Gracz do Brutusa: 'Daj mi godzinę przed buntem.'",
                "Brutus: 'Po co?'",
                "Gracz: 'Spróbuję wynegocjować wasze żądania.'",
                "Brutus: 'Masz godzinę. Potem atakujemy.'",
                "",
                "Do naczelnika:",
                "Gracz: 'Wie pan co się szykuje?'",
                "Naczelnik: 'Domyślam się.'",
                "Gracz: 'Mogę to zatrzymać. Ale musi pan ustąpić.'",
                "Naczelnik: 'Czego chcą?'",
                "Gracz: 'Lepsze jedzenie, dłuższe spacery, listy raz w tygodniu.'",
                "Naczelnik: 'To dużo...'",
                "Gracz: 'Mniej niż odbudowa więzienia po buncie.'",
                "",
                "Negocjacje trwają.",
                "W końcu:",
                "",
                "Naczelnik: 'Zgoda na jedzenie i listy. Spacery co drugi dzień.'",
                "Gracz: 'Przyjmę to.'",
                "",
                "Do Brutusa:",
                "Gracz: 'Mam umowę. Nie wszystko, ale dużo.'",
                "Brutus: 'Bez walki?'",
                "Gracz: 'Bez śmierci. Pomyśl o swoich ludziach.'",
                "Brutus: '...Dobra. Ale jeśli nie dotrzymają słowa...'",
                "Gracz: 'Dotrzymają. Daję słowo szamana.'",
                "",
                "Buntu nie ma.",
                "Reformy są wprowadzone.",
                "Ty zyskujesz szacunek obu stron."
            ]
        }
        mediate_branch.add_consequence('world_state', {
            'prison.reforms_implemented': True,
            'prison.tension': 3,
            'prison.revolt_prevented': True
        })
        mediate_branch.add_consequence('relationships', {
            'Brutus': 40,
            'prisoners': 50,
            'guards': 40,
            'warden': 60
        })
        mediate_branch.add_consequence('delayed', {
            240: {  # 10 dni
                'description': 'Propozycja wcześniejszego zwolnienia',
                'world_changes': {'early_release_possible': True},
                'npc_reactions': {
                    'warden': 'Za twoją pomoc, możemy skrócić wyrok...'
                },
                'new_quests': ['early_release_quest']
            }
        })
        self.add_branch(mediate_branch)


# Eksportuj klasy questów
__all__ = [
    'PrisonFoodConflictQuest',
    'GuardKeysLostQuest',
    'HoleInWallQuest',
    'PrisonerRevoltQuest'
]