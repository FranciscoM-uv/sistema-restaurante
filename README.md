# Sabor de Goiás

Sistema de gestão para restaurante, com cadastro de clientes e funcionários, mapa de mesas com reservas e controle de comandas.

## Tecnologias

- Python 3.14
- [Flet](https://flet.dev) (interface)
- PostgreSQL 18
- psycopg 3 (conexão com o banco)

## Funcionalidades

- [x] Tela inicial com cards clicáveis que levam às seções
- [x] Menu lateral que acompanha a navegação (inclusive quando o clique vem dos cards)
- [x] Barra superior colorida (AppBar)

**Clientes**
- [x] Cadastro com máscara de telefone (`62 98761-1234`)
- [x] E-mail único (restrição `UNIQUE` no banco)
- [x] Validação de campos obrigatórios
- [x] Mensagens coloridas de sucesso e erro
- [x] Consulta por nome ou telefone, sem diferenciar maiúsculas de minúsculas, com sugestões ao digitar
- [x] Edição de cadastro
- [x] Lista de clientes com comanda aberta, com a(s) mesa(s) de cada um
- [x] Abertura de comanda em uma ou mais mesas (mesas juntadas)
- [x] Fechamento de comanda

**Mesas**
- [x] Mapa de mesas com status calculado automaticamente: Livre, Ocupada ou Reservada
- [x] Capacidade por mesa
- [x] Cadastro de novas mesas
- [x] Reservas com validação de capacidade, data e hora
- [x] Cancelamento de reservas

**Funcionários**
- [x] Cadastro com cargo em lista fixa (Dropdown)
- [x] Mudança de cargo com motivo
- [x] Demissão sem apagar o registro (histórico preservado) e readmissão
- [x] Histórico de admissão, mudanças de cargo, demissão e readmissão
- [x] Autorização por PIN de gerente (PIN guardado com hash e salt)
- [x] Trava para o último gerente ativo e para alterar o próprio cargo

**Em desenvolvimento**
- [ ] Tela de Produtos
- [ ] Tela de Pedidos
- [ ] Login por usuário e senha, com permissões por cargo
- [ ] Eventos (aniversário, casamento, confraternização) ligados a reservas
- [ ] Excluir clientes (hoje só é possível editar)

## Estrutura do projeto

```
sistema_restaurante/
├── .gitignore
├── README.md
└── restaurante_app/
    ├── main.py            # janela, menu lateral e navegação entre telas
    ├── conexao.py         # conexão com o PostgreSQL (não vai para o Git)
    ├── .env               # credenciais do banco (não vai para o Git)
    └── views/
        ├── __init__.py
        ├── clientes.py    # cadastro, lista de comandas abertas e consulta
        ├── funcionarios.py# cadastro, equipe, cargos, demissão e histórico
        ├── mesas.py       # mapa de mesas, reservas e nova mesa
        └── produtos.py    # em desenvolvimento
```

## Banco de dados

Tabelas principais:

| Tabela | Função |
|---|---|
| `cliente` | Dados dos clientes |
| `funcionario` | Equipe, com cargo, situação (`ativo`) e `pin_hash` |
| `funcionario_historico` | Registro de admissões, mudanças de cargo e demissões |
| `mesa` | Número e capacidade das mesas |
| `comanda` | Contas dos clientes, com status `aberta` ou `fechada` |
| `comanda_mesa` | Liga uma comanda a uma ou mais mesas |
| `reserva` | Reservas de mesas com data e hora |

O status de cada mesa não é digitado: ele é calculado a partir das comandas abertas e das reservas ativas.

## Como rodar

1. Clone o repositório e entre na pasta do app:

   ```powershell
   git clone https://github.com/FranciscoM-uv/sistema-restaurante.git
   cd sistema-restaurante/restaurante_app
   ```

2. Crie e ative o ambiente virtual:

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. Instale as dependências:

   ```powershell
   pip install flet "psycopg[binary]" python-dotenv
   ```

4. Crie o banco `restaurante` no PostgreSQL e as tabelas listadas acima.

5. Crie o arquivo `.env` em `restaurante_app/` com os dados do seu banco e o arquivo `conexao.py`, que como ficam fora do Git, precisam ser criados em cada máquina.

6. Execute:

   ```powershell
   flet run main.py
   ```

## Regras e acabamento

- E-mail único no banco.
- Máscara de telefone com o evento `on_change`.
- Funcionários nunca são apagados: a demissão apenas desativa o cadastro.
- AppBar verde-água, ícones nos campos (`prefix`) e botões estilizados (`ButtonStyle`).
