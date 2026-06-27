# -*- coding: utf-8 -*-
"""LaunchBoards — Schwester-Produkt von SoftwareCenter (gemeinsamer Unterbau).

Startet denselben Code mit dem LaunchBoards-Profil: eigener Name, eigenes Icon,
eigener QSettings-Namespace und eigene Single-Instance. Dadurch laufen
SoftwareCenter und LaunchBoards parallel mit getrennten Profilen.

Falls LaunchBoards später eigene Features bekommt (z.B. Zeichnen auf Boards),
kann es anhand dieser Trennung sauber in ein eigenes Repo ausgegliedert werden.
"""
from SoftwareCenter import main, PROFILE_LAUNCHBOARDS

if __name__ == "__main__":
    main(PROFILE_LAUNCHBOARDS)
