import flet as ft
from conexao import conectar


def cadastro_clientes(page):
    nome_cadastro = ft.TextField(
        label='Nome',
        prefix=ft.Icon(ft.Icons.PERSON, color='#168C8C'),
        hint_text='Digite o nome',
        width=400
    )
    telefone_cadastro = ft.TextField(
        label='Telefone',
        prefix=ft.Icon(ft.Icons.PHONE, color='#168C8C'),
        hint_text='Digite o telefone',
        width=400
    )
    email_cadastro = ft.TextField(
        label='E-mail',
        prefix=ft.Icon(ft.Icons.EMAIL, color='#168C8C'),
        hint_text='Digite o email',
        width=400
    )

    def formatar_telefone(e):
        numeros = ''
        for caractere in telefone_cadastro.value:
            if caractere.isdigit():
                numeros += caractere

        numeros = numeros[:11]

        if len(numeros) <= 2:
            formatado = numeros
        elif len(numeros) <= 7:
            formatado = numeros[:2] + ' ' + numeros[2:]
        else:
            formatado = numeros[:2] + ' ' + numeros[2:7] + '-' + numeros[7:]

        telefone_cadastro.value = formatado
        telefone_cadastro.update()

    telefone_cadastro.on_change = formatar_telefone

    def cadastrar(e):
        if not nome_cadastro.value or not email_cadastro.value:
            page.show_dialog(ft.SnackBar(content=ft.Text('Preencha pelo menos nome e e-mail')))
            return

        try:
            with conectar() as conexao:
                with conexao.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO cliente(nome, telefone, email) VALUES (%s, %s, %s)',
                        (nome_cadastro.value, telefone_cadastro.value, email_cadastro.value)
                    )

            nome_cadastro.value = ''
            telefone_cadastro.value = ''
            email_cadastro.value = ''
            page.show_dialog(ft.SnackBar(content=ft.Text('Cadastro com sucesso', color='white'),
                                         bgcolor='#168C8C'))
            page.update()

        except Exception:
            page.show_dialog(ft.SnackBar(content=ft.Text('E-mail já cadastrado ou dados inválidos', color='white'),
                                         bgcolor='#C62828'))

    return ft.Column(
        controls=[
            ft.Text(
                "Cadastro de Clientes",
                size=30,
                weight=ft.FontWeight.BOLD,
                color="#172B4D"
            ),
            nome_cadastro,
            telefone_cadastro,
            email_cadastro,
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


def clientes_view(page):
    lista, recarregar_lista = listar_clientes()

    return ft.Tabs(
        length=3,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label='Cadastro'),
                        ft.Tab(label='Lista'),
                        ft.Tab(label='Consulta'),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        cadastro_clientes(page),
                        lista,
                        consulta_clientes(recarregar_lista),
                    ]
                ),
            ]
        )
    )


def listar_clientes():
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text('Mesa(s)')),
            ft.DataColumn(label=ft.Text('Nome')),
            ft.DataColumn(label=ft.Text('Telefone')),
            ft.DataColumn(label=ft.Text('E-mail')),
            ft.DataColumn(label=ft.Text('Comanda')),
        ],
        rows=[]
    )
    vazio = ft.Text('Nenhuma comanda aberta no momento.', color='#6B778C')

    def fechar(e, id_comanda):
        fechar_comanda(id_comanda)
        e.page.show_dialog(ft.SnackBar(
            content=ft.Text('Comanda fechada', color='white'),
            bgcolor='#168C8C'
        ))
        recarregar()

    def montar_linhas():
        linhas = []
        for id_comanda, mesas, nome, telefone, email in buscar_clientes_comanda_aberta():
            linhas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(mesas))),
                        ft.DataCell(ft.Text(nome)),
                        ft.DataCell(ft.Text(telefone)),
                        ft.DataCell(ft.Text(email)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.RECEIPT_LONG,
                                icon_color='#C62828',
                                tooltip='Fechar comanda',
                                on_click=lambda e, i=id_comanda: fechar(e, i)
                            )
                        ),
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

    linhas_iniciais = montar_linhas()
    tabela.rows = linhas_iniciais
    tabela.visible = bool(linhas_iniciais)
    vazio.visible = not linhas_iniciais

    conteudo = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Row(
                controls=[
                    ft.Text('Comandas abertas', size=22,
                            weight=ft.FontWeight.BOLD, color='#172B4D'),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color='#168C8C',
                        tooltip='Atualizar',
                        on_click=recarregar
                    ),
                ]
            ),
            vazio,
            tabela,
        ]
    )

    return conteudo, recarregar


def buscar_clientes(filtro=None):
    with conectar() as conexao:
        with conexao.cursor() as cursor:

            if filtro:
                cursor.execute(
                    '''
                    SELECT id_cliente, nome, telefone, email
                    FROM cliente
                    WHERE LOWER(nome) LIKE LOWER(%s)
                    OR telefone LIKE %s
                    ORDER BY nome
                    ''',
                    (f'%{filtro}%', f'%{filtro}%')
                )
            else:
                cursor.execute(
                    '''
                    SELECT id_cliente, nome, telefone, email
                    FROM cliente
                    ORDER BY nome
                    '''
                )

            return cursor.fetchall()


def atualizar_cliente(id_cliente, nome, telefone, email):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE cliente
                SET nome = %s, telefone = %s, email = %s
                WHERE id_cliente = %s
                ''',
                (nome, telefone, email, id_cliente)
            )


def buscar_mesas():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute('SELECT id_mesa, numero_mesa FROM mesa ORDER BY numero_mesa')
            return cursor.fetchall()


def abrir_comanda(id_cliente, ids_mesa):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                'INSERT INTO comanda(id_cliente) VALUES (%s) RETURNING id_comanda',
                (id_cliente,)
            )
            id_comanda = cursor.fetchone()[0]

            for id_mesa in ids_mesa:
                cursor.execute(
                    'INSERT INTO comanda_mesa(id_comanda, id_mesa) VALUES (%s, %s)',
                    (id_comanda, id_mesa)
                )


def fechar_comanda(id_comanda):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE comanda
                SET status = 'fechada', fechada_em = NOW()
                WHERE id_comanda = %s
                ''',
                (id_comanda,)
            )


def buscar_clientes_comanda_aberta():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                SELECT co.id_comanda,
                       STRING_AGG(m.numero_mesa::text, ' + ' ORDER BY m.numero_mesa) AS mesas,
                       c.nome, c.telefone, c.email
                FROM comanda co
                JOIN cliente c ON c.id_cliente = co.id_cliente
                JOIN comanda_mesa cm ON cm.id_comanda = co.id_comanda
                JOIN mesa m ON m.id_mesa = cm.id_mesa
                WHERE co.status = 'aberta'
                GROUP BY co.id_comanda, c.nome, c.telefone, c.email
                ORDER BY MIN(m.numero_mesa), c.nome
                '''
            )
            return cursor.fetchall()


def consulta_clientes(recarregar_lista):
    resultado = ft.Column(spacing=10)
    sugestoes = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    pesquisa = ft.TextField(
        label='Digite o nome ou telefone para consultar',
        prefix=ft.Icon(ft.Icons.SEARCH, color='#168C8C'),
        width=400
    )

    def linha_info(icone, texto):
        return ft.Row(
            controls=[
                ft.Icon(icone, color='#168C8C', size=20),
                ft.Text(texto, size=15, color='#172B4D'),
            ],
            spacing=10
        )

    def card_cliente(cliente):
        id_cliente, nome, telefone, email = cliente

        return ft.Container(
            width=400,
            padding=20,
            border_radius=12,
            bgcolor='white',
            border=ft.Border.all(1, '#D0D7DE'),
            shadow=ft.BoxShadow(
                blur_radius=8,
                color='#1A000000',
                offset=ft.Offset(0, 2)
            ),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                nome,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color='#168C8C'
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_color='#168C8C',
                                tooltip='Editar cliente',
                                on_click=lambda e, c=cliente: abrir_edicao(e, c)
                            ),
                        ]
                    ),
                    ft.Divider(height=1),
                    linha_info(ft.Icons.PHONE, telefone),
                    linha_info(ft.Icons.EMAIL, email),
                    ft.Button(
                        content=ft.Text('Abrir comanda'),
                        icon=ft.Icons.RECEIPT_LONG,
                        on_click=lambda e, c=cliente: abrir_comanda_dialog(e, c),
                        style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
                    ),
                ]
            )
        )

    def abrir_edicao(e, cliente):
        page = e.page
        id_cliente, nome, telefone, email = cliente

        campo_nome = ft.TextField(label='Nome', value=nome, width=350)
        campo_telefone = ft.TextField(label='Telefone', value=telefone, width=350)
        campo_email = ft.TextField(label='E-mail', value=email, width=350)

        def formatar(ev):
            numeros = ''.join(c for c in campo_telefone.value if c.isdigit())[:11]

            if len(numeros) <= 2:
                formatado = numeros
            elif len(numeros) <= 7:
                formatado = numeros[:2] + ' ' + numeros[2:]
            else:
                formatado = numeros[:2] + ' ' + numeros[2:7] + '-' + numeros[7:]

            campo_telefone.value = formatado
            campo_telefone.update()

        campo_telefone.on_change = formatar

        def salvar(ev):
            if not campo_nome.value.strip() or not campo_email.value.strip():
                page.show_dialog(ft.SnackBar(
                    content=ft.Text('Preencha pelo menos nome e e-mail', color='white'),
                    bgcolor='#C62828'
                ))
                return

            try:
                atualizar_cliente(
                    id_cliente,
                    campo_nome.value.strip(),
                    campo_telefone.value,
                    campo_email.value.strip()
                )
            except Exception:
                page.show_dialog(ft.SnackBar(
                    content=ft.Text('E-mail já cadastrado ou dados inválidos', color='white'),
                    bgcolor='#C62828'
                ))
                return

            page.pop_dialog()
            page.show_dialog(ft.SnackBar(
                content=ft.Text('Cliente atualizado', color='white'),
                bgcolor='#168C8C'
            ))

            pesquisa.value = campo_nome.value.strip()
            pesquisa.update()
            pesquisar(None)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text('Editar cliente'),
            content=ft.Column(
                tight=True,
                spacing=15,
                controls=[campo_nome, campo_telefone, campo_email]
            ),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(
                    content=ft.Text('Salvar'),
                    on_click=salvar,
                    style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
                ),
            ]
        ))

    def abrir_comanda_dialog(e, cliente):
        page = e.page
        id_cliente, nome, telefone, email = cliente

        checks = [
            ft.Checkbox(label=f'Mesa {numero}', data=id_mesa)
            for id_mesa, numero in buscar_mesas()
        ]

        def confirmar(ev):
            ids = [c.data for c in checks if c.value]

            if not ids:
                page.show_dialog(ft.SnackBar(
                    content=ft.Text('Escolha pelo menos uma mesa', color='white'),
                    bgcolor='#C62828'
                ))
                return

            try:
                abrir_comanda(id_cliente, ids)
            except Exception:
                page.show_dialog(ft.SnackBar(
                    content=ft.Text('Esse cliente já tem comanda aberta', color='white'),
                    bgcolor='#C62828'
                ))
                return

            page.pop_dialog()
            page.show_dialog(ft.SnackBar(
                content=ft.Text(f'Comanda aberta para {nome}', color='white'),
                bgcolor='#168C8C'
            ))
            recarregar_lista()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Abrir comanda: {nome}'),
            content=ft.Column(
                width=250,
                height=250,
                scroll=ft.ScrollMode.AUTO,
                controls=checks
            ),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(
                    content=ft.Text('Abrir'),
                    on_click=confirmar,
                    style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
                ),
            ]
        ))

    def aviso(texto, cor_fundo, cor_texto, icone):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            border_radius=8,
            bgcolor=cor_fundo,
            content=ft.Row(
                tight=True,
                spacing=8,
                controls=[
                    ft.Icon(icone, color=cor_texto, size=20),
                    ft.Text(texto, color=cor_texto, weight=ft.FontWeight.W_500),
                ]
            )
        )

    def selecionar_cliente(e, cliente):
        id_cliente, nome, telefone, email = cliente

        resultado.controls.clear()
        resultado.controls.append(card_cliente(cliente))
        pesquisa.value = nome
        sugestoes.controls.clear()

        pesquisa.update()
        sugestoes.update()
        resultado.update()

    def pesquisar(e):
        texto = pesquisa.value.strip()

        resultado.controls.clear()
        sugestoes.controls.clear()
        sugestoes.update()

        if not texto:
            resultado.controls.append(
                aviso('Digite um nome ou telefone.', '#FFF4E5', '#B26A00', ft.Icons.INFO_OUTLINE)
            )
            resultado.update()
            return

        clientes = buscar_clientes(texto)

        if clientes:
            for cliente in clientes:
                resultado.controls.append(card_cliente(cliente))
        else:
            resultado.controls.append(
                aviso('Cliente não encontrado', '#FDECEA', '#C62828', ft.Icons.PERSON_OFF)
            )

        resultado.update()

    def sugerir(e):
        texto = pesquisa.value.strip()

        resultado.controls.clear()
        resultado.update()

        sugestoes.controls.clear()

        if len(texto) < 2:
            sugestoes.update()
            return

        for cliente in buscar_clientes(texto):
            id_cliente, nome, telefone, email = cliente

            sugestoes.controls.append(
                ft.Button(
                    content=ft.Text(f'{nome} - {telefone}'),
                    on_click=lambda e, c=cliente: selecionar_cliente(e, c)
                )
            )

        sugestoes.update()

    pesquisa.on_change = sugerir
    pesquisa.on_submit = pesquisar

    botao_pesquisar = ft.Button(
        content=ft.Text('Pesquisar'),
        on_click=pesquisar,
        style=ft.ButtonStyle(
            bgcolor='#168C8C',
            color='white'
        )
    )

    return ft.Column(
        controls=[
            ft.Container(height=40),
            pesquisa,
            sugestoes,
            botao_pesquisar,
            resultado
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15
    )