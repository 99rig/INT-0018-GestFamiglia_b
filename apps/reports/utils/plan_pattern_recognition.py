"""
Utility per il riconoscimento di pattern nei titoli dei piani di spesa
e la generazione intelligente di titoli per periodi successivi.
"""

import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PlanPatternRecognizer:
    """Classe per riconoscere pattern temporali nei titoli dei piani di spesa"""

    # Pattern per riconoscere mesi (completi e abbreviati)
    MONTH_PATTERNS = {
        # Nomi completi
        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
        'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12,
        # Abbreviazioni comuni
        'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6,
        'lug': 7, 'ago': 8, 'set': 9, 'sett': 9, 'ott': 10, 'nov': 11, 'dic': 12
    }

    # Arrays per la generazione dei nomi successivi
    FULL_MONTHS = [
        'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
        'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'
    ]

    SHORT_MONTHS = [
        'gen', 'feb', 'mar', 'apr', 'mag', 'giu',
        'lug', 'ago', 'set', 'ott', 'nov', 'dic'
    ]

    SHORT_MONTHS_WITH_SETT = [
        'gen', 'feb', 'mar', 'apr', 'mag', 'giu',
        'lug', 'ago', 'sett', 'ott', 'nov', 'dic'
    ]

    def __init__(self, plan_name: str):
        """
        Inizializza il recognizer con il nome del piano da analizzare

        Args:
            plan_name (str): Nome del piano di spesa
        """
        self.plan_name = plan_name
        self.title_lower = plan_name.lower()
        self._detected_month = None
        self._detected_year = None
        self._current_month_name = None

    def detect_patterns(self) -> dict:
        """
        Rileva pattern temporali nel titolo del piano

        Returns:
            dict: Dizionario con i pattern rilevati
        """
        # Cerca mese nel titolo (ordina per lunghezza decrescente per privilegiare match più lunghi)
        sorted_patterns = sorted(self.MONTH_PATTERNS.items(), key=lambda x: len(x[0]), reverse=True)
        for month_name, month_num in sorted_patterns:
            if month_name in self.title_lower:
                self._detected_month = month_num
                # Trova la versione con case originale nel titolo
                self._current_month_name = self._find_original_case_month(month_name)
                break

        # Cerca anno nel titolo (formato 2024, 2025, etc.)
        year_match = re.search(r'\b(20\d{2})\b', self.plan_name)
        if year_match:
            self._detected_year = int(year_match.group(1))

        return {
            'detected_month': self._detected_month,
            'detected_year': self._detected_year,
            'current_month_name': self._current_month_name,
            'title_pattern_used': bool(self._detected_month or self._detected_year)
        }

    def generate_next_period_title(self, plan_type: str = 'monthly') -> str:
        """
        Genera il titolo per il periodo successivo basato sui pattern rilevati

        Args:
            plan_type (str): Tipo di piano ('monthly', 'quarterly', 'yearly', 'custom')

        Returns:
            str: Nuovo titolo per il periodo successivo
        """
        # Se non sono stati rilevati pattern, usa i dati di detect_patterns
        if self._detected_month is None and self._detected_year is None:
            self.detect_patterns()

        # Se abbiamo pattern mese/anno, usa logica intelligente
        if self._detected_month and self._detected_year:
            return self._generate_smart_title()

        # Fallback: usa logica basata sul tipo di piano
        return self._generate_fallback_title(plan_type)

    def _generate_smart_title(self) -> str:
        """Genera titolo intelligente basato su mese e anno rilevati"""
        # Calcola il periodo successivo
        current_date = datetime(self._detected_year, self._detected_month, 1).date()
        next_date = current_date + relativedelta(months=1)

        new_title = self.plan_name

        if self._current_month_name:
            # Determina il tipo di formato (completo, abbreviato, o sett)
            next_month_name = self._get_next_month_name(next_date.month)

            # Preserva il case del titolo originale
            if self._current_month_name[0].isupper():
                next_month_name = next_month_name.capitalize()

            # Sostituisci il mese (ora _current_month_name ha il case originale)
            new_title = new_title.replace(self._current_month_name, next_month_name, 1)

            # Sostituisci anno se è cambiato
            if next_date.year != self._detected_year:
                new_title = new_title.replace(str(self._detected_year), str(next_date.year))

        return new_title

    def _get_next_month_name(self, next_month: int) -> str:
        """Ottiene il nome del mese successivo nel formato appropriato"""
        current_lower = self._current_month_name.lower()

        # Case speciale per "sett" (settembre abbreviato)
        if current_lower == 'sett':
            return self.SHORT_MONTHS_WITH_SETT[next_month - 1]
        elif current_lower in self.SHORT_MONTHS:
            # Usa abbreviazioni standard
            return self.SHORT_MONTHS[next_month - 1]
        else:
            # Usa nomi completi
            return self.FULL_MONTHS[next_month - 1]

    def _generate_fallback_title(self, plan_type: str) -> str:
        """Genera titolo di fallback basato sul tipo di piano"""
        if plan_type == 'monthly':
            return f"{self.plan_name} - Successivo"
        elif plan_type == 'quarterly':
            return f"{self.plan_name} - Trimestre Successivo"
        elif plan_type == 'yearly':
            return f"{self.plan_name} - Anno Successivo"
        else:
            return f"{self.plan_name} - Copia"

    def calculate_next_period_dates(self, start_date, end_date, plan_type: str = 'monthly') -> tuple:
        """
        Calcola le date per il periodo successivo

        Args:
            start_date: Data inizio del piano corrente
            end_date: Data fine del piano corrente
            plan_type (str): Tipo di piano

        Returns:
            tuple: (new_start_date, new_end_date)
        """
        # Se abbiamo pattern mese/anno, usa logica intelligente
        if self._detected_month and self._detected_year:
            current_date = datetime(self._detected_year, self._detected_month, 1).date()
            next_date = current_date + relativedelta(months=1)

            new_start_date = next_date.replace(day=start_date.day if start_date.day <= 28 else 1)

            if plan_type == 'monthly':
                new_end_date = (new_start_date + relativedelta(months=1)) - relativedelta(days=1)
            else:
                period_length = (end_date - start_date).days
                new_end_date = new_start_date + relativedelta(days=period_length)
        else:
            # Fallback: usa la logica standard basata sul tipo di piano
            if plan_type == 'monthly':
                new_start_date = start_date + relativedelta(months=1)
                new_end_date = end_date + relativedelta(months=1)
            elif plan_type == 'quarterly':
                new_start_date = start_date + relativedelta(months=3)
                new_end_date = end_date + relativedelta(months=3)
            elif plan_type == 'yearly':
                new_start_date = start_date + relativedelta(years=1)
                new_end_date = end_date + relativedelta(years=1)
            else:
                # Per piani personalizzati, duplica il periodo
                period_length = (end_date - start_date).days
                new_start_date = end_date + relativedelta(days=1)
                new_end_date = new_start_date + relativedelta(days=period_length)

        return new_start_date, new_end_date

    def _find_original_case_month(self, lowercase_month: str) -> str:
        """
        Trova la versione con case originale del mese nel titolo

        Args:
            lowercase_month (str): Nome del mese in lowercase

        Returns:
            str: Nome del mese con case originale dal titolo
        """
        import re

        # Crea un pattern che matcha il mese ignorando il case
        pattern = re.compile(re.escape(lowercase_month), re.IGNORECASE)
        match = pattern.search(self.plan_name)

        if match:
            return match.group(0)  # Restituisce la versione trovata nel titolo originale
        else:
            return lowercase_month  # Fallback


def generate_intelligent_clone_data(plan_name: str, start_date, end_date, plan_type: str = 'monthly') -> dict:
    """
    Funzione di utilità per generare tutti i dati necessari per un clone intelligente

    Args:
        plan_name (str): Nome del piano originale
        start_date: Data inizio del piano
        end_date: Data fine del piano
        plan_type (str): Tipo di piano

    Returns:
        dict: Dizionario con tutti i dati per il clone
    """
    recognizer = PlanPatternRecognizer(plan_name)
    patterns = recognizer.detect_patterns()

    new_title = recognizer.generate_next_period_title(plan_type)
    new_start_date, new_end_date = recognizer.calculate_next_period_dates(start_date, end_date, plan_type)

    return {
        'new_title': new_title,
        'new_start_date': new_start_date,
        'new_end_date': new_end_date,
        'pattern_detection': patterns
    }