# Sistema de Agendamentos - Projeto Impacta

Projeto acadêmico desenvolvido durante o curso de Análise e Desenvolvimento de Sistemas (ADS) na Faculdade Impacta.

## Descrição

Sistema web para gerenciamento de agendamentos e CRM (Customer Relationship Management), com interface em HTML e back-end em Python.

## Funcionalidades

- Tela inicial (Home)
- Criação e visualização de agendamentos
- Gerenciamento de fila de atendimento
- CRM básico para controle de clientes

## Tecnologias Utilizadas

- **HTML5** — Estrutura das páginas web
- **Python** — Lógica de back-end e CRM
- **SQLite** — Armazenamento de dados (instância local)

## Estrutura do Projeto

```
impacta/
├── home.html            # Página inicial
├── agendar.html         # Formulário de agendamento
├── agendamentos.html    # Listagem de agendamentos
├── fila.html            # Gerenciamento de fila
├── crm.py               # Lógica de CRM em Python
├── instance/            # Banco de dados local
└── diagram.jpg          # Diagrama do sistema
```

## Como Executar

1. Clone o repositório:
   ```bash
   git clone https://github.com/gusjmo/impacta.git
   ```
2. Execute o back-end Python:
   ```bash
   python crm.py
   ```
3. Abra o arquivo `home.html` no navegador.

## Autor

**Gustavo Juvencio** — [@gusjmo](https://github.com/gusjmo)

Estudante de ADS | São Paulo, SP
