# System Questów Emergentnych - Dokumentacja

## Przegląd Systemu

System questów emergentnych dla Droga Szamana RPG został zaprojektowany, aby tworzyć naturalne, wyłaniające się ze stanu świata questy, zamiast statycznych zadań typu "przynieś 10 skór wilka". Każdy quest ma znaczenie, konsekwencje rozchodzą się po świecie, a wybory gracza mają wpływ na przyszłość.

## Główne Komponenty

### 1. Quest Engine (`quests/quest_engine.py`)
- **QuestEngine**: Główny silnik zarządzający questami
- **QuestSeed**: Ziarna questów z warunkami aktywacji
- **EmergentQuest**: Bazowa klasa dla wszystkich questów
- **QuestBranch**: Różne ścieżki rozwiązania questów
- **Investigation**: System śledztwa i zbierania wskazówek

### 2. Konkretne Questy (`quests/emergent_quests.py`)
- **PrisonEscapeQuest**: Planowanie i wykonanie ucieczki z więzienia
- **ContrabandTradeQuest**: Handel przemytem w więzieniu
- **PrisonGangWarQuest**: Konflikty między gangami więziennymi
- **CorruptionExposureQuest**: Ujawnienie korupcji wśród strażników
- **PrisonDiseaseQuest**: Epidemia w więzieniu
- **InformationGatheringQuest**: Zbieranie cennych informacji
- **RevengeQuest**: Zemsta za doznane krzywdy

### 3. System Konsekwencji (`quests/quest_consequences.py`)
- **ConsequenceTracker**: Śledzi i wykonuje konsekwencje
- **ConsequenceEffect**: Pojedyncze efekty wpływające na świat
- **ConsequenceChain**: Kaskadowe łańcuchy konsekwencji
- **TrackedConsequence**: Konsekwencje rozłożone w czasie

### 4. Integracja z GUI (`integrated_gui.py`)
- Zakładka questów w interfejsie
- Wyświetlanie aktywnych sytuacji
- Panel konsekwencji działań
- Interaktywne rozwiązywanie questów

## Kluczowe Cechy

### Odkrywanie Questów
Questy nie są przydzielane automatycznie. Gracz musi je odkryć poprzez:
- **Podsłuchiwanie** rozmów NPCów
- **Obserwację** wydarzeń w świecie
- **Znalezienie** wskazówek i dokumentów
- **Otrzymanie** informacji od zaufanych NPCów
- **Natknięcie się** przypadkowo
- **Konsekwencje** poprzednich działań

### Wielość Rozwiązań
Każdy quest oferuje minimum 3-4 różne podejścia:
- **Przemoc** - bezpośrednia konfrontacja
- **Skradanie** - działanie z ukrycia
- **Dyplomacja** - negocjacje i przekonywanie
- **Ekonomia** - łapówki, handel
- **Ignorowanie** - z konsekwencjami dla świata

### System Konsekwencji

#### Typy Konsekwencji:
- **Natychmiastowe** - efekty widoczne od razu
- **Opóźnione** - ujawniają się po czasie (godziny, dni, tygodnie)
- **Powtarzające się** - cykliczne efekty
- **Warunkowe** - aktywują się przy spełnieniu warunków
- **Kaskadowe** - wywołują kolejne konsekwencje
- **Permanentne** - trwałe zmiany w świecie

#### Zakres Wpływu:
- **Osobisty** - tylko gracz
- **Lokalny** - najbliższe otoczenie
- **Frakcja** - cała grupa/gang
- **Regionalny** - całe więzienie
- **Globalny** - cały świat gry

### System Śledztwa
Gracze prowadzą śledztwa poprzez:
1. **Przeszukiwanie** lokacji
2. **Przesłuchiwanie** NPCów
3. **Badanie** śladów
4. **Analizowanie** zebranych wskazówek
5. **Rekrutowanie** wspólników

## Przykładowe Questy

### 1. Ucieczka z Więzienia
**Aktywacja**: Gracz jest w więzieniu > 3 dni  
**Trasy ucieczki**:
- Tunel pod kuchnią (7 dni kopania)
- Słaby mur w celi 5 (5 dni)
- Przekupienie strażnika (2 dni negocjacji)
- Kanały ściekowe (1 dzień, wysokie ryzyko)
- Bunt jako przykrywka (3 dni przygotowań)

### 2. Wojna Gangów
**Aktywacja**: Napięcia między gangami > 70%  
**Rozwiązania**:
- Poprowadź gang do zwycięstwa
- Wynegocjuj pokój
- Zniszcz wszystkie gangi
- Skłóć gangi przeciwko sobie

### 3. Epidemia
**Aktywacja**: Warunki sanitarne < 30%, zarażeni > 2  
**Rozwiązania**:
- Znajdź i rozprowadź lekarstwo
- Wprowadź kwarantannę
- Wykorzystaj chaos dla własnych celów

## System Karmy

Działania gracza wpływają na karmę w kategoriach:
- **Dobro vs Zło** - pomoc vs krzywdzenie
- **Chaos vs Porządek** - destabilizacja vs stabilizacja
- **Neutralność** - balans między ekstremami

## Integracja ze Światem

### NPCe
- Pamiętają wydarzenia związane z questami
- Zmieniają relacje na podstawie wyborów gracza
- Mogą być wspólnikami lub przeciwnikami
- Generują własne questy na podstawie potrzeb

### Ekonomia
- Questy wpływają na ceny i dostępność towarów
- Monopole i kartele powstają z działań gracza
- Kryzys ekonomiczny może wywołać nowe questy

### Lokacje
- Zmieniają poziom bezpieczeństwa
- Mogą stać się niedostępne
- Nowe obszary otwierają się przez questy

## Wskazówki dla Rozwoju

### Dodawanie Nowych Questów
1. Stwórz klasę dziedziczącą po `EmergentQuest`
2. Zdefiniuj warunki aktywacji w `QuestSeed`
3. Dodaj gałęzie rozwiązania (`QuestBranch`)
4. Zaimplementuj system śledztwa
5. Określ konsekwencje każdej decyzji

### Najlepsze Praktyki
- Każdy quest powinien mieć minimum 3 sposoby rozwiązania
- Konsekwencje powinny być proporcjonalne do działań
- Ignorowanie questów też powinno mieć konsekwencje
- Questy powinny być ze sobą powiązane
- Unikaj questów jednorazowych - niech wpływają na świat

## Przykładowy Kod

### Tworzenie Questa
```python
seed = QuestSeed(
    quest_id="unique_id",
    name="Nazwa Questa",
    activation_conditions={
        "world_state_key": required_value
    },
    discovery_methods=[DiscoveryMethod.OVERHEARD],
    initial_clues={
        "location": "Wskazówka do odkrycia"
    },
    time_sensitive=True,
    expiry_hours=72,
    priority=7
)
```

### Dodawanie Konsekwencji
```python
consequence_data = {
    "effects": [{
        "target_type": "npc",
        "target_id": "all",
        "effect_type": "relationship",
        "magnitude": -5.0
    }],
    "type": "DELAYED",
    "scope": "LOCAL",
    "delay_hours": 24
}
tracker.add_consequence(quest_id, branch_id, consequence_data)
```

## Podsumowanie

System questów emergentnych tworzy żywy, reagujący świat gdzie:
- Questy wyłaniają się naturalnie z sytuacji
- Każda decyzja ma długoterminowe konsekwencje
- Świat żyje i zmienia się bez gracza
- NPCe pamiętają i reagują na wydarzenia
- Ekonomia i polityka są integralną częścią questów

System został zaprojektowany, aby każda rozgrywka była unikalna, a wybory gracza miały rzeczywiste znaczenie w świecie gry.