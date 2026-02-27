# PontoFirst

Automacao de registro de ponto no sistema **pmdecision** (First Decision).
Gera lancamentos com horarios variados e preenche o formulario web automaticamente via Playwright.

## Requisitos

- Python 3.10+
- Google Chrome (instalado automaticamente pelo Playwright)

## Instalacao

```bash
# Clonar o repositorio
git clone https://github.com/seu-usuario/PontoFirst.git
cd PontoFirst

# Instalar dependencias
pip install -r requirements.txt

# Instalar o browser (apenas na primeira vez)
python -m playwright install chromium
```

## Uso

```bash
python -m src.main
```

O script ira solicitar:

| Parametro | Descricao | Exemplo |
|-----------|-----------|---------|
| Dia inicial | Primeiro dia do periodo | `1` |
| Dia final | Ultimo dia do periodo | `28` |
| Feriados | Dias de feriado (separados por virgula) | `3,17,25` |
| Total de horas | Carga horaria total do mes | `160` |
| Dry-run | Exibir tabela sem automacao web | `Sim/Nao` |

Apos preencher os dados, o script:

1. Calcula os horarios para cada dia util
2. Exibe uma tabela formatada no console para conferencia
3. Solicita confirmacao antes de iniciar a automacao
4. Abre o navegador e aguarda o login manual
5. Preenche os lancamentos automaticamente

## Logica de Distribuicao de Horas

- O total de horas e dividido igualmente entre os dias uteis do periodo
- Sabados, domingos e feriados sao excluidos automaticamente
- Cada dia gera **2 lancamentos**: manha e tarde
- Horarios base com variacao aleatoria de +/- 20 minutos:
  - Entrada: ~09:00
  - Almoco (saida): ~12:00
  - Retorno: ~13:00 (minimo 1h de intervalo garantido)
  - Saida: calculada para atingir o total do dia
- O ultimo dia util e ajustado para que a soma total bata **exatamente** com o target

## Estrutura do Projeto

```
PontoFirst/
├── requirements.txt          # Dependencias (Playwright, InquirerPy, Rich)
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py               # Entry point e orquestracao
│   ├── cli.py                # Entrada de dados via terminal
│   ├── calculator.py         # Calculo e distribuicao de horas
│   └── automation.py         # Automacao web com Playwright
└── tests/
    ├── __init__.py
    └── test_calculator.py    # Testes unitarios
```

## Mapeamento de Elementos (DOM)

| Campo | Seletor |
|-------|---------|
| Dia | `input#Dia` |
| Hora de Inicio | `input#HoraInicio` |
| Hora de Termino | `input#HoraTermino` |
| Tipo de Atividade | `select#TipoAtividadeId` (value: 2117) |
| Detalhamento | `textarea#Detalhamento` |
| Salvar | `button[type="submit"].btn.btn-default.fd-btn-form` |

## Testes

```bash
python -m pytest tests/ -v
```

Os testes validam:

- Soma total exata para multiplos valores de horas (80h, 120h, 160h, 176h, 200h)
- Dois lancamentos por dia (manha + tarde)
- Horarios nao-redondos (variacao aleatoria)
- Exclusao correta de feriados e fins de semana
- Horarios dentro do expediente
- Consistencia em execucoes consecutivas

## Tecnologias

- **Python 3** — Linguagem principal
- **Playwright** — Automacao web com waits inteligentes
- **InquirerPy** — Prompts interativos no terminal
- **Rich** — Tabelas formatadas e coloridas no console

## Licenca

MIT
