import logging
import time
from datetime import datetime

import requests
from django.conf import settings as django_settings
from django.db import IntegrityError

from players.models import Player
from events.models import Event, EventParticipant

logger = logging.getLogger(__name__)

ALBION_API_BASE = 'https://gameinfo.albiononline.com/api/gameinfo'


def _get_guild_id():
    """Busca el guild_id del gremio configurado en settings o en la DB."""
    guild_id = getattr(django_settings, 'TRACKED_GUILD_ID', None)
    if guild_id:
        return guild_id
    # Intentar encontrarlo en la DB
    guild_name = getattr(django_settings, 'TRACKED_GUILD', None)
    if guild_name:
        player = Player.objects.filter(guild_name=guild_name, guild_id__gt='').first()
        if player:
            return player.guild_id
    return None


def fetch_guild_battles(limit=20, max_pages=3):
    """
    Busca batallas recientes del gremio via la API de battles de Albion.
    Para cada batalla, obtiene los detalles completos y crea/actualiza
    los events y players correspondientes.
    Retorna (new_battles, new_events).
    """
    guild_id = _get_guild_id()
    if not guild_id:
        logger.error('No guild_id configured. Set TRACKED_GUILD_ID in settings.')
        return 0, 0

    total_new_battles = 0
    total_new_events = 0
    session = requests.Session()

    for page in range(max_pages):
        offset = page * limit
        url = f'{ALBION_API_BASE}/battles'
        params = {
            'guildId': guild_id,
            'limit': limit,
            'offset': offset,
            'sort': 'recent',
        }

        try:
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f'Error fetching guild battles (page {page}): {e}')
            break

        battles_data = response.json()
        if not battles_data:
            break

        new_in_page = 0
        for battle_data in battles_data:
            battle_id = battle_data.get('id')
            if not battle_id:
                continue

            # Obtener detalle completo de la batalla
            new_events = _fetch_and_store_battle_detail(battle_id, session)
            if new_events > 0:
                new_in_page += 1
                total_new_events += new_events
            time.sleep(0.5)  # Rate limiting

        total_new_battles += new_in_page
        logger.info(f'Page {page}: {new_in_page} new battles with events')

        if new_in_page == 0:
            break

    session.close()
    return total_new_battles, total_new_events


def _fetch_and_store_battle_detail(battle_id, session=None):
    """
    Fetch detalle de una batalla específica y crea events sintéticos
    a partir de los datos de jugadores.
    Retorna cantidad de events nuevos creados.
    """
    # Si ya tenemos events de esta batalla, skip
    existing = Event.objects.filter(battle_id_api=battle_id).count()
    if existing > 0:
        return 0

    http = session or requests
    url = f'{ALBION_API_BASE}/battles/{battle_id}'
    try:
        response = http.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f'Error fetching battle {battle_id}: {e}')
        return 0

    data = response.json()
    players_data = data.get('players', {})
    if not players_data:
        return 0

    # Parse timestamps
    start_str = data.get('startTime', '')
    try:
        timestamp = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        logger.warning(f'Invalid timestamp for battle {battle_id}')
        return 0

    zone = data.get('clusterName') or 'Unknown'

    # Complementar con eventos individuales para daño/healing
    damage_map, event_zone = _fetch_event_damage_for_battle(battle_id)
    if event_zone and zone == 'Unknown':
        zone = event_zone

    # Crear players y un "event" por cada kill/death en la batalla
    new_count = 0
    players_list = list(players_data.values())

    # Crear/actualizar todos los jugadores primero
    player_objects = {}
    for p_data in players_list:
        if not p_data.get('id'):
            continue
        player = _get_or_create_player(p_data)
        player_objects[p_data['id']] = player

    # Construir mapa de kills/deaths por DB player_id desde la API de batallas
    # Esto se almacena en raw_data para que calculate_battle_stats lo use
    api_player_stats = {}
    for p_data in players_list:
        pid = p_data.get('id')
        if pid and pid in player_objects:
            db_id = player_objects[pid].pk
            # Capturar arma principal del jugador
            equip = p_data.get('equipment', {}) or {}
            main_hand = equip.get('mainHand', equip.get('MainHand', {})) or {}
            weapon = main_hand.get('type', main_hand.get('Type', '')) or ''
            # También buscar en damage_map (tiene datos de events con Equipment PascalCase)
            dmg_data = damage_map.get(pid, {})
            if not weapon:
                weapon = dmg_data.get('weapon', '')
            # IP viene de damage_map (events API), battles API no lo tiene
            ip = dmg_data.get('ip', 0)
            api_player_stats[str(db_id)] = {
                'kills': p_data.get('kills', 0),
                'deaths': p_data.get('deaths', 0),
                'weapon': weapon,
                'ip': ip,
            }

    # Crear events sintéticos: uno por cada jugador con kills o deaths
    # Esto permite que nuestro sistema de stats funcione correctamente
    killers = [p for p in players_list if p.get('kills', 0) > 0]
    victims = [p for p in players_list if p.get('deaths', 0) > 0]

    # Crear un event por cada kill reportado en la batalla
    # Emparejamos killers con victims para generar events completos
    event_idx = 0
    for killer_data in killers:
        kid = killer_data.get('id')
        if not kid or kid not in player_objects:
            continue
        for _k in range(killer_data.get('kills', 0)):
            # Sintético event_id: negativo para no colisionar con IDs reales
            synth_event_id = -(battle_id * 1000 + event_idx)
            event_idx += 1

            # Buscar victim disponible
            victim_data = None
            for v in victims:
                if v.get('deaths', 0) > 0 and v.get('id') != kid:
                    victim_data = v
                    v['deaths'] -= 1
                    break

            if not victim_data or victim_data.get('id') not in player_objects:
                continue

            try:
                event = Event.objects.create(
                    event_id=synth_event_id,
                    battle_id_api=battle_id,
                    timestamp=timestamp,
                    zone=zone,
                    killer=player_objects[kid],
                    victim=player_objects[victim_data['id']],
                    total_kill_fame=killer_data.get('killFame', 0) // max(killer_data.get('kills', 1), 1),
                    number_of_participants=len(players_list),
                    raw_data={
                        'source': 'battles_api',
                        'battle_id': battle_id,
                        'api_player_stats': api_player_stats,
                    },
                )
                new_count += 1

                # Guardar participants con daño/healing
                for p_data in players_list:
                    pid = p_data.get('id')
                    if pid and pid in player_objects:
                        dmg_data = damage_map.get(pid, {})
                        try:
                            EventParticipant.objects.create(
                                event=event,
                                player=player_objects[pid],
                                damage_done=int(dmg_data.get('damage', 0)),
                                healing_done=int(dmg_data.get('healing', 0)),
                            )
                        except IntegrityError:
                            pass

            except IntegrityError:
                continue

    logger.info(f'Battle {battle_id}: {new_count} events, {len(players_list)} players')
    return new_count


def _fetch_event_damage_for_battle(battle_id):
    """
    Intenta obtener datos de daño/healing de los events de esta batalla.
    Retorna (damage_map, zone) donde:
      damage_map = {player_albion_id: {'damage': X, 'healing': Y}}
      zone = string con la ubicación o None
    """
    damage_map = {}
    zone = None
    guild_id = _get_guild_id()
    if not guild_id:
        return damage_map, zone

    # Buscar events del gremio que coincidan con este battle_id
    url = f'{ALBION_API_BASE}/events'
    params = {'guildId': guild_id, 'limit': 51}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        events = response.json()
    except requests.RequestException:
        return damage_map, zone

    for event in events:
        if event.get('BattleId') != battle_id:
            continue
        if not zone:
            zone = event.get('Location')
        for p in event.get('Participants', []):
            pid = p.get('Id')
            if pid:
                existing = damage_map.get(pid, {'damage': 0, 'healing': 0, 'weapon': '', 'ip': 0})
                existing['damage'] = max(existing['damage'], p.get('DamageDone', 0) or 0)
                existing['healing'] = max(existing['healing'], p.get('SupportHealingDone', 0) or 0)
                # Capturar arma principal
                equip = p.get('Equipment', {}) or {}
                main_hand = equip.get('MainHand', {}) or {}
                weapon = main_hand.get('Type', '') or ''
                if weapon and not existing.get('weapon'):
                    existing['weapon'] = weapon
                # Capturar IP (Item Power)
                ip = p.get('AverageItemPower', 0) or 0
                if ip > existing.get('ip', 0):
                    existing['ip'] = ip
                damage_map[pid] = existing

    return damage_map, zone


def fetch_and_store_events(limit=51, max_pages=5):
    """
    Fetch latest kill events from Albion API filtered by guild.
    Returns the count of new events stored.
    """
    guild_id = _get_guild_id()
    total_new = 0

    for page in range(max_pages):
        offset = page * limit
        params = {'limit': limit, 'offset': offset}
        if guild_id:
            params['guildId'] = guild_id

        try:
            response = requests.get(f'{ALBION_API_BASE}/events', params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f'Error fetching events (page {page}): {e}')
            break

        events_data = response.json()
        if not events_data:
            break

        new_in_page = 0
        for event_data in events_data:
            created = _store_single_event(event_data)
            if created:
                new_in_page += 1

        total_new += new_in_page
        logger.info(f'Page {page}: {new_in_page} new events')

        if new_in_page == 0:
            break

    return total_new


def _store_single_event(event_data):
    """Process and store a single event from the API. Returns True if new."""
    event_id = event_data.get('EventId')
    if not event_id:
        return False

    # Skip duplicates
    if Event.objects.filter(event_id=event_id).exists():
        return False

    killer_data = event_data.get('Killer', {})
    victim_data = event_data.get('Victim', {})

    if not killer_data.get('Id') or not victim_data.get('Id'):
        return False

    # Create/update players
    killer = _get_or_create_player(killer_data)
    victim = _get_or_create_player(victim_data)

    # Parse timestamp
    ts_str = event_data.get('TimeStamp', '')
    try:
        timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        logger.warning(f'Invalid timestamp for event {event_id}: {ts_str}')
        return False

    # Create event
    try:
        event = Event.objects.create(
            event_id=event_id,
            battle_id_api=event_data.get('BattleId'),
            timestamp=timestamp,
            zone=event_data.get('Location') or event_data.get('KillArea') or 'Unknown',
            killer=killer,
            victim=victim,
            total_kill_fame=event_data.get('TotalVictimKillFame', 0),
            number_of_participants=event_data.get('numberOfParticipants', 0),
            raw_data=event_data,
        )
    except IntegrityError:
        return False

    # Store participants (assist/damage info)
    for p_data in event_data.get('Participants', []):
        if not p_data.get('Id'):
            continue
        player = _get_or_create_player(p_data)
        try:
            EventParticipant.objects.create(
                event=event,
                player=player,
                damage_done=p_data.get('DamageDone', 0) or 0,
                healing_done=p_data.get('SupportHealingDone', 0) or 0,
            )
        except IntegrityError:
            pass

    return True


def _get_or_create_player(data):
    """Create or update a Player from Albion API data."""
    # Normalizar keys: battles API usa lowercase, events API usa PascalCase
    albion_id = data.get('Id') or data.get('id')
    if not albion_id:
        return None
    name = data.get('Name') or data.get('name') or 'Unknown'
    guild_name = data.get('GuildName') or data.get('guildName') or ''
    guild_id = data.get('GuildId') or data.get('guildId') or ''
    alliance_name = data.get('AllianceName') or data.get('allianceName') or ''
    alliance_id = data.get('AllianceId') or data.get('allianceId') or ''

    player, created = Player.objects.get_or_create(
        albion_id=albion_id,
        defaults={
            'name': name,
            'guild_name': guild_name,
            'guild_id': guild_id,
            'alliance_name': alliance_name,
            'alliance_id': alliance_id,
        }
    )
    if not created:
        changed = False
        if name and name != 'Unknown' and player.name != name:
            player.name = name
            changed = True
        if guild_name and player.guild_name != guild_name:
            player.guild_name = guild_name
            player.guild_id = guild_id
            changed = True
        if alliance_name and player.alliance_name != alliance_name:
            player.alliance_name = alliance_name
            player.alliance_id = alliance_id
            changed = True
        if changed:
            player.save()
    return player
