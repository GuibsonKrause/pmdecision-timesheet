"""
test_calculator.py — Testes unitários para a lógica de cálculo de horas.

Valida que a soma dos lançamentos bate exatamente com o total informado
e que a jornada diária respeita o intervalo [7h50, 8h10].
"""

import pytest
from src.calculator import (
    generate_time_entries, _get_working_days,
    MIN_DAY_MINUTES, MAX_DAY_MINUTES,
)
from datetime import date


class TestGetWorkingDays:
    """Testes para a função _get_working_days."""

    def test_excludes_weekends(self):
        # Fevereiro de 2026 começa numa Domingo
        days = _get_working_days(2026, 2, 1, 28, [])
        for d in days:
            assert d.weekday() < 5, f"{d} é fim de semana!"

    def test_excludes_holidays(self):
        holidays = [3, 17]  # dias de feriado
        days = _get_working_days(2026, 2, 1, 28, holidays)
        day_numbers = [d.day for d in days]
        assert 3 not in day_numbers
        assert 17 not in day_numbers

    def test_respects_range(self):
        days = _get_working_days(2026, 2, 10, 20, [])
        for d in days:
            assert 10 <= d.day <= 20

    def test_empty_range_raises_no_error(self):
        # Intervalo de um fim de semana (sáb e dom)
        days = _get_working_days(2026, 2, 7, 8, [])  # 7/2/2026 = sáb, 8 = dom
        assert len(days) == 0


class TestGenerateTimeEntries:
    """Testes para a geração de lançamentos de ponto."""

    @pytest.mark.parametrize("total_hours", [157, 158, 160, 162, 163])
    def test_total_matches_exactly(self, total_hours):
        """A soma total dos minutos DEVE bater exatamente com o target."""
        # Fev/2026: 20 dias úteis → viável de ~156.7h a ~163.3h
        entries = generate_time_entries(
            year=2026, month=2,
            start_day=1, end_day=28,
            holidays=[],
            total_hours=total_hours,
        )
        total_minutes = sum(e.duration_minutes for e in entries)
        assert total_minutes == total_hours * 60, (
            f"Total gerado: {total_minutes} min, esperado: {total_hours * 60} min"
        )

    def test_two_entries_per_day(self):
        """Cada dia útil deve ter exatamente 2 lançamentos (manhã e tarde)."""
        entries = generate_time_entries(
            year=2026, month=2,
            start_day=1, end_day=28,
            holidays=[],
            total_hours=160,
        )
        days = set(e.day for e in entries)
        for day in days:
            day_entries = [e for e in entries if e.day == day]
            assert len(day_entries) == 2, f"Dia {day} tem {len(day_entries)} lançamentos"
            periods = [e.period for e in day_entries]
            assert "Manhã" in periods
            assert "Tarde" in periods

    def test_daily_duration_within_range(self):
        """Cada dia deve ter entre 7h50 (470min) e 8h10 (490min)."""
        entries = generate_time_entries(
            year=2026, month=2,
            start_day=1, end_day=28,
            holidays=[],
            total_hours=160,
        )
        days = set(e.day for e in entries)
        for day in days:
            day_entries = [e for e in entries if e.day == day]
            day_total = sum(e.duration_minutes for e in day_entries)
            assert MIN_DAY_MINUTES <= day_total <= MAX_DAY_MINUTES, (
                f"Dia {day}: {day_total} min fora do intervalo "
                f"[{MIN_DAY_MINUTES}, {MAX_DAY_MINUTES}]"
            )

    def test_no_exact_round_times(self):
        """Horários não devem ser redondos (00 ou 30 em todos)."""
        entries = generate_time_entries(
            year=2026, month=2,
            start_day=1, end_day=28,
            holidays=[],
            total_hours=160,
        )
        # Pelo menos ALGUNS horários devem ter minutos diferentes de 00 e 30
        non_round = [
            e for e in entries
            if e.start_time.minute not in (0, 30) or e.end_time.minute not in (0, 30)
        ]
        assert len(non_round) > 0, "Todos os horários são redondos!"

    def test_holidays_are_excluded(self):
        """Dias de feriado não devem ter lançamentos."""
        holidays = [3, 17, 24]
        # 17 dias úteis (20 - 3 feriados em dia útil)
        # Faixa viável: ~133.2h a ~138.8h → usar 136
        entries = generate_time_entries(
            year=2026, month=2,
            start_day=1, end_day=28,
            holidays=holidays,
            total_hours=136,
        )
        entry_days = set(e.day for e in entries)
        for h in holidays:
            assert h not in entry_days, f"Feriado dia {h} tem lançamentos!"

    def test_times_are_within_business_hours(self):
        """Horários devem estar dentro de um intervalo razoável."""
        entries = generate_time_entries(
            year=2026, month=2,
            start_day=1, end_day=28,
            holidays=[],
            total_hours=160,
        )
        for e in entries:
            if e.period == "Manhã":
                assert 8 <= e.start_time.hour <= 9, (
                    f"Manhã início fora do horário: {e.start_str} (Dia {e.day})"
                )
                assert 11 <= e.end_time.hour <= 13, (
                    f"Manhã término fora do horário: {e.end_str} (Dia {e.day})"
                )
            else:  # Tarde
                assert 12 <= e.start_time.hour <= 13, (
                    f"Tarde início fora do horário: {e.start_str} (Dia {e.day})"
                )
                assert e.end_time.hour <= 22, (
                    f"Tarde término muito tarde: {e.end_str} (Dia {e.day})"
                )

    def test_empty_working_days_raises_error(self):
        """Se não houver dias úteis, deve lançar ValueError."""
        with pytest.raises(ValueError, match="Nenhum dia útil"):
            generate_time_entries(
                year=2026, month=2,
                start_day=7, end_day=8,  # sáb e dom
                holidays=[],
                total_hours=160,
            )

    def test_infeasible_total_raises_error(self):
        """Se o total não for viável com a restrição diária, deve lançar ValueError."""
        # 20 dias úteis, mas 80h = 240min/dia → abaixo de 470min
        with pytest.raises(ValueError, match="não é viável"):
            generate_time_entries(
                year=2026, month=2,
                start_day=1, end_day=28,
                holidays=[],
                total_hours=80,
            )

    def test_with_different_months(self):
        """Testar com meses de diferentes quantidades de dias."""
        # Janeiro/2026 com feriado dia 1: 21 dias úteis
        # Faixa viável: ~164.3h a ~171.5h → usar 168
        entries = generate_time_entries(
            year=2026, month=1,
            start_day=1, end_day=31,
            holidays=[1],  # Confraternização
            total_hours=168,
        )
        total_minutes = sum(e.duration_minutes for e in entries)
        assert total_minutes == 168 * 60

    def test_consistency_across_multiple_runs(self):
        """Múltiplas execuções devem sempre bater o total exato."""
        for _ in range(10):
            entries = generate_time_entries(
                year=2026, month=2,
                start_day=1, end_day=28,
                holidays=[],
                total_hours=160,
            )
            total_minutes = sum(e.duration_minutes for e in entries)
            assert total_minutes == 160 * 60

    def test_daily_range_across_multiple_runs(self):
        """Em múltiplas execuções, TODOS os dias devem respeitar [7h50, 8h10]."""
        for _ in range(10):
            entries = generate_time_entries(
                year=2026, month=2,
                start_day=1, end_day=28,
                holidays=[],
                total_hours=160,
            )
            days = set(e.day for e in entries)
            for day in days:
                day_entries = [e for e in entries if e.day == day]
                day_total = sum(e.duration_minutes for e in day_entries)
                assert MIN_DAY_MINUTES <= day_total <= MAX_DAY_MINUTES, (
                    f"Dia {day}: {day_total} min fora do intervalo"
                )
