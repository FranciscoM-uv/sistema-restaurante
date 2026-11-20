import hashlib
import hmac
import secrets

import flet as ft
from conexao import conectar

CARGOS = ['Garçom', 'Cozinheiro', 'Gerente', 'Caixa', 'Atendente']

ROTULO_TIPO = {
    'admissao': 'Admissão',
    'mudanca_cargo': 'Mudança de cargo',
    'demissao': 'Demissão',
    'readmissao': 'Readmissão',
}


def hash_pin(pin):
    salt = secrets.token_hex(8)
    h = hashlib.pbkdf2_hmac('sha256', pin.encode(), salt.encode(), 100000).hex()
    return f'{salt}${h}'


def conferir_pin(pin, armazenado):
    salt, h = armazenado.split('$')
    calculado = hashlib.pbkdf2_hmac('sha256', pin.encode(), salt.encode(), 100000).hex()
    return hmac.compare_digest(calculado, h)


def pin_valido(pin):
    return pin.isdigit() and 4 <= len(pin) <= 6


def gerentes_com_pin():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                SELECT id_funcionario, pin_hash
                FROM funcionario
                WHERE cargo = 'Gerente' AND ativo AND pin_hash IS NOT NULL
                '''
            )
            return cursor.fetchall()


def existe_gerente_com_pin():
    return len(gerentes_com_pin()) > 0


def autorizar(pin):
    for id_gerente, pin_hash in gerentes_com_pin():
        if conferir_pin(pin, pin_hash):
            return id_gerente
    return None


def checar_ultimo_gerente(cursor):
    cursor.execute("SELECT COUNT(*) FROM funcionario WHERE cargo = 'Gerente' AND ativo")
    if cursor.fetchone()[0] <= 1:
        raise ValueError('Não é possível: este é o último gerente ativo')


def buscar_funcionarios(mostrar_desligados):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                SELECT id_funcionario, nome, cargo, ativo,
                       data_admissao, data_demissao, pin_hash IS NOT NULL
                FROM funcionario
                WHERE ativo OR %s
                ORDER BY ativo DESC, nome
                ''',
                (mostrar_desligados,)
            )
            return cursor.fetchall()


def cadastrar_funcionario(nome, cargo, pin_hash, id_aut):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO funcionario(nome, cargo, pin_hash)
                VALUES (%s, %s, %s)
                RETURNING id_funcionario
                ''',
                (nome, cargo, pin_hash)
            )
            id_func = cursor.fetchone()[0]
            cursor.execute(
                '''
                INSERT INTO funcionario_historico(id_funcionario, tipo, cargo_novo, autorizado_por)
                VALUES (%s, 'admissao', %s, %s)
                ''',
                (id_func, cargo, id_aut)
            )


def alterar_cargo(id_func, novo_cargo, motivo, id_aut):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                'SELECT cargo, ativo FROM funcionario WHERE id_funcionario = %s',
                (id_func,)
            )
            cargo_atual, ativo = cursor.fetchone()

            if not ativo:
                raise ValueError('Funcionário já está desligado')
            if id_aut == id_func:
                raise ValueError('Você não pode alterar o próprio cargo')
            if cargo_atual == 'Gerente' and novo_cargo != 'Gerente':
                checar_ultimo_gerente(cursor)

            cursor.execute(
                'UPDATE funcionario SET cargo = %s WHERE id_funcionario = %s',
                (novo_cargo, id_func)
            )
            cursor.execute(
                '''
                INSERT INTO funcionario_historico
                    (id_funcionario, tipo, cargo_anterior, cargo_novo, motivo, autorizado_por)
                VALUES (%s, 'mudanca_cargo', %s, %s, %s, %s)
                ''',
                (id_func, cargo_atual, novo_cargo, motivo, id_aut)
            )


def demitir_funcionario(id_func, motivo, id_aut):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                'SELECT cargo, ativo FROM funcionario WHERE id_funcionario = %s',
                (id_func,)
            )
            cargo_atual, ativo = cursor.fetchone()

            if not ativo:
                raise ValueError('Funcionário já está desligado')
            if id_aut == id_func:
                raise ValueError('Você não pode demitir a si mesmo')
            if cargo_atual == 'Gerente':
                checar_ultimo_gerente(cursor)

            cursor.execute(
                '''
                UPDATE funcionario
                SET ativo = FALSE, data_demissao = CURRENT_DATE
                WHERE id_funcionario = %s
                ''',
                (id_func,)
            )
            cursor.execute(
                '''
                INSERT INTO funcionario_historico
                    (id_funcionario, tipo, cargo_anterior, motivo, autorizado_por)
                VALUES (%s, 'demissao', %s, %s, %s)
                ''',
                (id_func, cargo_atual, motivo, id_aut)
            )


def readmitir_funcionario(id_func, cargo, motivo, id_aut):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE funcionario
                SET ativo = TRUE, data_demissao = NULL, cargo = %s
                WHERE id_funcionario = %s
                ''',
                (cargo, id_func)
            )
            cursor.execute(
                '''
                INSERT INTO funcionario_historico
                    (id_funcionario, tipo, cargo_novo, motivo, autorizado_por)
                VALUES (%s, 'readmissao', %s, %s, %s)
                ''',
                (id_func, cargo, motivo, id_aut)
            )


def salvar_pin(id_func, pin_hash):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                'UPDATE funcionario SET pin_hash = %s WHERE id_funcionario = %s',
                (pin_hash, id_func)
            )


def buscar_historico(id_func):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                SELECT h.tipo, h.cargo_anterior, h.cargo_novo, h.motivo,
                       h.registrado_em, a.nome
                FROM funcionario_historico h
                LEFT JOIN funcionario a ON a.id_funcionario = h.autorizado_por
                WHERE h.id_funcionario = %s
                ORDER BY h.registrado_em DESC
                ''',
                (id_func,)
            )
            return cursor.fetchall()


def snack(page, texto, cor='#168C8C'):
    page.show_dialog(ft.SnackBar(content=ft.Text(texto, color='white'), bgcolor=cor))


def exigir_gerente(page, titulo, ao_autorizar):
    campo = ft.TextField(
        label='PIN do gerente',
        password=True,
        can_reveal_password=True,
        width=250,
        autofocus=True
    )

    def confirmar(ev):
        id_aut = autorizar(campo.value or '')
        if id_aut is None:
            snack(page, 'PIN inválido', '#C62828')
            return
        page.pop_dialog()
        ao_autorizar(id_aut)

    campo.on_submit = confirmar

    page.show_dialog(ft.AlertDialog(
        modal=True,
        title=ft.Text(titulo),
        content=campo,
        actions=[
            ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
            ft.Button(
                content=ft.Text('Autorizar'),
                on_click=confirmar,
                style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
            ),
        ]
    ))


def com_autorizacao(page, titulo, ao_autorizar, obrigatorio=True):
    if existe_gerente_com_pin():
        exigir_gerente(page, titulo, ao_autorizar)
    elif obrigatorio:
        snack(page, 'Nenhum gerente com PIN. Cadastre ou defina o PIN de um gerente primeiro.',
              '#C62828')
    else:
        ao_autorizar(None)


def cadastro_funcionarios(page, recarregar_equipe):
    nome_funcionario = ft.TextField(
        label='Nome',
        prefix=ft.Icon(ft.Icons.PERSON, color='#168C8C'),
        hint_text='Digite o nome',
        width=400
    )
    cargo_funcionario = ft.Dropdown(
        label='Cargo do funcionário',
        options=[ft.DropdownOption(c) for c in CARGOS],
        width=400
    )
    pin_funcionario = ft.TextField(
        label='PIN (obrigatório para Gerente, 4 a 6 dígitos)',
        prefix=ft.Icon(ft.Icons.LOCK, color='#168C8C'),
        password=True,
        can_reveal_password=True,
        width=400
    )

    def cadastrar(e):
        if not nome_funcionario.value or not cargo_funcionario.value:
            snack(page, 'Preencha com nome e cargo', '#E65100')
            return

        nome_tratado = nome_funcionario.value.strip().title()
        cargo = cargo_funcionario.value
        pin = (pin_funcionario.value or '').strip()

        if cargo == 'Gerente' and not pin_valido(pin):
            snack(page, 'Gerente precisa de um PIN de 4 a 6 números', '#E65100')
            return
        if pin and not pin_valido(pin):
            snack(page, 'O PIN deve ter de 4 a 6 números', '#E65100')
            return

        pin_hash = hash_pin(pin) if pin else None

        def executar(id_aut):
            try:
                cadastrar_funcionario(nome_tratado, cargo, pin_hash, id_aut)
            except Exception:
                snack(page, 'Erro ao cadastrar funcionário', '#C62828')
                return

            nome_funcionario.value = ''
            cargo_funcionario.value = None
            pin_funcionario.value = ''
            snack(page, 'Cadastro com sucesso')
            page.update()
            recarregar_equipe()

        com_autorizacao(page, 'Autorizar cadastro', executar, obrigatorio=False)

    return ft.Column(
        controls=[
            ft.Text(
                'Cadastro de Funcionários',
                size=30,
                weight=ft.FontWeight.BOLD,
                color='#172B4D'
            ),
            nome_funcionario,
            cargo_funcionario,
            pin_funcionario,
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


def equipe_funcionarios(page):
    mostrar_desligados = ft.Switch(label='Mostrar desligados', value=False)

    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text('Nome')),
            ft.DataColumn(label=ft.Text('Cargo')),
            ft.DataColumn(label=ft.Text('Situação')),
            ft.DataColumn(label=ft.Text('Admissão')),
            ft.DataColumn(label=ft.Text('Ações')),
        ],
        rows=[]
    )
    vazio = ft.Text('Nenhum funcionário encontrado.', color='#6B778C')

    def abrir_cargo(id_func, nome, cargo_atual):
        opcoes = [c for c in CARGOS if c != cargo_atual]
        novo = ft.Dropdown(
            label='Novo cargo',
            options=[ft.DropdownOption(c) for c in opcoes],
            width=300
        )
        motivo = ft.TextField(label='Motivo (opcional)', width=300)

        def confirmar(ev):
            if not novo.value:
                snack(page, 'Escolha o novo cargo', '#C62828')
                return

            novo_cargo = novo.value
            texto_motivo = motivo.value.strip()
            page.pop_dialog()

            def executar(id_aut):
                try:
                    alterar_cargo(id_func, novo_cargo, texto_motivo, id_aut)
                except ValueError as err:
                    snack(page, str(err), '#C62828')
                    return
                except Exception:
                    snack(page, 'Erro ao alterar o cargo', '#C62828')
                    return
                snack(page, f'{nome} agora é {novo_cargo}')
                recarregar()

            com_autorizacao(page, 'Autorizar mudança de cargo', executar)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Alterar cargo: {nome}'),
            content=ft.Column(
                tight=True,
                spacing=15,
                controls=[ft.Text(f'Cargo atual: {cargo_atual}'), novo, motivo]
            ),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(
                    content=ft.Text('Continuar'),
                    on_click=confirmar,
                    style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
                ),
            ]
        ))

    def abrir_demissao(id_func, nome):
        motivo = ft.TextField(label='Motivo da demissão', width=300)

        def confirmar(ev):
            if not motivo.value.strip():
                snack(page, 'Informe o motivo', '#C62828')
                return

            texto_motivo = motivo.value.strip()
            page.pop_dialog()

            def executar(id_aut):
                try:
                    demitir_funcionario(id_func, texto_motivo, id_aut)
                except ValueError as err:
                    snack(page, str(err), '#C62828')
                    return
                except Exception:
                    snack(page, 'Erro ao demitir funcionário', '#C62828')
                    return
                snack(page, f'{nome} foi desligado')
                recarregar()

            com_autorizacao(page, 'Autorizar demissão', executar)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Demitir {nome}?'),
            content=ft.Column(
                tight=True,
                spacing=15,
                controls=[
                    ft.Text('O cadastro e o histórico são mantidos.'),
                    motivo,
                ]
            ),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(
                    content=ft.Text('Continuar'),
                    on_click=confirmar,
                    style=ft.ButtonStyle(bgcolor='#C62828', color='white')
                ),
            ]
        ))

    def abrir_readmissao(id_func, nome, cargo_anterior):
        cargo = ft.Dropdown(
            label='Cargo',
            value=cargo_anterior if cargo_anterior in CARGOS else None,
            options=[ft.DropdownOption(c) for c in CARGOS],
            width=300
        )
        motivo = ft.TextField(label='Motivo (opcional)', width=300)

        def confirmar(ev):
            if not cargo.value:
                snack(page, 'Escolha o cargo', '#C62828')
                return

            cargo_escolhido = cargo.value
            texto_motivo = motivo.value.strip()
            page.pop_dialog()

            def executar(id_aut):
                try:
                    readmitir_funcionario(id_func, cargo_escolhido, texto_motivo, id_aut)
                except Exception:
                    snack(page, 'Erro ao readmitir funcionário', '#C62828')
                    return
                snack(page, f'{nome} foi readmitido')
                recarregar()

            com_autorizacao(page, 'Autorizar readmissão', executar)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Readmitir {nome}'),
            content=ft.Column(tight=True, spacing=15, controls=[cargo, motivo]),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(
                    content=ft.Text('Continuar'),
                    on_click=confirmar,
                    style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
                ),
            ]
        ))

    def abrir_pin(id_func, nome):
        novo_pin = ft.TextField(
            label='Novo PIN (4 a 6 números)',
            password=True,
            can_reveal_password=True,
            width=300
        )

        def confirmar(ev):
            pin = (novo_pin.value or '').strip()
            if not pin_valido(pin):
                snack(page, 'O PIN deve ter de 4 a 6 números', '#C62828')
                return

            pin_hash = hash_pin(pin)
            page.pop_dialog()

            def executar(id_aut):
                try:
                    salvar_pin(id_func, pin_hash)
                except Exception:
                    snack(page, 'Erro ao salvar o PIN', '#C62828')
                    return
                snack(page, f'PIN de {nome} definido')
                recarregar()

            com_autorizacao(page, 'Autorizar troca de PIN', executar, obrigatorio=False)

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Definir PIN: {nome}'),
            content=novo_pin,
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(
                    content=ft.Text('Continuar'),
                    on_click=confirmar,
                    style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
                ),
            ]
        ))

    def abrir_historico(id_func, nome):
        eventos = buscar_historico(id_func)
        itens = []

        for tipo, anterior, novo, motivo, quando, autorizador in eventos:
            if tipo == 'mudanca_cargo':
                detalhe = f'{anterior} → {novo}'
            elif tipo == 'demissao':
                detalhe = f'Cargo: {anterior}'
            else:
                detalhe = f'Cargo: {novo}'

            linhas = [
                ft.Text(f'{ROTULO_TIPO[tipo]}  ·  {quando:%d/%m/%Y %H:%M}',
                        weight=ft.FontWeight.BOLD, color='#168C8C'),
                ft.Text(detalhe),
            ]
            if motivo:
                linhas.append(ft.Text(f'Motivo: {motivo}', size=13))
            if autorizador:
                linhas.append(ft.Text(f'Autorizado por: {autorizador}', size=13,
                                      color='#6B778C'))

            itens.append(ft.Column(spacing=2, controls=linhas))
            itens.append(ft.Divider(height=1))

        if not itens:
            itens.append(ft.Text('Sem registros.'))

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f'Histórico: {nome}'),
            content=ft.Column(width=380, height=300, scroll=ft.ScrollMode.AUTO,
                              spacing=10, controls=itens),
            actions=[ft.TextButton('Fechar', on_click=lambda ev: page.pop_dialog())]
        ))

    def montar_linhas():
        linhas = []

        for id_func, nome, cargo, ativo, admissao, demissao, tem_pin in \
                buscar_funcionarios(mostrar_desligados.value):

            acoes = [
                ft.IconButton(
                    icon=ft.Icons.HISTORY,
                    icon_color='#6B778C',
                    tooltip='Histórico',
                    on_click=lambda e, i=id_func, n=nome: abrir_historico(i, n)
                )
            ]

            if ativo:
                acoes.insert(0, ft.IconButton(
                    icon=ft.Icons.SWAP_HORIZ,
                    icon_color='#168C8C',
                    tooltip='Alterar cargo',
                    on_click=lambda e, i=id_func, n=nome, c=cargo: abrir_cargo(i, n, c)
                ))
                if cargo == 'Gerente':
                    acoes.insert(1, ft.IconButton(
                        icon=ft.Icons.LOCK if tem_pin else ft.Icons.LOCK_OPEN,
                        icon_color='#168C8C' if tem_pin else '#E65100',
                        tooltip='Definir PIN',
                        on_click=lambda e, i=id_func, n=nome: abrir_pin(i, n)
                    ))
                acoes.append(ft.IconButton(
                    icon=ft.Icons.PERSON_OFF,
                    icon_color='#C62828',
                    tooltip='Demitir',
                    on_click=lambda e, i=id_func, n=nome: abrir_demissao(i, n)
                ))
                situacao = 'Ativo'
                cor_situacao = '#168C8C'
            else:
                acoes.insert(0, ft.IconButton(
                    icon=ft.Icons.REPLAY,
                    icon_color='#168C8C',
                    tooltip='Readmitir',
                    on_click=lambda e, i=id_func, n=nome, c=cargo: abrir_readmissao(i, n, c)
                ))
                situacao = f'Desligado em {demissao:%d/%m/%Y}'
                cor_situacao = '#C62828'

            linhas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(nome)),
                        ft.DataCell(ft.Text(cargo)),
                        ft.DataCell(ft.Text(situacao, color=cor_situacao)),
                        ft.DataCell(ft.Text(f'{admissao:%d/%m/%Y}')),
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

    mostrar_desligados.on_change = recarregar

    linhas_iniciais = montar_linhas()
    tabela.rows = linhas_iniciais
    tabela.visible = bool(linhas_iniciais)
    vazio.visible = not linhas_iniciais

    conteudo = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Row(
                controls=[
                    ft.Text('Equipe', size=22, weight=ft.FontWeight.BOLD, color='#172B4D'),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color='#168C8C',
                        tooltip='Atualizar',
                        on_click=recarregar
                    ),
                    mostrar_desligados,
                ]
            ),
            vazio,
            tabela,
        ]
    )

    return conteudo, recarregar


def funcionarios_view(page):
    equipe, recarregar_equipe = equipe_funcionarios(page)

    return ft.Tabs(
        length=2,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label='Cadastro'),
                        ft.Tab(label='Equipe'),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        cadastro_funcionarios(page, recarregar_equipe),
                        equipe,
                    ]
                ),
            ]
        )
    )