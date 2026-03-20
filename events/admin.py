from django.contrib import admin

from events.models import Event, EventParticipant


class EventParticipantInline(admin.TabularInline):
    model = EventParticipant
    extra = 0
    readonly_fields = ['player', 'damage_done', 'healing_done']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'timestamp', 'zone', 'killer', 'victim', 'total_kill_fame', 'battle']
    list_filter = ['zone']
    search_fields = ['event_id', 'killer__name', 'victim__name']
    readonly_fields = [
        'event_id', 'battle_id_api', 'timestamp', 'zone',
        'killer', 'victim', 'total_kill_fame', 'raw_data',
    ]
    inlines = [EventParticipantInline]
