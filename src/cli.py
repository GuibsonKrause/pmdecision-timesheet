"""
cli.py — Módulo de entrada do usuário via CLI interativo.

Solicita: mês/ano de referência, dia inicial, dia final, feriados, total de horas.
Usa prompts de texto para compatibilidade com Python 3.14.
"""

import calendar
from datetime import date
from InquirerPy import inquirer


def _ask_int(message: str, default: int, min_val: int = 1, max_val: int = 999) -> int:
    """Solicita um número inteiro ao usuário com validação."""
    while True:
        raw = inquirer.text(
            message=message,
            default=str(default),
        ).execute()
        try:
            value = int(raw.strip())
            if min_val <= value <= max_val:
                return value
            print(f"  [!] Valor deve estar entre {min_val} e {max_val}.")
        except ValueError:
            print("  [!] Digite um número inteiro válido.")


def _ask_float(message: str, default: float, min_val: float = 1) -> float:
    """Solicita um número decimal ao usuário com validação."""
    while True:
        raw = inquirer.text(
            message=message,
            default=str(default),
        ).execute()
        try:
            value = float(raw.strip())
            if value >= min_val:
                return value
            print(f"  [!] Valor deve ser pelo menos {min_val}.")
        except ValueError:
            print("  [!] Digite um número válido.")


def get_user_input() -> dict:
    """Solicita e valida os dados de entrada do usuário."""

    today = date.today()

    # Mês de referência
    month = _ask_int("Mes de referencia (1-12):", default=today.month, min_val=1, max_val=12)

    # Ano de referência
    year = _ask_int("Ano de referencia:", default=today.year, min_val=2020, max_val=2099)

    # Último dia do mês selecionado
    last_day_of_month = calendar.monthrange(year, month)[1]

    month_name = calendar.month_name[month]
    print(f"\n  Periodo selecionado: {month_name}/{year}\n")

    # Dia inicial
    start_day = _ask_int("Dia inicial do periodo:", default=1, min_val=1, max_val=last_day_of_month)

    # Dia final (default = último dia do mês ou dia atual se for o mês corrente)
    default_end = today.day if (month == today.month and year == today.year) else last_day_of_month
    end_day = _ask_int("Dia final do periodo:", default=default_end, min_val=start_day, max_val=last_day_of_month)

    # Feriados
    holidays_input = inquirer.text(
        message="Dias de feriado (separados por virgula, ou vazio):",
        default="",
    ).execute()

    holidays: list[int] = []
    if holidays_input.strip():
        holidays = [int(d.strip()) for d in holidays_input.split(",") if d.strip()]

    # Total de horas
    total_hours = _ask_float("Total de horas a lancar no mes:", default=160)

    # Confirmar modo dry-run
    dry_run = inquirer.confirm(
        message="Executar em modo DRY-RUN (sem automacao web)?",
        default=False,
    ).execute()

    return {
        "start_day": start_day,
        "end_day": end_day,
        "holidays": holidays,
        "total_hours": total_hours,
        "month": month,
        "year": year,
        "dry_run": dry_run,
    }
