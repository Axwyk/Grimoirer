from django.db import models

# Mapeo de tipo de arma → rol
# Se extrae la parte central del ID de arma: T6_MAIN_HOLYSTAFF_AVALON@2 → HOLYSTAFF
ROLE_HEALER = 'HEALER'
ROLE_TANK = 'TANK'
ROLE_SUPPORT = 'SUPPORT'
ROLE_DPS = 'DPS'

ROLE_CHOICES = [
    (ROLE_DPS, 'DPS'),
    (ROLE_HEALER, 'Healer'),
    (ROLE_TANK, 'Tank'),
    (ROLE_SUPPORT, 'Support'),
]

# Sub-roles para display más granular
SUB_ROLE_CHOICES = [
    # Healers
    ('HOLY', 'Holy'),
    ('NATURE', 'Nature'),
    # Tanks
    ('HAMMER', 'Hammer'),
    ('MACE', 'Mace'),
    # Supports
    ('ARCANE', 'Arcane'),
    ('CURSE', 'Curse'),
    ('FROST', 'Frost'),
    # DPS
    ('MELEE', 'Melee DPS'),
    ('RANGED', 'Ranged DPS'),
]

# Keywords en el ID de arma que determinan el rol
HEALER_WEAPONS = {
    'HOLYSTAFF', 'DIVINESTAFF', 'REDEMPTIONSTAFF', 'HALLOWFALL', 'LIFETOUCH',
    'NATURESTAFF', 'WILDSTAFF', 'DRUIDICSTAFF', 'RAMPANTSTAFF', 'IRONROOTSTAFF',
}
TANK_WEAPONS = {
    'HAMMER', 'POLEHAMMER', 'DUALHAMMER', 'TOMBHAMMER', 'GROVEKEEPER', 'FORGE',
    'MACE', 'FLAIL', 'ROCKMACE', 'DUALMACE', 'OATHKEEPERS', 'CAMLANN', 'INCUBUS',
    'KNUCKLES',
}
SUPPORT_WEAPONS = {
    # Arcane
    'ARCANESTAFF', 'ENIGMATICSTAFF', 'ENIGMATICORB', 'OCCULTSTAFF', 'WITCHWORK',
    'MALEVOLENT', 'LOCUS',
    # Curse (soportes ofensivos - Maldiciones)
    'CURSEDSTAFF', 'DEMONICSTAFF', 'GREATCURSEDSTAFF', 'CURSEDSKULL',
    'DAMNATION', 'SHADOWCALLER',
    # Frost (stopper/soporte)
    'GLACIALSTAFF', 'CHILLHOWL',
    # Shapeshifter (cambiaformas)
    'SHAPESHIFTER',
}

# Mapeo para sub-rol display
WEAPON_TO_SUBROLE = {
    # Holy healers
    'HOLYSTAFF': 'HOLY', 'DIVINESTAFF': 'HOLY', 'REDEMPTIONSTAFF': 'HOLY',
    'HALLOWFALL': 'HOLY', 'LIFETOUCH': 'HOLY',
    # Nature healers
    'NATURESTAFF': 'NATURE', 'WILDSTAFF': 'NATURE', 'DRUIDICSTAFF': 'NATURE',
    'RAMPANTSTAFF': 'NATURE', 'IRONROOTSTAFF': 'NATURE',
    # Hammers
    'HAMMER': 'HAMMER', 'POLEHAMMER': 'HAMMER', 'DUALHAMMER': 'HAMMER',
    'TOMBHAMMER': 'HAMMER', 'GROVEKEEPER': 'HAMMER', 'FORGE': 'HAMMER',
    # Maces
    'MACE': 'MACE', 'FLAIL': 'MACE', 'ROCKMACE': 'MACE', 'DUALMACE': 'MACE',
    'OATHKEEPERS': 'MACE', 'CAMLANN': 'MACE', 'INCUBUS': 'MACE', 'KNUCKLES': 'MACE',
    # Arcane
    'ARCANESTAFF': 'ARCANE', 'ENIGMATICSTAFF': 'ARCANE', 'ENIGMATICORB': 'ARCANE',
    'OCCULTSTAFF': 'ARCANE', 'WITCHWORK': 'ARCANE', 'MALEVOLENT': 'ARCANE', 'LOCUS': 'ARCANE',
    # Curse
    'CURSEDSTAFF': 'CURSE', 'DEMONICSTAFF': 'CURSE', 'GREATCURSEDSTAFF': 'CURSE',
    'CURSEDSKULL': 'CURSE', 'DAMNATION': 'CURSE', 'SHADOWCALLER': 'CURSE',
    # Frost
    'FROSTSTAFF': 'FROST', 'GREATFROSTSTAFF': 'FROST', 'GLACIALSTAFF': 'FROST',
    'ICICLE': 'FROST', 'PERMAFROST': 'FROST', 'CHILLHOWL': 'FROST',
}

ALBION_RENDER_URL = 'https://render.albiononline.com/v1/item/{item_id}.png'


def _extract_weapon_keyword(weapon_type):
    """Extract the weapon keyword from Albion weapon ID."""
    if not weapon_type:
        return None
    clean = weapon_type.split('@')[0]
    parts = clean.split('_')
    for part in parts[2:]:
        if part in HEALER_WEAPONS or part in TANK_WEAPONS or part in SUPPORT_WEAPONS:
            return part
    return None


def get_role_from_weapon(weapon_type):
    """Determina el rol a partir del tipo de arma de Albion.
    Ej: T6_MAIN_HOLYSTAFF_AVALON@2 → HEALER
    """
    if not weapon_type:
        return ROLE_DPS
    clean = weapon_type.split('@')[0]
    parts = clean.split('_')
    weapon_keywords = set()
    for part in parts[2:]:
        weapon_keywords.add(part)

    # Prioridad: SHAPESHIFTER siempre SUPPORT (match parcial)
    for kw in weapon_keywords:
        if any('SHAPESHIFTER' in kw_part for kw_part in weapon_keywords):
            return ROLE_SUPPORT
    for kw in weapon_keywords:
        if kw in HEALER_WEAPONS:
            return ROLE_HEALER
    for kw in weapon_keywords:
        if kw in TANK_WEAPONS:
            return ROLE_TANK
    for kw in weapon_keywords:
        if kw in SUPPORT_WEAPONS:
            return ROLE_SUPPORT
    return ROLE_DPS


def get_subrole_from_weapon(weapon_type):
    """Determina el sub-rol display del arma."""
    if not weapon_type:
        return None
    clean = weapon_type.split('@')[0]
    parts = clean.split('_')
    for part in parts[2:]:
        if part in WEAPON_TO_SUBROLE:
            return WEAPON_TO_SUBROLE[part]
    return None


class Battle(models.Model):
    zone = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_players = models.IntegerField(default=0)
    total_kills = models.IntegerField(default=0)
    total_guilds = models.IntegerField(default=0)
    is_valid = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    elo_updated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['is_valid', 'processed']),
        ]

    def __str__(self):
        return f'Battle {self.zone} ({self.start_time:%Y-%m-%d %H:%M}) — {self.total_players}p/{self.total_kills}k'


class PlayerBattleStats(models.Model):
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name='player_stats')
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='battle_stats')

    damage_done = models.BigIntegerField(default=0)
    healing_done = models.BigIntegerField(default=0)
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    kill_fame = models.BigIntegerField(default=0)

    main_weapon = models.CharField(max_length=200, blank=True, default='')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_DPS)
    average_item_power = models.FloatField(default=0)

    raw_score = models.FloatField(default=0)
    normalized_score = models.FloatField(default=0)

    elo_before = models.IntegerField(null=True, blank=True)
    elo_after = models.IntegerField(null=True, blank=True)
    elo_change = models.IntegerField(default=0)

    class Meta:
        unique_together = ('battle', 'player')
        ordering = ['-raw_score']

    def __str__(self):
        return f'{self.player} — Score: {self.raw_score:.1f}'
