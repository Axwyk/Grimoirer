from battles.models import Battle

# Marca todas las batallas como no procesadas y sin ELO actualizado
def run():
    Battle.objects.all().update(processed=False, elo_updated=False)
    print('Todas las batallas marcadas como no procesadas y sin ELO actualizado.')
