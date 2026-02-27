"""
cli.py — Módulo de entrada do usuário via CLI interativo.

Solicita: dia inicial, dia final, feriados, total de horas.
Usa prompts de texto para compatibilidade com Python 3.14.
"""

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
    current_month = today.month
    current_year = today.year

    print(f"\nMes de referencia: {today.strftime('%B/%Y')}\n")

    # Dia inicial
    start_day = _ask_int("Dia inicial do período:", default=1, min_val=1, max_val=31)

    # Dia final
    end_day = _ask_int("Dia final do período:", default=today.day, min_val=start_day, max_val=31)

    # Feriados
    holidays_input = inquirer.text(
        message="Dias de feriado (separados por vírgula, ou vazio):",
        default="",
    ).execute()

    holidays: list[int] = []
    if holidays_input.strip():
        holidays = [int(d.strip()) for d in holidays_input.split(",") if d.strip()]

    # Total de horas
    total_hours = _ask_float("Total de horas a lançar no mês:", default=160)

    # Confirmar modo dry-run
    dry_run = inquirer.confirm(
        message="Executar em modo DRY-RUN (sem automação web)?",
        default=False,
    ).execute()

    return {
        "start_day": start_day,
        "end_day": end_day,
        "holidays": holidays,
        "total_hours": total_hours,
        "month": current_month,
        "year": current_year,
        "dry_run": dry_run,
    }
