# Sabor de Goiás

Sistema de gestão para restaurante com interface desktop feita em **Python + Flet** e banco de dados **PostgreSQL**.

Projeto em desenvolvimento, criado em formato de estudo, passo a passo.

## Tecnologias

- Python 3.14
- [Flet](https://flet.dev) (interface)
- PostgreSQL 18
- psycopg 3 (conexão com o banco)

## Funcionalidades

- [x] Tela inicial com cards clicáveis que levam às seções
- [x] Menu lateral que acompanha a navegação (inclusive quando o clique vem dos cards)
- [x] Barra superior colorida (AppBar)
- [x] Cadastro de clientes
  - [x] Máscara de telefone (`62 98761-1234`)
  - [x] E-mail único (restrição `UNIQUE` no banco)
  - [x] Validação de campos obrigatórios
  - [x] Mensagens coloridas de sucesso e erro
- [x] Cadastro de funcionários
- [ ] Cargo como lista fixa (Dropdown) para padronizar os dados
- [ ] Listagem de clientes e funcionários
- [ ] Editar e excluir registros
- [ ] Telas de Produtos, Mesas e Pedidos

## Estrutura do projeto

```
sistema_restaurante/
├── .gitignore
└── restaurante_app/
    ├── main.py              # janela, menu lateral e navegação entre telas
    ├── conexao.py           # conexão com o PostgreSQL (não vai para o GitHub)
    └── views/
        ├── __init__.py
        ├── clientes.py      # tela de cadastro de clientes
        └── funcionarios.py  # tela de cadastro de funcionários
```

## Banco de dados

Banco: `restaurante`, com as tabelas:

| Tabela | Colunas |
|---|---|
| `cliente` | `id_cliente`, `nome`, `telefone`, `email` (único) |
| `funcionario` | `id_funcionario`, `nome`, `cargo` |
| `produto` | `id_produto`, `nome`, `categoria`, `preco` |
| `mesa` | `id_mesa`, `numero_mesa`, `status` |
| `pedido` | `id_pedido`, `data_horario`, `valor_total`, `id_cliente`, `id_funcionario`, `id_mesa` |
| `item_pedido` | `id_pedido`, `id_produto`, `quantidade`, `preco_unitario` |

Restrição de e-mail único:

```sql
ALTER TABLE cliente ADD CONSTRAINT uq_cliente_email UNIQUE (email);
```

## Como rodar

1. Clone o repositório e entre na pasta do projeto.
2. Crie e ative o ambiente virtual:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instale as dependências:

```bash
pip install flet "psycopg[binary]"
```

4. Crie o arquivo `restaurante_app/conexao.py` (ele não vem no repositório porque contém a senha do banco):

```python
import psycopg

def conectar():
    return psycopg.connect(
        host='localhost',
        port='SUA_PORTA',
        dbname='restaurante',
        user='SEU_USUARIO',
        password='SUA_SENHA'
    )
```

5. Execute a partir da pasta `restaurante_app`:

```bash
cd restaurante_app
flet run main.py
```

## Diário de desenvolvimento

Passos já feitos, na ordem.

### 1. Estrutura e tela de clientes
- Criada a pasta `views` com `__init__.py` e o arquivo `clientes.py`.
- Função `clientes_view(page)` devolve uma `Column` com os campos e o botão.
- Layout centralizado com `alignment`, `horizontal_alignment` e `expand=True`.

### 2. Navegação
- Função `mostrar_tela(selecionado)` troca o conteúdo da página conforme a opção escolhida.
- A lista `opcoes` guarda os nomes das seções, e `menu.selected_index` é atualizado com `opcoes.index(...)`.
- Os cards da tela inicial usam `on_click=lambda e: mostrar_tela(titulo)`.

### 3. Cadastro de clientes no banco
- Campos guardados em variáveis para ler o texto com `.value`.
- Função `cadastrar(e)` dentro de `clientes_view`.
- `INSERT` com parâmetros (`%s`) para evitar SQL injection.
- `try/except` para não derrubar o app quando o banco recusa um dado.
- `SnackBar` verde-água (sucesso) e vermelho (erro).

### 4. Regras e acabamento
- E-mail único no banco.
- Máscara de telefone com o evento `on_change`.
- AppBar verde-água, ícones nos campos (`prefix`) e botão estilizado (`ButtonStyle`).

### 5. Cadastro de funcionários
- Arquivo `views/funcionarios.py` seguindo o mesmo molde do cadastro de clientes.
- Cargos já gravados foram padronizados no banco com `UPDATE`.

### 6. Publicação no GitHub
- `.gitignore` protegendo `venv/`, `__pycache__/`, `.flet/`, `.env` e `conexao.py`.
- Repositório criado com `git init`, `git add`, `git commit` e `git push`.
