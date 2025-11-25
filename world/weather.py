"""
System pogody dla gry Droga Szamana RPG.
Zarządza warunkami atmosferycznymi wpływającymi na grę.
"""

import random
from enum import Enum
from typing import Dict, List, Tuple, Any


class WeatherType(Enum):
    """Typy pogody."""
    CLEAR = "czyste_niebo"
    CLOUDY = "pochmurno"
    RAIN = "deszcz"
    STORM = "burza"
    FOG = "mgła"
    SNOW = "śnieg"
    DRIZZLE = "mżawka"


class WindStrength(Enum):
    """Siła wiatru."""
    CALM = "cisza"
    LIGHT = "lekki"
    MODERATE = "umiarkowany"
    STRONG = "silny"
    GALE = "wichura"


class WeatherSystem:
    """System zarządzania pogodą w grze."""
    
    def __init__(self, initial_weather: WeatherType = WeatherType.CLEAR):
        """Inicjalizacja systemu pogody."""
        self.current_weather = initial_weather
        self.temperature = 15  # Stopnie Celsjusza
        self.humidity = 50  # Procent
        self.wind_strength = WindStrength.LIGHT
        self.wind_direction = "północny"
        
        # Czas trwania aktualnej pogody (w minutach gry)
        self.weather_duration = random.randint(60, 240)
        self.time_elapsed = 0
        
        # Prawdopodobieństwa przejść między typami pogody
        self.weather_transitions = {
            WeatherType.CLEAR: {
                WeatherType.CLEAR: 0.5,
                WeatherType.CLOUDY: 0.3,
                WeatherType.FOG: 0.1,
                WeatherType.DRIZZLE: 0.1
            },
            WeatherType.CLOUDY: {
                WeatherType.CLEAR: 0.2,
                WeatherType.CLOUDY: 0.4,
                WeatherType.RAIN: 0.2,
                WeatherType.DRIZZLE: 0.1,
                WeatherType.STORM: 0.1
            },
            WeatherType.RAIN: {
                WeatherType.CLOUDY: 0.3,
                WeatherType.RAIN: 0.4,
                WeatherType.STORM: 0.2,
                WeatherType.DRIZZLE: 0.1
            },
            WeatherType.STORM: {
                WeatherType.RAIN: 0.5,
                WeatherType.STORM: 0.3,
                WeatherType.CLOUDY: 0.2
            },
            WeatherType.FOG: {
                WeatherType.FOG: 0.4,
                WeatherType.CLOUDY: 0.3,
                WeatherType.CLEAR: 0.2,
                WeatherType.DRIZZLE: 0.1
            },
            WeatherType.SNOW: {
                WeatherType.SNOW: 0.5,
                WeatherType.CLOUDY: 0.3,
                WeatherType.CLEAR: 0.2
            },
            WeatherType.DRIZZLE: {
                WeatherType.DRIZZLE: 0.3,
                WeatherType.CLOUDY: 0.3,
                WeatherType.RAIN: 0.2,
                WeatherType.FOG: 0.1,
                WeatherType.CLEAR: 0.1
            }
        }
        
        # Wpływ pogody na parametry
        self.weather_effects = {
            WeatherType.CLEAR: {
                'visibility': 1.0,
                'movement_speed': 1.0,
                'mood': 0.1
            },
            WeatherType.CLOUDY: {
                'visibility': 0.9,
                'movement_speed': 1.0,
                'mood': 0.0
            },
            WeatherType.RAIN: {
                'visibility': 0.7,
                'movement_speed': 0.9,
                'mood': -0.1
            },
            WeatherType.STORM: {
                'visibility': 0.5,
                'movement_speed': 0.7,
                'mood': -0.2
            },
            WeatherType.FOG: {
                'visibility': 0.3,
                'movement_speed': 0.8,
                'mood': -0.05
            },
            WeatherType.SNOW: {
                'visibility': 0.6,
                'movement_speed': 0.8,
                'mood': 0.05
            },
            WeatherType.DRIZZLE: {
                'visibility': 0.8,
                'movement_speed': 0.95,
                'mood': -0.05
            }
        }
    
    def update(self, minutes: int = 1):
        """Aktualizuje pogodę po upływie czasu."""
        self.time_elapsed += minutes
        
        # Sprawdź czy czas zmienić pogodę
        if self.time_elapsed >= self.weather_duration:
            self.change_weather()
            self.time_elapsed = 0
            self.weather_duration = random.randint(60, 240)
        
        # Aktualizuj parametry pogodowe
        self._update_temperature()
        self._update_wind()
        self._update_humidity()
    
    def change_weather(self):
        """Zmienia pogodę na podstawie prawdopodobieństw."""
        transitions = self.weather_transitions.get(self.current_weather, {})
        
        if not transitions:
            return
        
        # Wybierz nową pogodę na podstawie prawdopodobieństw
        weather_types = list(transitions.keys())
        probabilities = list(transitions.values())
        
        # Normalizuj prawdopodobieństwa
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p / total_prob for p in probabilities]
        
        # Wybierz losowo z wagami
        self.current_weather = random.choices(weather_types, weights=probabilities)[0]
    
    def _update_temperature(self):
        """Aktualizuje temperaturę na podstawie pogody."""
        base_change = random.uniform(-1, 1)
        
        # Modyfikacje na podstawie pogody
        if self.current_weather == WeatherType.CLEAR:
            base_change += 0.5
        elif self.current_weather in [WeatherType.RAIN, WeatherType.STORM]:
            base_change -= 0.5
        elif self.current_weather == WeatherType.SNOW:
            base_change -= 1.0
            self.temperature = min(self.temperature, 0)  # Śnieg tylko poniżej 0°C
        
        self.temperature += base_change
        self.temperature = max(-20, min(35, self.temperature))  # Ograniczenia
    
    def _update_wind(self):
        """Aktualizuje wiatr."""
        # Kierunek wiatru
        if random.random() < 0.1:  # 10% szans na zmianę kierunku
            directions = ["północny", "południowy", "wschodni", "zachodni",
                         "północno-wschodni", "północno-zachodni",
                         "południowo-wschodni", "południowo-zachodni"]
            self.wind_direction = random.choice(directions)
        
        # Siła wiatru zależna od pogody
        if self.current_weather == WeatherType.STORM:
            self.wind_strength = random.choice([WindStrength.STRONG, WindStrength.GALE])
        elif self.current_weather == WeatherType.RAIN:
            self.wind_strength = random.choice([WindStrength.MODERATE, WindStrength.STRONG])
        elif self.current_weather == WeatherType.CLEAR:
            self.wind_strength = random.choice([WindStrength.CALM, WindStrength.LIGHT])
        else:
            self.wind_strength = random.choice(list(WindStrength))
    
    def _update_humidity(self):
        """Aktualizuje wilgotność."""
        base_change = random.uniform(-5, 5)
        
        # Modyfikacje na podstawie pogody
        if self.current_weather in [WeatherType.RAIN, WeatherType.STORM, WeatherType.DRIZZLE]:
            self.humidity += 10
        elif self.current_weather == WeatherType.FOG:
            self.humidity = max(80, self.humidity)
        elif self.current_weather == WeatherType.CLEAR:
            self.humidity -= 5
        
        self.humidity += base_change
        self.humidity = max(20, min(100, self.humidity))
    
    def get_weather_description(self) -> str:
        """Zwraca opisowy tekst aktualnej pogody."""
        descriptions = {
            WeatherType.CLEAR: [
                "Niebo jest czyste, bez jednej chmurki.",
                "Słońce świeci jasno na bezchmurnym niebie.",
                "Pogoda jest piękna, niebo błękitne i czyste."
            ],
            WeatherType.CLOUDY: [
                "Ciężkie chmury wiszą nisko nad ziemią.",
                "Niebo jest zasnute szarymi chmurami.",
                "Pochmurne niebo sprawia, że świat wydaje się przytłumiony."
            ],
            WeatherType.RAIN: [
                "Deszcz bębni o wszystko wokół.",
                "Krople deszczu spadają z ołowianego nieba.",
                "Ulewny deszcz przemacza wszystko na swojej drodze."
            ],
            WeatherType.STORM: [
                "Burza szaleje z pełną mocą, błyskawice rozdzierają niebo.",
                "Grzmoty przetaczają się po niebie, a deszcz leje jak z cebra.",
                "Potężna burza sprawia, że powietrze jest naelektryzowane."
            ],
            WeatherType.FOG: [
                "Gęsta mgła ogranicza widoczność do kilku metrów.",
                "Świat jest spowity mleczną mgłą.",
                "Mgła kładzie się ciężkim całunem na wszystkim."
            ],
            WeatherType.SNOW: [
                "Śnieg pada spokojnie, pokrywając wszystko białym puchem.",
                "Płatki śniegu wirują w powietrzu.",
                "Zimowy krajobraz jest pokryty świeżym śniegiem."
            ],
            WeatherType.DRIZZLE: [
                "Delikatna mżawka zwilża powietrze.",
                "Drobny deszczyk spowija wszystko wilgocią.",
                "Mżawka tworzy cienką zasłonę wody w powietrzu."
            ]
        }
        
        weather_descs = descriptions.get(self.current_weather, ["Pogoda jest dziwna."])
        return random.choice(weather_descs)
    
    def get_wind_description(self) -> str:
        """Zwraca opis wiatru."""
        wind_descs = {
            WindStrength.CALM: "Powietrze jest całkowicie nieruchome.",
            WindStrength.LIGHT: f"Lekki {self.wind_direction} wiatr delikatnie porusza powietrzem.",
            WindStrength.MODERATE: f"Umiarkowany {self.wind_direction} wiatr wieje równomiernie.",
            WindStrength.STRONG: f"Silny {self.wind_direction} wiatr gnie drzewa i utrudnia poruszanie.",
            WindStrength.GALE: f"Wichura z kierunku {self.wind_direction[:-1]}ego wyrywa wszystko z korzeniami!"
        }
        
        return wind_descs.get(self.wind_strength, "Wiatr wieje.")
    
    def get_temperature_description(self) -> str:
        """Zwraca opis temperatury."""
        if self.temperature < -10:
            return "Jest mroźno, oddech zamarza w powietrzu."
        elif self.temperature < 0:
            return "Jest zimno, trzeba się ciepło ubrać."
        elif self.temperature < 10:
            return "Jest chłodno."
        elif self.temperature < 20:
            return "Temperatura jest przyjemna."
        elif self.temperature < 30:
            return "Jest ciepło."
        else:
            return "Jest bardzo gorąco, pot spływa strumieniami."
    
    def get_full_weather_description(self) -> str:
        """Zwraca pełny opis pogody."""
        parts = [
            self.get_weather_description(),
            self.get_wind_description(),
            self.get_temperature_description()
        ]
        
        return " ".join(parts)
    
    def get_visibility_modifier(self) -> float:
        """Zwraca modyfikator widoczności (0.0 - 1.0)."""
        return self.weather_effects[self.current_weather]['visibility']
    
    def get_movement_modifier(self) -> float:
        """Zwraca modyfikator prędkości ruchu."""
        return self.weather_effects[self.current_weather]['movement_speed']
    
    def get_mood_modifier(self) -> float:
        """Zwraca modyfikator nastroju."""
        return self.weather_effects[self.current_weather]['mood']
    
    def is_outdoor_weather_harsh(self) -> bool:
        """Sprawdza czy pogoda jest trudna do zniesienia na zewnątrz."""
        return self.current_weather in [WeatherType.STORM, WeatherType.SNOW] or \
               self.temperature < -5 or self.temperature > 30
    
    def affects_torches(self) -> bool:
        """Sprawdza czy pogoda może gasić pochodnie."""
        return self.current_weather in [WeatherType.RAIN, WeatherType.STORM]
    
    def force_weather(self, weather_type: WeatherType):
        """Wymusza konkretny typ pogody."""
        self.current_weather = weather_type
        self.time_elapsed = 0
        self.weather_duration = random.randint(60, 240)
    
    def save_state(self) -> Dict[str, Any]:
        """Zapisz stan systemu pogody.
        
        Returns:
            Słownik ze stanem pogody
        """
        return {
            'current_weather': self.current_weather.value,
            'time_elapsed': self.time_elapsed,
            'weather_duration': self.weather_duration,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'wind_strength': self.wind_strength.value,
            'wind_direction': self.wind_direction
        }
    
    def load_state(self, data: Dict[str, Any]):
        """Wczytaj stan systemu pogody.
        
        Args:
            data: Dane pogody
        """
        if 'current_weather' in data:
            self.current_weather = WeatherType(data['current_weather'])
        if 'time_elapsed' in data:
            self.time_elapsed = data['time_elapsed']
        if 'weather_duration' in data:
            self.weather_duration = data['weather_duration']
        if 'temperature' in data:
            self.temperature = data['temperature']
        if 'humidity' in data:
            self.humidity = data['humidity']
        if 'wind_strength' in data:
            self.wind_strength = WindStrength(data['wind_strength'])
        if 'wind_direction' in data:
            self.wind_direction = data['wind_direction']