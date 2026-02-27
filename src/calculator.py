"""
calculator.py — Lógica de cálculo e distribuição de horas.

Gera os lançamentos (manhã e tarde) para cada dia útil,
garantindo que a soma total bata EXATAMENTE com o target.
"""

import random
from dataclasses import dataclass
from datetime import date, time, timedelta
from rich.console import Console
from rich.table import Table


@dataclass
class TimeEntry:
    """Representa um lançamento de ponto (um turno)."""
    day: int
    date: date
    period: str          # "Manhã" ou "Tarde"
    start_time: time
    end_time: time
    duration_minutes: int

    @property
    def start_str(self) -> str:
        return self.start_time.strftime("%H:%M")

    @property
    def end_str(self) -> str:
        return self.end_time.strftime("%H:%M")

    @property
    def duration_str(self) -> str:
        h, m = divmod(self.duration_minutes, 60)
        return f"{h}:{m:02d}"


def _get_working_days(year: int, month: int, start_day: int, end_day: int,
                      holidays: list[int]) -> list[date]:
    """Retorna lista de dias úteis no intervalo (exclui sáb, dom, feriados)."""
    working_days = []
    for day_num in range(start_day, end_day + 1):
        try:
            d = date(year, month, day_num)
        except ValueError:
            continue  # dia inválido para o mês
        if d.weekday() >= 5:  # sábado=5, domingo=6
            continue
        if day_num in holidays:
            continue
        working_days.append(d)
    return working_days


def _minutes_to_time(base_hour: int, base_minute: int, offset_minutes: int) -> time:
    """Converte hora base + offset em um objeto time."""
    total = base_hour * 60 + base_minute + offset_minutes
    total = max(0, min(total, 23 * 60 + 59))  # clamp ao intervalo válido
    h, m = divmod(total, 60)
    return time(h, m)


def _total_minutes_from_time(t: time) -> int:
    return t.hour * 60 + t.minute


def generate_time_entries(
    year: int,
    month: int,
    start_day: int,
    end_day: int,
    holidays: list[int],
    total_hours: float,
) -> list[TimeEntry]:
    """
    Gera lançamentos de ponto com variação aleatória e soma exata.

    Algoritmo:
    1. Calcula minutos base por dia (total / dias_úteis).
    2. Divide cada dia em manhã (~metade) e tarde (~metade).
    3. Aplica variação aleatória nos horários.
    4. No último dia, ajusta para compensar a diferença acumulada.
    """
    working_days = _get_working_days(year, month, start_day, end_day, holidays)

    if not working_days:
        raise ValueError("Nenhum dia útil encontrado no intervalo informado.")

    total_minutes = int(total_hours * 60)
    num_days = len(working_days)
    base_minutes_per_day = total_minutes / num_days

    entries: list[TimeEntry] = []
    accumulated_minutes = 0

    for idx, work_date in enumerate(working_days):
        is_last_day = (idx == num_days - 1)
        remaining_days = num_days - idx

        if is_last_day:
            # Último dia: ajusta para bater exatamente
            day_minutes = total_minutes - accumulated_minutes
        else:
            # Variação de ±15 min na carga diária para parecer natural
            variation = random.randint(-15, 15)
            day_minutes = int(base_minutes_per_day) + variation

            # Garantir mínimo razoável por dia (pelo menos 4h) — somente dias não-últimos
            day_minutes = max(day_minutes, 240)

            # Garantir que não ultrapassa o orçamento restante
            # (deixar pelo menos 240 min para cada dia restante)
            remaining_after = total_minutes - accumulated_minutes - day_minutes
            min_needed_for_rest = (remaining_days - 1) * 240
            if remaining_after < min_needed_for_rest:
                day_minutes = total_minutes - accumulated_minutes - min_needed_for_rest

        # --- HORÁRIOS COM VARIAÇÃO DE ±20 MIN ---
        # Entrada: ~09:00
        morning_start_var = random.randint(-20, 20)
        morning_start = _minutes_to_time(9, 0, morning_start_var)
        morning_start_total = _total_minutes_from_time(morning_start)

        # Almoço (saída manhã): ~12:00
        morning_end_var = random.randint(-20, 20)
        morning_end = _minutes_to_time(12, 0, morning_end_var)
        morning_end_total = _total_minutes_from_time(morning_end)

        # Duração da manhã
        morning_minutes = morning_end_total - morning_start_total

        # Volta do almoço: ~13:00 (garantindo mínimo 1h de almoço)
        afternoon_start_var = random.randint(-20, 20)
        afternoon_start_total = 13 * 60 + afternoon_start_var
        # Se o intervalo ficaria menor que 60 min, ajustar
        if afternoon_start_total - morning_end_total < 60:
            afternoon_start_total = morning_end_total + 60
        afternoon_start = _minutes_to_time(0, 0, afternoon_start_total)

        # Duração da tarde = total do dia - manhã
        afternoon_minutes = day_minutes - morning_minutes

        # Saída: calculada para bater o total do dia
        afternoon_end_total = afternoon_start_total + afternoon_minutes
        afternoon_end = _minutes_to_time(0, 0, afternoon_end_total)

        entries.append(TimeEntry(
            day=work_date.day,
            date=work_date,
            period="Manhã",
            start_time=morning_start,
            end_time=morning_end,
            duration_minutes=morning_minutes,
        ))

        entries.append(TimeEntry(
            day=work_date.day,
            date=work_date,
            period="Tarde",
            start_time=afternoon_start,
            end_time=afternoon_end,
            duration_minutes=afternoon_minutes,
        ))

        accumulated_minutes += (morning_minutes + afternoon_minutes)

    return entries


def display_entries_table(entries: list[TimeEntry], total_hours: float) -> None:
    """Exibe tabela formatada no console para conferência."""
    console = Console()
    table = Table(
        title="Lancamentos de Ponto Gerados",
        show_lines=True,
        title_style="bold cyan",
    )

    table.add_column("Dia", style="bold white", justify="center", width=6)
    table.add_column("Data", style="dim", justify="center", width=12)
    table.add_column("Período", style="cyan", justify="center", width=8)
    table.add_column("Início", style="green", justify="center", width=8)
    table.add_column("Término", style="green", justify="center", width=8)
    table.add_column("Duração", style="yellow", justify="center", width=8)

    total_mins = 0
    for entry in entries:
        day_of_week = entry.date.strftime("%a")
        table.add_row(
            f"{entry.day:02d}",
            f"{entry.date.strftime('%d/%m')} ({day_of_week})",
            entry.period,
            entry.start_str,
            entry.end_str,
            entry.duration_str,
        )
        total_mins += entry.duration_minutes

    total_h, total_m = divmod(total_mins, 60)
    target_h, target_m = divmod(int(total_hours * 60), 60)

    table.add_section()
    match_symbol = "[OK]" if total_mins == int(total_hours * 60) else "[ERRO]"
    table.add_row(
        "", "", "",
        f"{match_symbol} TOTAL",
        f"{total_h}:{total_m:02d}",
        f"(target: {target_h}:{target_m:02d})",
    )

    console.print()
    console.print(table)
    console.print()

    if total_mins == int(total_hours * 60):
        console.print(
            f"[bold green][OK] Soma total confere: {total_h}:{total_m:02d} "
            f"== {target_h}:{target_m:02d}[/bold green]"
        )
    else:
        console.print(
            f"[bold red][ERRO] ATENCAO: Soma total ({total_h}:{total_m:02d}) "
            f"NÃO confere com o target ({target_h}:{target_m:02d})![/bold red]"
        )
