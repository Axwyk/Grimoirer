import logging
from datetime import timedelta

from django.db import transaction

from events.models import Event
from battles.models import Battle, PlayerBattleStats, get_role_from_weapon, ROLE_HEALER, ROLE_DPS, ROLE_TANK, ROLE_SUPPORT

logger = logging.getLogger(__name__)

# --- Configuración ---
BATTLE_TIME_WINDOW = timedelta(minutes=5)
MIN_PLAYERS = 4
MIN_KILLS = 2
MIN_GUILDS = 2


# =====================
# 1. AGRUPACIÓN
# =====================

def group_battles():
    """
    Agrupa eventos sin battle asignada en battles.
    Prioriza battle_id_api (del API de Albion), fallback a zona + tiempo.
    Retorna cantidad de battles creadas.
    """
    ungrouped = Event.objects.filter(battle__isnull=True).order_by('timestamp')

    if not ungrouped.exists():
        return 0

    battles_created = 0
    # Mapa: api_battle_id -> Battle object (para agrupación por API ID)
    api_battle_map = {}
    # Mapa: zone -> lista de battles abiertas (fallback)
    open_battles = {}

    for event in ungrouped.iterator():
        assigned = False

        # Prioridad 1: Agrupar por battle_id_api si existe
        if event.battle_id_api:
            api_id = event.battle_id_api
            if api_id in api_battle_map:
                battle = api_battle_map[api_id]
                event.battle = battle
                event.save(update_fields=['battle'])

                if event.timestamp < battle.start_time:
                    battle.start_time = event.timestamp
                if event.timestamp > battle.end_time:
                    battle.end_time = event.timestamp
                battle.save(update_fields=['start_time', 'end_time'])
                assigned = True
            else:
                # Buscar battle existente con este api_id
                existing = Battle.objects.filter(
                    events__battle_id_api=api_id
                ).first()
                if existing:
                    api_battle_map[api_id] = existing
                    event.battle = existing
                    event.save(update_fields=['battle'])
                    assigned = True

        # Prioridad 2: Fallback a zona + ventana temporal
        if not assigned:
            zone = event.zone
            if zone in open_battles:
                for battle in open_battles[zone]:
                    if (event.timestamp >= battle.start_time - BATTLE_TIME_WINDOW and
                            event.timestamp <= battle.end_time + BATTLE_TIME_WINDOW):
                        event.battle = battle
                        event.save(update_fields=['battle'])

                        if event.timestamp < battle.start_time:
                            battle.start_time = event.timestamp
                        if event.timestamp > battle.end_time:
                            battle.end_time = event.timestamp
                        battle.save(update_fields=['start_time', 'end_time'])

                        assigned = True
                        break

        if not assigned:
            zone = event.zone
            battle = Battle.objects.create(
                zone=zone,
                start_time=event.timestamp,
                end_time=event.timestamp,
            )
            event.battle = battle
            event.save(update_fields=['battle'])

            if event.battle_id_api:
                api_battle_map[event.battle_id_api] = battle
            open_battles.setdefault(zone, []).append(battle)
            battles_created += 1

    # Actualizar metadatos y validar
    _update_battle_metadata()

    # Fusionar batallas cercanas con jugadores en común
    merged = _merge_overlapping_battles()
    if merged:
        _update_battle_metadata()

    return battles_created


MERGE_TIME_WINDOW = timedelta(minutes=5)
MERGE_PLAYER_OVERLAP = 0.65  # 65% de jugadores compartidos para fusionar


def _merge_overlapping_battles():
    """
    Fusiona batallas que ocurren en tiempos cercanos con jugadores en común.
    Similar a cómo albionbb.com/battles/multi detecta peleas extendidas.
    Solo fusiona batallas no procesadas aún.
    """
    battles = list(
        Battle.objects.filter(processed=False)
        .order_by('start_time')
    )
    if len(battles) < 2:
        return 0

    # Construir mapa de jugadores por batalla
    battle_players = {}
    for battle in battles:
        player_ids = set()
        for event in battle.events.select_related('killer', 'victim').all():
            player_ids.add(event.killer_id)
            player_ids.add(event.victim_id)
        battle_players[battle.id] = player_ids

    merged_count = 0
    merged_ids = set()

    for i, b1 in enumerate(battles):
        if b1.id in merged_ids:
            continue
        for b2 in battles[i + 1:]:
            if b2.id in merged_ids:
                continue
            # Comprobar ventana temporal
            time_gap = b2.start_time - b1.end_time
            if time_gap > MERGE_TIME_WINDOW:
                continue

            # Comprobar solapamiento de jugadores
            p1 = battle_players.get(b1.id, set())
            p2 = battle_players.get(b2.id, set())
            if not p1 or not p2:
                continue
            overlap = len(p1 & p2)
            smaller = min(len(p1), len(p2))
            if smaller > 0 and overlap / smaller >= MERGE_PLAYER_OVERLAP:
                # Fusionar b2 en b1
                b2.events.update(battle=b1)
                # Actualizar tiempos
                b1.start_time = min(b1.start_time, b2.start_time)
                b1.end_time = max(b1.end_time, b2.end_time)
                b1.save(update_fields=['start_time', 'end_time'])
                # Registrar jugadores fusionados
                battle_players[b1.id] = p1 | p2
                merged_ids.add(b2.id)
                merged_count += 1

    # Eliminar batallas vacías (fueron absorbidas)
    if merged_ids:
        Battle.objects.filter(id__in=merged_ids).delete()
        logger.info(f'Merged {merged_count} overlapping battles')

    return merged_count


def _update_battle_metadata():
    """Calcula total_players, total_kills, total_guilds y valida cada battle."""
    from players.models import Player

    battles = Battle.objects.filter(is_valid=False, processed=False)

    for battle in battles:
        events = battle.events.select_related('killer', 'victim').all()
        player_ids = set()
        guild_names = set()
        best_zone = battle.zone

        for event in events:
            player_ids.add(event.killer_id)
            player_ids.add(event.victim_id)
            # Guilds from Player objects (works for both real and synthetic events)
            if event.killer.guild_name:
                guild_names.add(event.killer.guild_name)
            if event.victim.guild_name:
                guild_names.add(event.victim.guild_name)
            # Pick best zone from events
            if best_zone in ('Unknown', '') and event.zone not in ('Unknown', ''):
                best_zone = event.zone

            for ep in event.participants.select_related('player').all():
                player_ids.add(ep.player_id)
                if ep.player.guild_name:
                    guild_names.add(ep.player.guild_name)

        battle.zone = best_zone
        battle.total_players = len(player_ids)
        battle.total_kills = events.count()
        battle.total_guilds = len(guild_names)

        battle.is_valid = (
            battle.total_players >= MIN_PLAYERS
            and battle.total_kills >= MIN_KILLS
            and battle.total_guilds >= MIN_GUILDS
        )
        battle.save()


# =====================
# 2. CÁLCULO DE STATS
# =====================

@transaction.atomic
def calculate_battle_stats(battle):
    """
    Calcula stats individuales y scores para una battle válida.
    Score = (Damage * 0.4) + (Assists * 0.3) + (Kills * 0.2) - (Deaths * 0.3)
    Luego normaliza con z-score dentro de la battle.
    """
    if battle.processed or not battle.is_valid:
        return

    events = battle.events.select_related('killer', 'victim').prefetch_related('participants')

    # Acumular stats por jugador
    stats = {}

    for event in events:
        kid = event.killer_id
        vid = event.victim_id

        # Solo contar kills/deaths de eventos reales (event_id > 0)
        # Los eventos sintéticos (event_id < 0) se generan desde la API de batallas
        # y duplican kills; la API ya suple via max() más abajo
        is_real = event.event_id > 0

        stats.setdefault(kid, _empty_stats())
        if is_real:
            stats[kid]['kills'] += 1
        stats[kid]['kill_fame'] += event.total_kill_fame

        stats.setdefault(vid, _empty_stats())
        if is_real:
            stats[vid]['deaths'] += 1

        for ep in event.participants.all():
            pid = ep.player_id
            stats.setdefault(pid, _empty_stats())
            stats[pid]['damage_done'] += ep.damage_done
            stats[pid]['healing_done'] += ep.healing_done
            if pid != kid and is_real:
                stats[pid]['assists'] += 1

    # Suplementar kills/deaths/weapon con datos de la API de batallas
    # (los eventos sintéticos no siempre capturan todas las muertes)
    api_stats_applied = set()
    for event in events:
        api_ps = event.raw_data.get('api_player_stats')
        if not api_ps:
            continue
        for pid_str, api_data in api_ps.items():
            pid = int(pid_str)
            if pid in api_stats_applied:
                continue
            api_stats_applied.add(pid)
            stats.setdefault(pid, _empty_stats())
            # Usar el máximo entre lo calculado por eventos y lo reportado por la API
            stats[pid]['deaths'] = max(stats[pid]['deaths'], api_data.get('deaths', 0))
            stats[pid]['kills'] = max(stats[pid]['kills'], api_data.get('kills', 0))
            # Capturar arma desde api_player_stats
            if api_data.get('weapon') and not stats[pid]['weapon']:
                stats[pid]['weapon'] = api_data['weapon']
            # Capturar IP desde api_player_stats
            api_ip = api_data.get('ip', 0)
            if api_ip and api_ip > stats[pid]['ip']:
                stats[pid]['ip'] = api_ip

    # Extraer armas desde raw_data de eventos reales (events API)
    for event in events:
        raw = event.raw_data
        if raw.get('source') == 'battles_api':
            continue  # ya procesado arriba
        # Eventos reales: raw_data contiene todo el JSON del event
        for p in raw.get('Participants', []):
            albion_id = p.get('Id')
            if not albion_id:
                continue
            equip = p.get('Equipment', {}) or {}
            main_hand = equip.get('MainHand', {}) or {}
            weapon = main_hand.get('Type', '') or ''
            if not weapon:
                continue
            # Buscar player_id por albion_id
            for pid, s in stats.items():
                # Necesitamos mapear albion_id → db_id
                pass
        # Método más directo: killer y victim
        killer_equip = raw.get('Killer', {}).get('Equipment', {}) or {}
        killer_mh = killer_equip.get('MainHand', {}) or {}
        killer_weapon = killer_mh.get('Type', '') or ''
        if killer_weapon and event.killer_id in stats and not stats[event.killer_id]['weapon']:
            stats[event.killer_id]['weapon'] = killer_weapon
        # IP de killer
        killer_ip = raw.get('Killer', {}).get('AverageItemPower', 0) or 0
        if killer_ip and event.killer_id in stats and killer_ip > stats[event.killer_id]['ip']:
            stats[event.killer_id]['ip'] = killer_ip

        victim_equip = raw.get('Victim', {}).get('Equipment', {}) or {}
        victim_mh = victim_equip.get('MainHand', {}) or {}
        victim_weapon = victim_mh.get('Type', '') or ''
        if victim_weapon and event.victim_id in stats and not stats[event.victim_id]['weapon']:
            stats[event.victim_id]['weapon'] = victim_weapon
        # IP de victim
        victim_ip = raw.get('Victim', {}).get('AverageItemPower', 0) or 0
        if victim_ip and event.victim_id in stats and victim_ip > stats[event.victim_id]['ip']:
            stats[event.victim_id]['ip'] = victim_ip

    # Determinar rol de cada jugador basado en su arma
    for s in stats.values():
        s['role'] = get_role_from_weapon(s['weapon'])

    # Calcular raw score con ajuste por rol
    # Los coeficientes de kills/assists/deaths se escalan al orden de magnitud
    # del daño/healing (miles) para que sean significativos en el z-score.
    #
    # DPS:     Daño × 0.18  + Kills × 600  + Assists × 150  - Deaths × 600
    # HEALER:  Heal × 0.40  + Assists × 400 + Kills × 600   - Deaths × 500
    # TANK:    Assists × 800 + Daño × 0.12  + Kills × 600   - Deaths × 500
    # SUPPORT: Assists × 800 + Heal × 0.18  + Daño × 0.08 + Kills × 600  - Deaths × 500
    for s in stats.values():
        # Si el arma es shapeshifter, nunca forzar a healer
        is_shapeshifter = s['role'] == ROLE_SUPPORT and s['weapon'] and 'SHAPESHIFTER' in s['weapon'].upper()
        is_healer = (
            s['role'] == ROLE_HEALER
            or (s['healing_done'] > s['damage_done'] and s['healing_done'] > 0)
        )
        if is_healer and not is_shapeshifter:
            s['role'] = ROLE_HEALER
            s['raw_score'] = (
                s['healing_done'] * 0.40
                + s['assists'] * 400
                + s['kills'] * 600
                - s['deaths'] * 500
            )
        elif s['role'] == ROLE_TANK:
            s['raw_score'] = (
                s['assists'] * 800
                + s['damage_done'] * 0.12
                + s['kills'] * 600
                - s['deaths'] * 500
            )
        elif s['role'] == ROLE_SUPPORT:
            s['raw_score'] = (
                s['assists'] * 800
                + s['healing_done'] * 0.18
                + s['damage_done'] * 0.08
                + s['kills'] * 600
                - s['deaths'] * 500
            )
        else:
            s['raw_score'] = (
                s['damage_done'] * 0.18
                + s['kills'] * 600
                + s['assists'] * 150
                - s['deaths'] * 600
            )

    # Normalización z-score POR ROL con amortiguación por grupo pequeño
    from collections import defaultdict
    role_groups = defaultdict(list)
    for pid, s in stats.items():
        role_groups[s['role']].append(s)

    # Calcular media/std global para fallback cuando hay 1 solo del rol
    all_scores = [s['raw_score'] for s in stats.values()]
    global_n = len(all_scores)
    global_mean = sum(all_scores) / global_n if global_n > 0 else 0
    global_var = sum((x - global_mean) ** 2 for x in all_scores) / global_n if global_n > 1 else 0
    global_std = global_var ** 0.5 if global_var > 0 else 1.0

    for role, group in role_groups.items():
        scores = [s['raw_score'] for s in group]
        n = len(scores)
        if n > 1:
            mean = sum(scores) / n
            variance = sum((x - mean) ** 2 for x in scores) / n
            std = variance ** 0.5 if variance > 0 else 1.0
            # Factor de amortiguación: con 2 jugadores = 0.6, con 3 = 0.75, con 4+ = ~1.0
            dampen = min(1.0, 0.3 + (n / 6))
            for s in group:
                raw_norm = (s['raw_score'] - mean) / std if std > 0 else 0
                s['normalized_score'] = raw_norm * dampen
        else:
            # Solo 1 del rol: normalizar contra todos los jugadores de la batalla
            raw_norm = (group[0]['raw_score'] - global_mean) / global_std
            dampen = 0.5  # amortiguación extra por ser único del rol
            group[0]['normalized_score'] = raw_norm * dampen

    # Crear registros PlayerBattleStats
    for player_id, s in stats.items():
        PlayerBattleStats.objects.update_or_create(
            battle=battle,
            player_id=player_id,
            defaults={
                'damage_done': int(s['damage_done']),
                'healing_done': int(s['healing_done']),
                'kills': s['kills'],
                'deaths': s['deaths'],
                'assists': s['assists'],
                'kill_fame': s['kill_fame'],
                'main_weapon': s['weapon'],
                'role': s['role'],
                'average_item_power': round(s['ip'], 2),
                'raw_score': s['raw_score'],
                'normalized_score': s['normalized_score'],
            }
        )

    battle.processed = True
    battle.save(update_fields=['processed'])


def calculate_all_stats():
    """Calcula stats para todas las battles válidas no procesadas."""
    battles = Battle.objects.filter(is_valid=True, processed=False)
    count = 0
    for battle in battles:
        calculate_battle_stats(battle)
        count += 1
    return count


def _empty_stats():
    return {
        'damage_done': 0,
        'healing_done': 0,
        'kills': 0,
        'deaths': 0,
        'assists': 0,
        'kill_fame': 0,
        'weapon': '',
        'ip': 0,
        'role': ROLE_DPS,
        'raw_score': 0,
        'normalized_score': 0,
    }
