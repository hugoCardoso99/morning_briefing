"""
Calendar node — checks if today or tomorrow is a notable date in Portugal.

Covers:
- Portuguese public holidays (fixed + moveable / Easter-based)
- A few widely observed informal dates (Carnival, etc.)

No API keys or external services needed — everything is computed locally.
"""

from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Easter calculation (Anonymous Gregorian algorithm)
# ---------------------------------------------------------------------------

def _easter(year: int) -> date:
    """Compute Easter Sunday for a given year."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


# ---------------------------------------------------------------------------
# Portuguese holidays for a given year
# ---------------------------------------------------------------------------

def _get_portuguese_holidays(year: int) -> dict[date, str]:
    """Return a dict mapping date -> holiday name for Portugal."""
    easter_date = _easter(year)

    holidays = {
        # Fixed public holidays
        date(year, 1, 1): "Ano Novo (New Year's Day)",
        date(year, 4, 25): "Dia da Liberdade (Freedom Day)",
        date(year, 5, 1): "Dia do Trabalhador (Labour Day)",
        date(year, 6, 10): "Dia de Portugal (Portugal Day)",
        date(year, 8, 15): "Assunção de Nossa Senhora (Assumption of Mary)",
        date(year, 10, 5): "Implantação da República (Republic Day)",
        date(year, 11, 1): "Dia de Todos os Santos (All Saints' Day)",
        date(year, 12, 1): "Restauração da Independência (Restoration of Independence)",
        date(year, 12, 8): "Imaculada Conceição (Immaculate Conception)",
        date(year, 12, 25): "Natal (Christmas Day)",

        # Moveable public holidays (Easter-based)
        easter_date + timedelta(days=-47): "Carnaval (Carnival) — not an official holiday but widely observed",
        easter_date + timedelta(days=-2): "Sexta-feira Santa (Good Friday)",
        easter_date: "Domingo de Páscoa (Easter Sunday)",
        easter_date + timedelta(days=60): "Corpo de Deus (Corpus Christi)",
    }

    return holidays


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

def calendar_node(state: dict) -> dict:
    """Check if today or tomorrow is a notable date in Portugal."""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    holidays = _get_portuguese_holidays(today.year)
    # Also check next year's holidays if we're near Dec 31
    if today.month == 12 and today.day >= 30:
        holidays.update(_get_portuguese_holidays(today.year + 1))

    today_notable = []
    tomorrow_notable = []

    if today in holidays:
        today_notable.append(holidays[today])
    if tomorrow in holidays:
        tomorrow_notable.append(holidays[tomorrow])

    return {
        "calendar": {
            "today_date": today.isoformat(),
            "tomorrow_date": tomorrow.isoformat(),
            "today_notable": today_notable,
            "tomorrow_notable": tomorrow_notable,
            "is_holiday_today": len(today_notable) > 0,
            "is_holiday_tomorrow": len(tomorrow_notable) > 0,
        }
    }
