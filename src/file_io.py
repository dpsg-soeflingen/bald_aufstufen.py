import warnings
import pandas as pd
from pathlib import Path


PATH_TO_EXPORTS = Path("..", "data", "in", "exports")


def load_excel_file(path):
    warnings.simplefilter("ignore")
    return pd.read_excel(path)


def load_export():
    file = "Mitglieder Grundinformationen mit Tätigkeiten und Stufe Abteilung.xlsx"
    path = Path(PATH_TO_EXPORTS, file)
    return load_excel_file(path)
