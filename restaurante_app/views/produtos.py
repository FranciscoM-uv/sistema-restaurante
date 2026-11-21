from decimal import Decimal, InvalidOperation

import flet as ft
from conexao import conectar
from views.funcionarios import com_autorizacao

CATEGORIAS = ['Prato', 'Bebida', 'Sobremesa']


def formatar_preco(valor):
    texto = f'{Decimal(str(valor)):,.2f}'
    return 'R$ ' + texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def ler_preco(texto):
    try:
        valor = Decimal((texto or '').replace(',', '.')).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None
    return valor if valor > 0 else None


def buscar_produtos(busca, categoria, mostrar_inativos):
    sql = '''
        SELECT id_produto, nome, categoria, preco, ativo
        FROM produto
        WHERE LOWER(nome) LIKE LOWER(%s)
    '''
    params = [f'%{busca}%']

    if not mostrar_inativos:
        sql += ' AND ativo'
    if categoria:
        sql += ' AND categoria = %s'
        params.append(categoria)

    sql += ' ORDER BY ativo DESC, categoria, nome'

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def inserir_produto(nome, categoria, preco, id_aut):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO produto(nome, categoria, preco)
                VALUES (%s, %s, %s)
                RETURNING id_produto
                ''',
                (nome, categoria, preco)
            )
            id_produto = cursor.fetchone()[0]
            cursor.execute(
                '''
                INSERT INTO produto_preco_historico(id_produto, preco_novo, autorizado_por)
                VALUES (%s, %s, %s)
                ''',
                (id_produto, preco, id_aut)
            )


def atualizar_produto(id_produto, nome, categoria, preco, id_aut):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                'SELECT preco FROM produto WHERE id_produto = %s FOR UPDATE',
                (id_produto,)
            )
            preco_atual = Decimal(str(cursor.fetchone()[0])).quantize(Decimal('0.01'))

            cursor.execute(
                '''
                UPDATE produto
                SET nome = %s, categoria = %s, preco = %s
                WHERE id_produto = %s
                ''',
                (nome, categoria, preco, id_produto)
            )

            if preco != preco_atual:
                cursor.execute(
                    '''
                    INSERT INTO produto_preco_historico
                        (id_produto, preco_anterior, preco_novo, autorizado_por)
                    VALUES (%s, %s, %s, %s)
                    ''',
                    (id_produto, preco_atual, preco, id_aut)
                )


def alterar_situacao(id_produto, ativo):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                'UPDATE produto SET ativo = %s WHERE id_produto = %s',
                (ativo, id_produto)
            )


def buscar_historico_preco(id_produto):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                SELECT h.preco_anterior, h.preco_novo, h.alterado_em, f.nome
                FROM produto_preco_historico h
                LEFT JOIN funcionario f ON f.id_funcionario = h.autorizado_por
                WHERE h.id_produto = %s
                ORDER BY h.alterado_em DESC
                ''',
                (id_produto,)
            )
            return cursor.fetchall()


def snack(page, texto, cor='#168C8C'):
    page.show_dialog(ft.SnackBar(content=ft.Text(texto, color='white'), bgcolor=cor))


def campo_preco(label='Preço', valor='', largura=400):
    return ft.TextField(
        label=label,
        value=valor,
        prefix=ft.Icon(ft.Icons.ATTACH_MONEY, color='#168C8C'),
        hint_text='Digite o preço',
        input_filter=ft.InputFilter(
            allow=True,
            regex_string=r'^[0-9]*[.,]?[0-9]{0,2}$',
            replacement_string=''
        ),
        width=largura
    )


def cadastro_produtos(page, recarregar_cardapio):
    nome_produto = ft.TextField(
        label='Nome do produto',
        prefix=ft.Icon(ft.Icons.RESTAURANT_MENU, color='#168C8C'),
        hint_text='Digite o nome do produto',
        width=400
    )
    categoria_produto = ft.Dropdown(
        label='Categoria',
        options=[ft.DropdownOption(c) for c in CATEGORIAS],
        width=400
    )
    preco_produto = campo_preco()

    def cadastrar(e):
        nome = nome_produto.value.strip().title()
        preco = ler_preco(preco_produto.value)

        if not nome or not categoria_produto.value or not preco_produto.value:
            snack(page, 'Preencha nome, categoria e preço', '#E65100')
            return
        if preco is None:
            snack(page, 'Informe um preço válido, maior que zero', '#E65100')
            return

        try:
            inserir_produto(nome, categoria_produto.value, preco, None)
        except Exception:
            snack(page, 'Já existe um produto com esse nome nessa categoria', '#C62828')
            return

        nome_produto.value = ''
        categoria_produto.value = None
        preco_produto.value = ''
        snack(page, 'Produto cadastrado com sucesso')
        page.update()
        recarregar_cardapio()

    return ft.Column(
        controls=[
            ft.Text('Cadastro de Produtos', size=30,
                    weight=ft.FontWeight.BOLD, color='#172B4D'),
            nome_produto,
            categoria_produto,
            preco_produto,
            ft.Button(
                content=ft.Text('Cadastrar'),
                on_click=cadastrar,
                style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15
    )


def cardapio_produtos(page):
    busca = ft.TextField(
        label='Buscar produto',
        prefix=ft.Icon(ft.Icons.SEARCH, color='#168C8C'),
        width=260
    )
    filtro_categoria = ft.Dropdown(
        label='Categoria',
        value='Todas',
        options=[ft.DropdownOption(key='Todas', text='Todas')]
                + [ft.DropdownOption(key=c, text=c) for c in CATEGORIAS],
        width=180
    )
    mostrar_inativos = ft.Switch(label='Mostrar descontinuados', value=False)

    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text('Produto')),
            ft.DataColumn(label=ft.Text('Categoria')),
            ft.DataColumn(label=ft.Text('Preço')),
            ft.DataColumn(label=ft.Text('Situação')),
            ft.DataColumn(label=ft.Text('Ações')),
        ],
        rows=[]
    )
    vazio = ft.Text('Nenhum produto encontrado.', color='#6B778C')

    def abrir_edicao(id_produto, nome, categoria, preco):
        preco_atual = Decimal(str(preco)).quantize(Decimal('0.01'))

        campo_nome = ft.TextField(label='Nome', value=nome, width=350)
        campo_categoria = ft.Dropdown(
            label='Categoria',
            value=categoria if categoria in CATEGORIAS else None,
            options=[ft.DropdownOption(c) for c in CATEGORIAS],
            width=350
        )
        campo_novo_preco = campo_preco(valor=str(preco_atual).replace('.', ','), largura=350)

        def salvar(ev):
            novo_nome = campo_nome.value.strip().title()
            novo_preco = ler_preco(campo_novo_preco.value)

            if not novo_nome or not campo_categoria.value:
                snack(page, 'Preencha nome e categoria', '#C62828')
                return
            if novo_preco is None:
                snack(page, 'Informe um preço válido, maior que zero', '#C62828')
                return

            nova_categoria = campo_categoria.value
            page.pop_dialog()

            def executar(id_aut):
                try:
                    atualizar_produto(id_produto, novo_nome, nova_categoria,
                                      novo_preco, id_aut)
                except Exception:
                    snack(page, 'Já existe um produto com esse nome nessa categoria',
                          '#C62828')
                    return
                snack(page, 'Produto atualizado')
                recarregar()

            if novo_preco != preco_atual:
                com_autorizacao(page, 'Autorizar mudança de preço', executar,
                                obrigatorio=False)
            else:
                executar(None)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text('Editar produto'),
            content=ft.Column(
                tight=True,
                spacing=15,
                controls=[campo_nome, campo_categoria, campo_novo_preco,
                          ft.Text('Mudar o preço pede o PIN do gerente.', size=12,
                                  color='#6B778C')]
            ),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(content=ft.Text('Salvar'), on_click=salvar,
                          style=ft.ButtonStyle(bgcolor='#168C8C', color='white')),
            ]
        ))

    def abrir_descontinuar(id_produto, nome):
        def confirmar(ev):
            page.pop_dialog()

            def executar(id_aut):
                try:
                    alterar_situacao(id_produto, False)
                except Exception:
                    snack(page, 'Erro ao descontinuar o produto', '#C62828')
                    return
                snack(page, f'{nome} saiu do cardápio')
                recarregar()

            com_autorizacao(page, 'Autorizar descontinuação', executar, obrigatorio=False)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Descontinuar {nome}?'),
            content=ft.Text('O produto sai do cardápio, mas os pedidos antigos continuam '
                            'com ele. Dá para reativar depois.'),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(content=ft.Text('Descontinuar'), on_click=confirmar,
                          style=ft.ButtonStyle(bgcolor='#C62828', color='white')),
            ]
        ))

    def reativar(id_produto, nome):
        try:
            alterar_situacao(id_produto, True)
        except Exception:
            snack(page, 'Erro ao reativar o produto', '#C62828')
            return
        snack(page, f'{nome} voltou ao cardápio')
        recarregar()

    def abrir_historico(id_produto, nome):
        itens = []

        for anterior, novo, quando, autorizador in buscar_historico_preco(id_produto):
            if anterior is None:
                detalhe = f'Preço inicial: {formatar_preco(novo)}'
            else:
                detalhe = f'{formatar_preco(anterior)} → {formatar_preco(novo)}'

            linhas = [
                ft.Text(f'{quando:%d/%m/%Y %H:%M}', weight=ft.FontWeight.BOLD,
                        color='#168C8C'),
                ft.Text(detalhe),
            ]
            if autorizador:
                linhas.append(ft.Text(f'Autorizado por: {autorizador}', size=13,
                                      color='#6B778C'))

            itens.append(ft.Column(spacing=2, controls=linhas))
            itens.append(ft.Divider(height=1))

        if not itens:
            itens.append(ft.Text('Sem registros.'))

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f'Histórico de preço: {nome}'),
            content=ft.Column(width=380, height=300, scroll=ft.ScrollMode.AUTO,
                              spacing=10, controls=itens),
            actions=[ft.TextButton('Fechar', on_click=lambda ev: page.pop_dialog())]
        ))

    def montar_linhas():
        categoria = None if filtro_categoria.value in (None, 'Todas') else filtro_categoria.value
        linhas = []

        for id_produto, nome, cat, preco, ativo in buscar_produtos(
                busca.value.strip(), categoria, mostrar_inativos.value):

            acoes = [
                ft.IconButton(
                    icon=ft.Icons.HISTORY,
                    icon_color='#6B778C',
                    tooltip='Histórico de preço',
                    on_click=lambda e, i=id_produto, n=nome: abrir_historico(i, n)
                )
            ]

            if ativo:
                acoes.insert(0, ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color='#168C8C',
                    tooltip='Editar',
                    on_click=lambda e, i=id_produto, n=nome, c=cat, p=preco:
                        abrir_edicao(i, n, c, p)
                ))
                acoes.append(ft.IconButton(
                    icon=ft.Icons.BLOCK,
                    icon_color='#C62828',
                    tooltip='Descontinuar',
                    on_click=lambda e, i=id_produto, n=nome: abrir_descontinuar(i, n)
                ))
                situacao, cor_situacao = 'No cardápio', '#168C8C'
            else:
                acoes.insert(0, ft.IconButton(
                    icon=ft.Icons.REPLAY,
                    icon_color='#168C8C',
                    tooltip='Reativar',
                    on_click=lambda e, i=id_produto, n=nome: reativar(i, n)
                ))
                situacao, cor_situacao = 'Descontinuado', '#C62828'

            linhas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(nome)),
                        ft.DataCell(ft.Text(cat)),
                        ft.DataCell(ft.Text(formatar_preco(preco))),
                        ft.DataCell(ft.Text(situacao, color=cor_situacao)),
                        ft.DataCell(ft.Row(tight=True, spacing=0, controls=acoes)),
                    ]
                )
            )

        return linhas

    def recarregar(e=None):
        linhas = montar_linhas()
        tabela.rows = linhas
        tabela.visible = bool(linhas)
        vazio.visible = not linhas
        tabela.update()
        vazio.update()

    busca.on_change = recarregar
    filtro_categoria.on_select = recarregar
    mostrar_inativos.on_change = recarregar

    linhas_iniciais = montar_linhas()
    tabela.rows = linhas_iniciais
    tabela.visible = bool(linhas_iniciais)
    vazio.visible = not linhas_iniciais

    conteudo = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Row(
                wrap=True,
                controls=[
                    ft.Text('Cardápio', size=22, weight=ft.FontWeight.BOLD, color='#172B4D'),
                    ft.IconButton(icon=ft.Icons.REFRESH, icon_color='#168C8C',
                                  tooltip='Atualizar', on_click=recarregar),
                ]
            ),
            ft.Row(wrap=True, controls=[busca, filtro_categoria, mostrar_inativos]),
            vazio,
            tabela,
        ]
    )

    return conteudo, recarregar


def produtos_view(page):
    cardapio, recarregar_cardapio = cardapio_produtos(page)

    return ft.Tabs(
        length=2,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label='Cadastro'),
                        ft.Tab(label='Cardápio'),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        cadastro_produtos(page, recarregar_cardapio),
                        cardapio,
                    ]
                ),
            ]
        )
    )