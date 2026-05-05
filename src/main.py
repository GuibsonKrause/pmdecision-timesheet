"""
main.py — Entry point da aplicação PontoFirst.

Orquestra: CLI → Cálculo → Conferência → Automação Web.
"""

import sys
from rich.console import Console

from cli import get_user_input
from calculator import generate_time_entries, display_entries_table
from automation import run as run_automation

console = Console()


def main():
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]   PontoFirst — Automação de Ponto     [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    # 1. Coletar dados do usuário
    try:
        user_input = get_user_input()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operação cancelada pelo usuário.[/yellow]")
        sys.exit(0)

    console.print(f"\n[dim]Configuração:[/dim]")
    console.print(f"  Período: {user_input['start_day']:02d}/{user_input['month']:02d} "
                  f"a {user_input['end_day']:02d}/{user_input['month']:02d}/{user_input['year']}")
    console.print(f"  Feriados: {user_input['holidays'] or 'Nenhum'}")
    console.print(f"  Total de horas: {user_input['total_hours']}h")
    console.print(f"  Modo: {'DRY-RUN' if user_input['dry_run'] else 'AUTOMACAO'}")

    # 2. Gerar lançamentos
    try:
        entries = generate_time_entries(
            year=user_input["year"],
            month=user_input["month"],
            start_day=user_input["start_day"],
            end_day=user_input["end_day"],
            holidays=user_input["holidays"],
            total_hours=user_input["total_hours"],
        )
    except ValueError as e:
        console.print(f"\n[bold red][ERRO] {e}[/bold red]")
        sys.exit(1)

    # 3. Exibir tabela para conferência
    display_entries_table(entries, user_input["total_hours"])

    # 4. Confirmar antes de prosseguir
    if user_input["dry_run"]:
        console.print("[bold yellow]Modo DRY-RUN: automacao web nao sera executada.[/bold yellow]\n")
        sys.exit(0)

    console.print("\n[bold yellow][!] Confira a tabela acima antes de prosseguir![/bold yellow]")
    confirm = input("Deseja iniciar a automação web? (s/N): ").strip().lower()

    if confirm not in ("s", "sim", "y", "yes"):
        console.print("[yellow]Operação cancelada.[/yellow]")
        sys.exit(0)

    # 5. Executar automação
    run_automation(entries)


if __name__ == "__main__":
    main()
