from datetime import date
from .models import Culture


def estimer_frequence_jours(culture: Culture) -> int:
    besoin = culture.besoin_base_l_j

    if besoin is None or besoin <= 0:
        return 3  # fréquence par défaut

    if besoin <= 2:
        return 4  # peu d'eau
    elif besoin <= 5:
        return 3  # moyen
    else:
        return 2  # beaucoup d'eau


def doit_etre_arrosee_aujourdhui(culture: Culture, aujourd_hui: date) -> bool:
    if not culture.date_semis or not culture.date_recolte_prevue:
        return False

    if aujourd_hui < culture.date_semis or aujourd_hui > culture.date_recolte_prevue:
        return False

    freq = estimer_frequence_jours(culture)
    start = culture.date_semis

    if aujourd_hui < start:
        return False

    delta_jours = (aujourd_hui - start).days
    return (delta_jours % freq) == 0


def doit_etre_recoltee_aujourdhui(culture: Culture, aujourd_hui: date) -> bool:
    if not culture.date_recolte_prevue:
        return False
    return culture.date_recolte_prevue == aujourd_hui
