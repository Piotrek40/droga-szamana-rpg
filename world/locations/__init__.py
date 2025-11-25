#!/usr/bin/env python3
"""
Modul lokacji swiata gry Droga Szamana.
Eksportuje glowne klasy lokacji.
"""

from world.locations.prison import (
    Prison,
    Location,
    LocationType,
    PrisonCell,
    PrisonCorridor,
    PrisonCourtyard,
    PrisonKitchen,
    PrisonArmory,
    WardenOffice,
    PrisonGuardPost,
    PrisonPantry,
    TortureChamber,
    DungeonCells,
    PrivateQuarters,
    PrisonGate,
    PrisonCanteen
)

from world.locations.dark_forest import (
    CzarnyLas,
    ForestLocation,
    ForestLocationType,
    DruidGrove,
    AbandonedLoggingCamp,
    DarkForestDepths
)

from world.locations.market_town import (
    TargowiskoTrzechDrog,
    MarketDistrict,
    DistrictType,
    MainMarketSquare,
    SlumsDistrict,
    NobleDistrict
)

__all__ = [
    # Prison
    'Prison',
    'Location',
    'LocationType',
    'PrisonCell',
    'PrisonCorridor',
    'PrisonCourtyard',
    'PrisonKitchen',
    'PrisonArmory',
    'WardenOffice',
    'PrisonGuardPost',
    'PrisonPantry',
    'TortureChamber',
    'DungeonCells',
    'PrivateQuarters',
    'PrisonGate',
    'PrisonCanteen',
    # Dark Forest
    'CzarnyLas',
    'ForestLocation',
    'ForestLocationType',
    'DruidGrove',
    'AbandonedLoggingCamp',
    'DarkForestDepths',
    # Market Town
    'TargowiskoTrzechDrog',
    'MarketDistrict',
    'DistrictType',
    'MainMarketSquare',
    'SlumsDistrict',
    'NobleDistrict',
]
