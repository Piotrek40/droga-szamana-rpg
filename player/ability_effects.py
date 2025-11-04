"""
System efektów zdolności klasowych.
Każda zdolność ma swoją funkcję wykonującą efekt.
"""

from typing import Dict, Any, Optional, Tuple
import random
from enum import Enum

from mechanics.combat import DamageType, BodyPart


class BuffType(Enum):
    """Typy buffów/debuffów."""
    DAMAGE_BOOST = "damage_boost"
    DEFENSE_BOOST = "defense_boost"
    SPEED_BOOST = "speed_boost"
    INVISIBLE = "invisible"
    PAIN_IMMUNITY = "pain_immunity"
    MANA_SHIELD = "mana_shield"
    BERSERK = "berserk"
    LAST_STAND = "last_stand"


class AbilityEffects:
    """Klasa zawierająca wszystkie efekty zdolności."""
    
    # ==================== WOJOWNIK ====================
    
    @staticmethod
    def berserk(character, target=None) -> Tuple[bool, str, Dict]:
        """
        Szał Bitewny - Wojownik
        +50% obrażeń, -25% obrony na 3 tury.
        """
        if character.stamina < 30:
            return False, "Brak staminy!", {}
        
        character.stamina -= 30
        
        # Dodaj buff
        if not hasattr(character, 'active_buffs'):
            character.active_buffs = {}
        
        character.active_buffs[BuffType.BERSERK] = {
            'duration': 3,
            'damage_multiplier': 1.5,
            'defense_multiplier': 0.75,
            'description': 'Szał Bitewny'
        }
        
        # Zwiększ siłę ataku natychmiast
        if hasattr(character, 'combat_stats'):
            character.combat_stats.damage_multiplier *= 1.5
            character.combat_stats.defense_multiplier *= 0.75
        
        return True, "Wpadasz w kontrolowany szał bitewny! Twoje oczy płoną dziką furią!", {
            'visual_effect': 'red_aura',
            'sound': 'war_cry'
        }
    
    @staticmethod
    def tarcza_woli(character, target=None) -> Tuple[bool, str, Dict]:
        """
        Tarcza Woli - Wojownik
        Ignorowanie bólu przez 2 tury.
        """
        if character.stamina < 20:
            return False, "Brak staminy!", {}
        
        character.stamina -= 20
        
        if not hasattr(character, 'active_buffs'):
            character.active_buffs = {}
        
        character.active_buffs[BuffType.PAIN_IMMUNITY] = {
            'duration': 2,
            'old_pain': character.pain if hasattr(character, 'pain') else 0,
            'description': 'Tarcza Woli'
        }
        
        # Zresetuj ból
        if hasattr(character, 'pain'):
            character.pain = 0
        if hasattr(character, 'combat_stats'):
            character.combat_stats.pain = 0
        
        return True, "Twoja wola staje się niezłomna! Ból nie ma nad tobą władzy!", {
            'visual_effect': 'golden_shield',
            'sound': 'mental_fortitude'
        }
    
    @staticmethod
    def ostatni_bastion(character, target=None) -> Tuple[bool, str, Dict]:
        """
        Ostatni Bastion - Wojownik (Pasywna)
        Aktywuje się automatycznie przy niskim HP.
        """
        # Ta zdolność jest pasywna i aktywuje się automatycznie
        if hasattr(character, 'health') and character.health < character.max_health * 0.2:
            if not hasattr(character, 'active_buffs'):
                character.active_buffs = {}
            
            if BuffType.LAST_STAND not in character.active_buffs:
                character.active_buffs[BuffType.LAST_STAND] = {
                    'duration': -1,  # Trwa do końca walki
                    'defense_boost': 2.0,
                    'stun_immunity': True,
                    'description': 'Ostatni Bastion'
                }
                
                if hasattr(character, 'combat_stats'):
                    character.combat_stats.defense_multiplier *= 2.0
                
                return True, "Ostatni Bastion się aktywuje! Stajesz się niezniszczalny!", {
                    'visual_effect': 'iron_fortress'
                }
        
        return False, "", {}
    
    # ==================== ŁOTRZYK ====================
    
    @staticmethod
    def niewidzialnosc(character, target=None) -> Tuple[bool, str, Dict]:
        """
        Płaszcz Cieni - Łotrzyk
        75% szans na unik przez 2 tury.
        """
        if character.stamina < 25:
            return False, "Brak staminy!", {}
        
        character.stamina -= 25
        
        if not hasattr(character, 'active_buffs'):
            character.active_buffs = {}
        
        character.active_buffs[BuffType.INVISIBLE] = {
            'duration': 2,
            'dodge_chance': 0.75,
            'description': 'Płaszcz Cieni'
        }
        
        return True, "Znikasz w cieniach! Jesteś prawie niewidzialny!", {
            'visual_effect': 'shadow_form',
            'sound': 'stealth'
        }
    
    @staticmethod
    def cios_w_plecy(character, target) -> Tuple[bool, str, Dict]:
        """
        Sztylet w Mroku - Łotrzyk
        Potrójne obrażenia jeśli cel nie widzi atakującego.
        """
        if character.stamina < 15:
            return False, "Brak staminy!", {}
        
        if not target:
            return False, "Brak celu!", {}
        
        character.stamina -= 15
        
        # Sprawdź czy jesteśmy niewidzialni lub cel jest oszołomiony
        is_hidden = False
        if hasattr(character, 'active_buffs'):
            is_hidden = BuffType.INVISIBLE in character.active_buffs
        
        is_target_stunned = False
        if hasattr(target, 'combat_stats'):
            is_target_stunned = target.combat_stats.is_stunned
        
        damage_multiplier = 3.0 if (is_hidden or is_target_stunned) else 1.5
        
        # Oblicz obrażenia
        base_damage = 15
        if hasattr(character, 'strength'):
            base_damage += character.strength
        
        final_damage = base_damage * damage_multiplier
        
        # Zadaj obrażenia
        if hasattr(target, 'take_damage'):
            # 50% na krwawienie
            injury = None
            if random.random() < 0.5:
                from mechanics.combat import Injury
                injury = Injury(
                    body_part=BodyPart.TULOW,
                    severity=30,
                    damage_type=DamageType.KLUTE,
                    bleeding=True,
                    bleeding_rate=2.0,
                    time_to_heal=1440
                )
            
            effect = target.take_damage(final_damage, BodyPart.TULOW, DamageType.KLUTE, injury)
            
            if damage_multiplier == 3.0:
                return True, f"Perfekcyjny cios w plecy! {effect}", {
                    'damage': final_damage,
                    'critical': True
                }
            else:
                return True, f"Szybki cios sztyletem! {effect}", {
                    'damage': final_damage
                }
        
        return False, "Nie udało się wykonać ataku!", {}
    
    # ==================== ŁOWCA ====================
    
    @staticmethod
    def celny_strzal(character, target) -> Tuple[bool, str, Dict]:
        """
        Oko Sokoła - Łowca
        Ignoruje pancerz, +100% obrażeń.
        """
        if character.stamina < 20:
            return False, "Brak staminy!", {}
        
        if not target:
            return False, "Brak celu!", {}
        
        character.stamina -= 20
        
        # Oblicz obrażenia (podwójne)
        base_damage = 20
        if hasattr(character, 'agility'):
            base_damage += character.agility * 1.5
        
        final_damage = base_damage * 2.0
        
        # Zadaj obrażenia ignorując pancerz
        if hasattr(target, 'combat_stats'):
            target.combat_stats.health -= final_damage
            
            # Szansa na trafienie w oko/głowę
            if random.random() < 0.3:
                if hasattr(target, 'combat_stats'):
                    target.combat_stats.is_stunned = True
                    target.combat_stats.stun_duration = 2
                
                return True, f"Perfekcyjny strzał w głowę! Zadano {final_damage:.1f} obrażeń! Cel oszołomiony!", {
                    'damage': final_damage,
                    'headshot': True
                }
            
            return True, f"Celny strzał! Zadano {final_damage:.1f} obrażeń ignorując pancerz!", {
                'damage': final_damage,
                'armor_pierce': True
            }
        
        return False, "Strzał chybił!", {}
    
    @staticmethod
    def pulapka(character, target) -> Tuple[bool, str, Dict]:
        """
        Sidła Myśliwego - Łowca
        60% szans na unieruchomienie na 2 tury.
        """
        if character.stamina < 15:
            return False, "Brak staminy!", {}
        
        if not target:
            return False, "Brak celu!", {}
        
        character.stamina -= 15
        
        # 60% szans na sukces
        if random.random() < 0.6:
            if hasattr(target, 'combat_stats'):
                # Unieruchomienie = bardzo wysoka kara do szybkości
                target.combat_stats.attack_speed *= 0.1
                
                if not hasattr(target, 'active_debuffs'):
                    target.active_debuffs = {}
                
                target.active_debuffs['trapped'] = {
                    'duration': 2,
                    'speed_penalty': 0.9,
                    'description': 'Uwięziony w pułapce'
                }
                
                return True, f"Pułapka zadziałała! {target.name if hasattr(target, 'name') else 'Przeciwnik'} jest unieruchomiony!", {
                    'trapped': True,
                    'duration': 2
                }
        
        return True, "Przeciwnik uniknął pułapki!", {'trapped': False}
    
    # ==================== RZEMIEŚLNIK ====================
    
    @staticmethod
    def naprawa_w_walce(character, target=None) -> Tuple[bool, str, Dict]:
        """
        Błyskawiczna Naprawa - Rzemieślnik
        Naprawia broń/pancerz w trakcie walki.
        """
        if character.stamina < 15:
            return False, "Brak staminy!", {}
        
        character.stamina -= 15
        
        repaired_items = []
        
        # Napraw broń
        if hasattr(character, 'equipment') and character.equipment.weapon:
            if character.equipment.weapon.get('condition', 100) < 100:
                character.equipment.weapon['condition'] = min(100, 
                    character.equipment.weapon.get('condition', 100) + 50)
                repaired_items.append("broń")
        
        # Napraw pancerz
        if hasattr(character, 'equipment') and character.equipment.armor:
            for slot, armor in character.equipment.armor.items():
                if armor and armor.get('condition', 100) < 100:
                    armor['condition'] = min(100, armor.get('condition', 100) + 50)
                    repaired_items.append(f"pancerz ({slot})")
        
        if repaired_items:
            return True, f"Błyskawicznie naprawiasz: {', '.join(repaired_items)}!", {
                'repaired': repaired_items
            }
        else:
            return True, "Twój ekwipunek jest w dobrym stanie.", {}
    
    @staticmethod
    def bomba_alchemiczna(character, target) -> Tuple[bool, str, Dict]:
        """
        Ładunek Wybuchowy - Rzemieślnik
        Obrażenia obszarowe.
        """
        if character.stamina < 10:
            return False, "Brak staminy!", {}
        
        character.stamina -= 10
        
        # Obrażenia bazowe
        base_damage = 25
        if hasattr(character, 'intelligence'):
            base_damage += character.intelligence * 2
        
        # Zadaj obrażenia celowi główne
        victims = []
        if target and hasattr(target, 'take_damage'):
            effect = target.take_damage(base_damage, BodyPart.TULOW, DamageType.OPARZENIE)
            victims.append(f"{target.name if hasattr(target, 'name') else 'cel główny'} ({base_damage:.0f} dmg)")
        
        # Note: Obrażenia obszarowe dla innych wrogów w pobliżu
        
        return True, f"BOOM! Bomba eksploduje! Trafieni: {', '.join(victims) if victims else 'nikt'}", {
            'damage': base_damage,
            'aoe': True,
            'visual_effect': 'explosion'
        }
    
    # ==================== MAG ====================
    
    @staticmethod
    def pocisk_mocy(character, target) -> Tuple[bool, str, Dict]:
        """
        Kula Ognia - Mag
        Obrażenia magiczne ignorujące pancerz.
        """
        if not hasattr(character, 'mana') or character.mana < 10:
            return False, "Brak many!", {}
        
        if character.stamina < 5:
            return False, "Brak staminy!", {}
        
        if not target:
            return False, "Brak celu!", {}
        
        character.mana -= 10
        character.stamina -= 5
        
        # Obrażenia magiczne
        base_damage = 15
        if hasattr(character, 'intelligence'):
            base_damage += character.intelligence * 2
        
        # Bonus z mocy zaklęć
        if hasattr(character, 'character_class'):
            spell_power = character.character_class.special_mechanics.get('spell_power', 1.0)
            base_damage *= spell_power
        
        # Zadaj obrażenia (ignorują pancerz)
        if hasattr(target, 'combat_stats'):
            target.combat_stats.health -= base_damage
            
            # Efekt podpalenia (mała szansa)
            burn_msg = ""
            if random.random() < 0.2:
                if not hasattr(target, 'active_debuffs'):
                    target.active_debuffs = {}
                target.active_debuffs['burning'] = {
                    'duration': 3,
                    'damage_per_turn': 5,
                    'description': 'Podpalenie'
                }
                burn_msg = " Cel się pali!"
            
            return True, f"Kula ognia trafia w cel! Zadano {base_damage:.1f} obrażeń magicznych!{burn_msg}", {
                'damage': base_damage,
                'damage_type': 'magic',
                'burning': burn_msg != ""
            }
        
        return False, "Zaklęcie chybiło!", {}
    
    @staticmethod
    def tarcza_many(character, target=None) -> Tuple[bool, str, Dict]:
        """
        Bariera Arkanów - Mag
        Pochłania 50% obrażeń przez 3 tury.
        """
        if not hasattr(character, 'mana') or character.mana < 20:
            return False, "Brak many!", {}
        
        if character.stamina < 10:
            return False, "Brak staminy!", {}
        
        character.mana -= 20
        character.stamina -= 10
        
        if not hasattr(character, 'active_buffs'):
            character.active_buffs = {}
        
        character.active_buffs[BuffType.MANA_SHIELD] = {
            'duration': 3,
            'damage_reduction': 0.5,
            'description': 'Bariera Arkanów',
            'shield_hp': 50  # Dodatkowe HP tarczy
        }
        
        return True, "Otacza cię świetlista bariera magicznej energii!", {
            'visual_effect': 'mana_shield',
            'sound': 'arcane_barrier'
        }
    
    @staticmethod
    def teleportacja(character, target=None) -> Tuple[bool, str, Dict]:
        """
        Przeskok Przestrzeni - Mag
        Teleportacja dająca przewagę taktyczną.
        """
        if not hasattr(character, 'mana') or character.mana < 25:
            return False, "Brak many!", {}
        
        if character.stamina < 15:
            return False, "Brak staminy!", {}
        
        character.mana -= 25
        character.stamina -= 15
        
        # Unik następnego ataku
        if not hasattr(character, 'active_buffs'):
            character.active_buffs = {}
        
        character.active_buffs['phased'] = {
            'duration': 1,
            'dodge_chance': 1.0,  # 100% unik na 1 turę
            'description': 'Przesunięcie Fazowe'
        }
        
        # Jeśli teleportujemy się za wroga, dostajemy bonus do następnego ataku
        if target:
            character.active_buffs['flanking'] = {
                'duration': 1,
                'damage_multiplier': 1.5,
                'description': 'Atak z flanki'
            }
            
            return True, f"Teleportujesz się za {target.name if hasattr(target, 'name') else 'przeciwnika'}! Masz przewagę!", {
                'visual_effect': 'teleport',
                'sound': 'blink',
                'tactical_advantage': True
            }
        
        return True, "Teleportujesz się w bezpieczne miejsce!", {
            'visual_effect': 'teleport',
            'sound': 'blink'
        }
    
    @staticmethod
    def meditacja(character, target=None) -> Tuple[bool, str, Dict]:
        """
        Medytacja Mocy - Mag
        Regeneracja many, ale brak ruchu.
        """
        if hasattr(character, 'active_buffs') and 'meditating' in character.active_buffs:
            return False, "Już medytujesz!", {}
        
        if not hasattr(character, 'active_buffs'):
            character.active_buffs = {}
        
        character.active_buffs['meditating'] = {
            'duration': 3,
            'mana_regen': 0.3,  # 30% many na turę
            'immobilized': True,
            'description': 'Medytacja'
        }
        
        return True, "Zaczynasz medytować. Energia magiczna przepływa przez ciebie...", {
            'visual_effect': 'meditation',
            'sound': 'chanting'
        }


# Słownik mapujący nazwy zdolności na funkcje
ABILITY_FUNCTIONS = {
    # Wojownik
    "berserk": AbilityEffects.berserk,
    "tarcza_woli": AbilityEffects.tarcza_woli,
    "ostatni_bastion": AbilityEffects.ostatni_bastion,
    
    # Łotrzyk
    "niewidzialnosc": AbilityEffects.niewidzialnosc,
    "cios_w_plecy": AbilityEffects.cios_w_plecy,
    
    # Łowca
    "celny_strzal": AbilityEffects.celny_strzal,
    "pulapka": AbilityEffects.pulapka,
    
    # Rzemieślnik
    "naprawa_w_walce": AbilityEffects.naprawa_w_walce,
    "bomba_alchemiczna": AbilityEffects.bomba_alchemiczna,
    
    # Mag
    "pocisk_mocy": AbilityEffects.pocisk_mocy,
    "tarcza_many": AbilityEffects.tarcza_many,
    "teleportacja": AbilityEffects.teleportacja,
    "meditacja": AbilityEffects.meditacja
}


def execute_ability(ability_name: str, character, target=None) -> Tuple[bool, str, Dict]:
    """
    Wykonuje zdolność.
    
    Args:
        ability_name: Nazwa zdolności
        character: Postać używająca
        target: Opcjonalny cel
    
    Returns:
        (sukces, opis, dodatkowe_dane)
    """
    if ability_name in ABILITY_FUNCTIONS:
        return ABILITY_FUNCTIONS[ability_name](character, target)
    
    return False, f"Nieznana zdolność: {ability_name}", {}