#!/usr/bin/env python3

import datetime
import getpass
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta as td

from pynami.nami import NaMi
from termcolor import colored

AGE_GROUPS = {
    "Wichtel": 0,
    "Biber": 5,
    "Wölfling": 7,
    "Jungpfadfinder": 10,
    "Pfadfinder": 13,
    "Rover": 16,
    "Leiter": 21,
}
STUFEN = list(AGE_GROUPS.keys())
DATE_FMT = "%Y-%m-%d"
DAYS_PER_YEAR = 365.2425


def age_from_birthday(birthday):
    return (dt.now().date() - birthday).days / DAYS_PER_YEAR


def ist_zu_alt_fuer_die_stufe(stufe: str, age: float):
    if stufe == "Biber" and age >= AGE_GROUPS["Wölfling"]:
        return True
    if stufe == "Wölfling" and age >= AGE_GROUPS["Jungpfadfinder"]:
        return True
    if stufe == "Jungpfadfinder" and age >= AGE_GROUPS["Pfadfinder"]:
        return True
    if stufe == "Pfadfinder" and age >= AGE_GROUPS["Rover"]:
        return True
    if stufe == "Rover" and age >= AGE_GROUPS["Leiter"]:
        return True
    return False


@dataclass
class Kind:
    name: tuple[str, str]
    birthday: datetime.datetime
    stufe: str


def get_current_activities(user, nami):
    # NaMi will fuer diese Zuordnung die NaMi-interne ID. Das ist NICHT (immer) die Mitgliedsnummer!
    activities = nami.mgl_activities(user.id)
    current_activities = [act.taetigkeit for act in activities if not act.aktivBis]
    return current_activities


def main():
    username = input("Benutzername: ")
    password = getpass.getpass("Passwort: ")

    # Alle Kinder im Stamm:
    kinder: dict[str, Kind] = {}
    with NaMi(username=username, password=password) as nami:
        # Suche nach allen aktiven Mitgliedern. Das ist relativ schnell.
        active_members = nami.search(mglTypeId="MITGLIED", mglStatusId="AKTIV")
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Standardmaessig wird eine recht kompakte Version von Mitgliedsinformationen
            # zurueckgegeben. Leider muss jetzt fuer jede Person einzeln die komplette
            # Information eingefordert werden, um z.B. das Geburtsdatum zu erhalten.
            # Deswegen passiert das multi-threaded.
            futures = [
                executor.submit(member.get_mitglied, nami) for member in active_members
            ]
            for future in as_completed(futures):
                member = future.result()
                stufe = member.stufe
                current_activities = get_current_activities(member, nami)
                if "LeiterIn" in "|".join(current_activities):
                    stufe = "Leiter"
                elif "Wahlausschuss" in current_activities:
                    continue
                kinder[member.mitgliedsNummer] = Kind(
                    (member.vorname, member.nachname), member.geburtsDatum, stufe
                )

    # Erst Kinder, sortiert nach Stufen:
    stufen: dict[str, list[Kind]] = {
        s: [k for _, k in kinder.items() if k.stufe == s] for s in STUFEN
    }
    # Dann Kinder, sortiert nach Stufen + Alter:
    stufen: dict[str, list[Kind]] = {
        s: sorted(stufen[s], key=lambda x: x.birthday) for s in STUFEN
    }

    # Info ueber aufzustufende Kinder, stufenweise:
    COL_BREAKS = [38, 52, 65]
    for stufe, stufen_kinder in list(stufen.items())[:-1]:
        text = f"{stufe.upper()}"
        text += (COL_BREAKS[0] - len(text)) * " "
        text += "Geboren am"
        text += (COL_BREAKS[1] - len(text)) * " "
        text += "Alter"
        text += (COL_BREAKS[2] - len(text)) * " "
        text += f"wann {AGE_GROUPS[STUFEN[STUFEN.index(stufe) + 1]]}?"
        print(f"\n{text}")

        for kind in stufen_kinder:
            birthday = kind.birthday
            age = age_from_birthday(birthday)
            muss_aufgestuft_werden = ist_zu_alt_fuer_die_stufe(stufe, age)
            kann_aufgestuft_werden = ist_zu_alt_fuer_die_stufe(stufe, age + 0.5)
            # ^ NOTE: "muss" & "kann" sind natuerlich keine verbindlichen Begriffe hier...
            color = "yellow" if kann_aufgestuft_werden else "white"
            color = "red" if muss_aufgestuft_werden else color

            vorname, nachname = kind.name
            text = f"{nachname}, {vorname}"
            text += (COL_BREAKS[0] - len(text)) * " "
            text += birthday.strftime("%Y-%m-%d")

            text += (COL_BREAKS[1] - len(text)) * " "
            years = math.floor(age)
            months = math.floor((age - years) * 12)
            text += f"{years}y {months}m"

            if kann_aufgestuft_werden:
                text += (COL_BREAKS[2] - len(text)) * " "
                deadline_age = AGE_GROUPS[STUFEN[STUFEN.index(stufe) + 1]]
                text += (birthday + td(days=deadline_age * DAYS_PER_YEAR)).strftime(
                    DATE_FMT
                )

            print(colored(text, color))


if __name__ == "__main__":
    main()
