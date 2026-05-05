"""
automation.py — Módulo de automação web com Playwright.

Preenche o formulário de lançamento de ponto no sistema pmdecision.
"""

from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout
from rich.console import Console

from calculator import TimeEntry

console = Console()

# Seletores DOM
SELECTORS = {
    "dia": "input#Dia",
    "hora_inicio": "input#HoraInicio",
    "hora_termino": "input#HoraTermino",
    "tipo_atividade": "select#TipoAtividadeId",
    "detalhamento": "textarea#Detalhamento",
    "submit": "button[type='submit'].btn.btn-default.fd-btn-form",
}

URL = "https://app.firstdecision.com.br/pmdecision/Lancamento/Create"
TIPO_ATIVIDADE_VALUE = "2117"  # Desenvolvimento
DETALHAMENTO_TEXT = "Implementação do Sigesa 2.0."


def _wait_for_form_ready(page: Page, timeout: int = 30000) -> None:
    """Aguarda o formulário estar pronto para preenchimento."""
    page.wait_for_selector(SELECTORS["dia"], state="visible", timeout=timeout)
    page.wait_for_selector(SELECTORS["hora_inicio"], state="visible", timeout=timeout)
    page.wait_for_selector(SELECTORS["submit"], state="visible", timeout=timeout)


def _clear_and_fill(page: Page, selector: str, value: str) -> None:
    """Limpa o campo e preenche com o valor fornecido."""
    element = page.locator(selector)
    element.click()
    element.fill("")
    element.fill(value)


def _handle_post_submit(page: Page) -> None:
    """
    Trata o estado após clicar em salvar.
    Aguarda possíveis alertas/modais e espera o formulário ficar pronto.
    """
    # Aguardar um breve momento para possíveis alertas ou redirecionamentos
    page.wait_for_load_state("networkidle", timeout=10000)

    # Tentar fechar modais de sucesso se existirem
    try:
        # Tenta fechar modal Bootstrap se houver
        close_btn = page.locator(".modal .close, .modal .btn-close, .modal .btn-default")
        if close_btn.count() > 0 and close_btn.first.is_visible():
            close_btn.first.click()
            page.wait_for_timeout(500)
    except Exception:
        pass  # Sem modal, segue normalmente

    # Aguardar o formulário estar pronto para o próximo lançamento
    _wait_for_form_ready(page, timeout=15000)


def _fill_entry(page: Page, entry: TimeEntry, index: int, total: int) -> None:
    """Preenche um único lançamento no formulário."""
    day_str = f"{entry.day:02d}"
    start_str = entry.start_str
    end_str = entry.end_str

    console.print(
        f"  ... [{index}/{total}] Dia {day_str} | {entry.period} | "
        f"{start_str} – {end_str} ({entry.duration_str})"
    )

    # Preencher Dia
    _clear_and_fill(page, SELECTORS["dia"], day_str)

    # Preencher Hora de Início
    _clear_and_fill(page, SELECTORS["hora_inicio"], start_str)

    # Preencher Hora de Término
    _clear_and_fill(page, SELECTORS["hora_termino"], end_str)

    # Selecionar Tipo de Atividade = Desenvolvimento
    page.locator(SELECTORS["tipo_atividade"]).select_option(value=TIPO_ATIVIDADE_VALUE)

    # Preencher Detalhamento
    _clear_and_fill(page, SELECTORS["detalhamento"], DETALHAMENTO_TEXT)

    # Clicar em Salvar
    page.locator(SELECTORS["submit"]).click()

    console.print(
        f"  [bold green][OK] [{index}/{total}] Dia {day_str} | {entry.period} -- Salvo![/bold green]"
    )


def run(entries: list[TimeEntry]) -> None:
    """
    Executa a automação completa no navegador.

    O browser abre em modo headed e pausa para o usuário fazer login.
    Após detectar o formulário, inicia os lançamentos automaticamente.
    """
    total = len(entries)

    console.print("\n[bold cyan]Iniciando automacao web...[/bold cyan]\n")
    console.print(f"   Total de lançamentos: [bold]{total}[/bold]")
    console.print(f"   URL: {URL}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # Navegar para a página de lançamento
        page.goto(URL, wait_until="domcontentloaded")

        console.print(
            "[bold yellow][!] Faca login no sistema manualmente.[/bold yellow]"
        )
        console.print(
            "[bold yellow]   Após o login, navegue até a página de criação de lançamento.[/bold yellow]"
        )
        console.print(
            "[bold yellow]   O script detectará o formulário e iniciará automaticamente.\n[/bold yellow]"
        )

        # Aguardar o formulário ficar disponível (após login manual)
        try:
            _wait_for_form_ready(page, timeout=300000)  # 5 minutos para login
        except PlaywrightTimeout:
            console.print("[bold red][ERRO] Timeout aguardando login. Encerrando.[/bold red]")
            browser.close()
            return

        console.print("[bold green][OK] Formulario detectado! Iniciando lancamentos...\n[/bold green]")

        # Registrar handler de dialogs JS uma unica vez (aceita alertas automaticamente)
        page.on("dialog", lambda dialog: dialog.accept())

        # Garantir formulário limpo navegando para a URL de criação
        page.goto(URL, wait_until="domcontentloaded")
        _wait_for_form_ready(page, timeout=15000)

        # Processar cada lançamento
        for idx, entry in enumerate(entries, start=1):
            try:
                _fill_entry(page, entry, idx, total)
                _handle_post_submit(page)
            except PlaywrightTimeout as e:
                console.print(
                    f"[bold red][ERRO] Timeout no lancamento {idx}/{total} "
                    f"(Dia {entry.day:02d} {entry.period}): {e}[/bold red]"
                )
                console.print("[yellow]   Tentando continuar...[/yellow]")
                try:
                    page.goto(URL, wait_until="domcontentloaded")
                    _wait_for_form_ready(page, timeout=15000)
                except Exception:
                    console.print("[bold red]   Falha ao recuperar. Pulando...[/bold red]")
                    continue
            except Exception as e:
                console.print(
                    f"[bold red][ERRO] Erro inesperado no lancamento {idx}/{total}: {e}[/bold red]"
                )
                continue

        console.print(
            f"\n[bold green]Automacao finalizada! "
            f"{total} lançamentos processados.[/bold green]\n"
        )

        # Manter browser aberto para conferência manual
        console.print("[dim]Pressione ENTER para fechar o navegador...[/dim]")
        input()
        browser.close()
