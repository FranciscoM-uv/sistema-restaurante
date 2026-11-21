import flet as ft
from datetime import datetime, timedelta
from conexao import conectar
from views.clientes import buscar_clientes

COR = {
    'Livre': '#168C8C',
    'Ocupada': '#C62828',
    'Reservada': '#F9A825',
}


def buscar_mesas():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                SELECT m.id_mesa, m.numero_mesa, m.capacidade,
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM comanda_mesa cm
                            JOIN comanda co ON co.id_comanda = cm.id_comanda
                            WHERE cm.id_mesa = m.id_mesa AND co.status = 'aberta'
                        ) THEN 'Ocupada'
                        WHEN EXISTS (
                            SELECT 1 FROM reserva r
                            WHERE r.id_mesa = m.id_mesa
                              AND r.status = 'ativa'
                              AND r.data_hora BETWEEN NOW() - INTERVAL '1 hour'
                                                  AND NOW() + INTERVAL '2 hours'
                        ) THEN 'Reservada'
                        ELSE 'Livre'
                    END AS situacao
                FROM mesa m
                ORDER BY m.numero_mesa
                '''
            )
            return cursor.fetchall()


def cadastrar_mesa(numero, capacidade):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                "INSERT INTO mesa(numero_mesa, capacidade, status) VALUES (%s, %s, 'Livre')",
                (numero, capacidade)
            )


def buscar_reservas(id_mesa):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                SELECT id_reserva, nome_reserva, num_pessoas, data_hora
                FROM reserva
                WHERE id_mesa = %s
                  AND status = 'ativa'
                  AND data_hora >= NOW() - INTERVAL '1 hour'
                ORDER BY data_hora
                ''',
                (id_mesa,)
            )
            return cursor.fetchall()


def criar_reserva(id_mesa, id_cliente, nome, telefone, pessoas, data_hora):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO reserva(id_mesa, id_cliente, nome_reserva, telefone,
                                    num_pessoas, data_hora)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''',
                (id_mesa, id_cliente, nome, telefone, pessoas, data_hora)
            )


def cancelar_reserva(id_reserva):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                "UPDATE reserva SET status = 'cancelada' WHERE id_reserva = %s",
                (id_reserva,)
            )


def snack(page, texto, cor='#168C8C'):
    page.show_dialog(ft.SnackBar(content=ft.Text(texto, color='white'), bgcolor=cor))


def formatar_telefone(texto):
    numeros = ''.join(c for c in texto if c.isdigit())[:11]

    if len(numeros) <= 2:
        return numeros
    if len(numeros) <= 7:
        return numeros[:2] + ' ' + numeros[2:]
    return numeros[:2] + ' ' + numeros[2:7] + '-' + numeros[7:]


def formatar_hora(texto):
    numeros = ''.join(c for c in texto if c.isdigit())[:4]

    if len(numeros) <= 2:
        return numeros
    return numeros[:2] + ':' + numeros[2:]


def formatar_data(texto):
    numeros = ''.join(c for c in texto if c.isdigit())[:8]

    if len(numeros) <= 2:
        return numeros
    if len(numeros) <= 4:
        return numeros[:2] + '/' + numeros[2:]
    return numeros[:2] + '/' + numeros[2:4] + '/' + numeros[4:]


def mesas_view(page):
    grade = ft.Row(
        wrap=True,
        spacing=15,
        run_spacing=15,
        alignment=ft.MainAxisAlignment.CENTER
    )

    def montar_cards():
        cards = []
        for mesa in buscar_mesas():
            id_mesa, numero, capacidade, situacao = mesa
            cards.append(
                ft.Container(
                    width=130,
                    height=95,
                    border_radius=10,
                    bgcolor=COR[situacao],
                    ink=True,
                    alignment=ft.Alignment(0, 0),
                    on_click=lambda e, m=mesa: abrir_mesa(e, m),
                    content=ft.Column(
                        tight=True,
                        spacing=2,
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(str(numero), color='white', size=28,
                                    weight=ft.FontWeight.BOLD),
                            ft.Row(
                                tight=True,
                                spacing=4,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.PEOPLE, color='white', size=16),
                                    ft.Text(str(capacidade), color='white', size=14),
                                ]
                            ),
                        ]
                    )
                )
            )
        return cards

    def recarregar(e=None):
        grade.controls = montar_cards()
        grade.update()

    grade.controls = montar_cards()

    def abrir_nova_mesa(e):
        page = e.page
        campo_numero = ft.TextField(label='Número da mesa', width=250,
                                    keyboard_type=ft.KeyboardType.NUMBER)
        campo_capacidade = ft.TextField(label='Capacidade (pessoas)', width=250,
                                        keyboard_type=ft.KeyboardType.NUMBER)

        def salvar(ev):
            if not campo_numero.value.isdigit() or not campo_capacidade.value.isdigit() \
                    or int(campo_capacidade.value) < 1:
                snack(page, 'Informe número e capacidade válidos', '#C62828')
                return
            try:
                cadastrar_mesa(int(campo_numero.value), int(campo_capacidade.value))
            except Exception:
                snack(page, 'Já existe uma mesa com esse número', '#C62828')
                return

            page.pop_dialog()
            snack(page, f'Mesa {campo_numero.value} criada')
            recarregar()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text('Nova mesa'),
            content=ft.Column(tight=True, spacing=15,
                              controls=[campo_numero, campo_capacidade]),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(content=ft.Text('Salvar'), on_click=salvar,
                          style=ft.ButtonStyle(bgcolor='#168C8C', color='white')),
            ]
        ))

    def abrir_reserva(e, mesa):
        page = e.page
        id_mesa, numero, capacidade, situacao = mesa
        page.pop_dialog()

        cliente_escolhido = {'id': None}

        busca_cliente = ft.TextField(
            label='Buscar cliente cadastrado',
            prefix=ft.Icon(ft.Icons.SEARCH, color='#168C8C'),
            hint_text='Nome ou telefone',
            width=300
        )
        sugestoes = ft.Column(spacing=0, width=300)
        campo_nome = ft.TextField(label='Nome da reserva', width=300)
        campo_telefone = ft.TextField(label='Telefone', width=300)
        campo_pessoas = ft.TextField(label=f'Pessoas (máx. {capacidade})', width=300,
                                     keyboard_type=ft.KeyboardType.NUMBER)
        campo_data = ft.TextField(label='Data (DD/MM/AAAA)', width=240,
                                  value=datetime.now().strftime('%d/%m/%Y'),
                                  max_length=10)
        campo_hora = ft.TextField(label='Hora (HH:MM)', width=300,
                                  hint_text='19:30', max_length=5)

        def escolher(ev, cliente):
            id_cliente, nome, telefone, email = cliente
            cliente_escolhido['id'] = id_cliente

            campo_nome.value = nome
            campo_telefone.value = telefone or ''
            busca_cliente.value = nome
            sugestoes.controls.clear()

            busca_cliente.update()
            campo_nome.update()
            campo_telefone.update()
            sugestoes.update()

        def sugerir(ev):
            texto = (busca_cliente.value or '').strip()
            sugestoes.controls.clear()

            if len(texto) >= 2:
                for cliente in buscar_clientes(texto)[:5]:
                    id_cliente, nome, telefone, email = cliente
                    sugestoes.controls.append(
                        ft.TextButton(
                            content=ft.Text(f'{nome} - {telefone}'),
                            on_click=lambda ev, c=cliente: escolher(ev, c)
                        )
                    )

            sugestoes.update()

        def nome_alterado(ev):
            cliente_escolhido['id'] = None

        def telefone_alterado(ev):
            campo_telefone.value = formatar_telefone(campo_telefone.value)
            campo_telefone.update()

        def data_alterada(ev):
            campo_data.value = formatar_data(campo_data.value)
            campo_data.update()

        def hora_alterada(ev):
            campo_hora.value = formatar_hora(campo_hora.value)
            campo_hora.update()

        def data_escolhida(ev):
            valor = ev.control.value
            if valor:
                campo_data.value = f'{valor:%d/%m/%Y}'
                campo_data.update()

        def abrir_calendario(ev):
            hoje = datetime.now()
            page.show_dialog(ft.DatePicker(
                first_date=hoje,
                last_date=hoje + timedelta(days=365),
                on_change=data_escolhida
            ))

        busca_cliente.on_change = sugerir
        campo_nome.on_change = nome_alterado
        campo_telefone.on_change = telefone_alterado
        campo_data.on_change = data_alterada
        campo_hora.on_change = hora_alterada

        def salvar(ev):
            if not campo_nome.value.strip() or not campo_pessoas.value.isdigit():
                snack(page, 'Preencha nome e número de pessoas', '#C62828')
                return

            pessoas = int(campo_pessoas.value)
            if pessoas < 1 or pessoas > capacidade:
                snack(page, f'A mesa {numero} comporta até {capacidade} pessoas', '#C62828')
                return

            try:
                data_hora = datetime.strptime(
                    f'{campo_data.value.strip()} {campo_hora.value.strip()}',
                    '%d/%m/%Y %H:%M'
                )
            except ValueError:
                snack(page, 'Data ou hora inválida. Use DD/MM/AAAA e HH:MM (ex.: 19:30)',
                      '#C62828')
                return

            if data_hora < datetime.now():
                snack(page, 'Não é possível reservar para um horário que já passou',
                      '#C62828')
                return

            criar_reserva(
                id_mesa,
                cliente_escolhido['id'],
                campo_nome.value.strip(),
                campo_telefone.value.strip(),
                pessoas,
                data_hora
            )
            page.pop_dialog()
            snack(page, f'Mesa {numero} reservada para {campo_nome.value.strip()}')
            recarregar()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Reservar mesa {numero}'),
            content=ft.Column(
                tight=True,
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                width=320,
                controls=[
                    busca_cliente,
                    sugestoes,
                    campo_nome,
                    campo_telefone,
                    campo_pessoas,
                    ft.Row(
                        spacing=0,
                        controls=[
                            campo_data,
                            ft.IconButton(
                                icon=ft.Icons.CALENDAR_MONTH,
                                icon_color='#168C8C',
                                tooltip='Escolher no calendário',
                                on_click=abrir_calendario
                            ),
                        ]
                    ),
                    campo_hora,
                ]
            ),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda ev: page.pop_dialog()),
                ft.Button(content=ft.Text('Reservar'), on_click=salvar,
                          style=ft.ButtonStyle(bgcolor='#168C8C', color='white')),
            ]
        ))

    def abrir_mesa(e, mesa):
        page = e.page
        id_mesa, numero, capacidade, situacao = mesa
        reservas = buscar_reservas(id_mesa)

        def cancelar(ev, id_reserva, nome):
            cancelar_reserva(id_reserva)
            page.pop_dialog()
            snack(page, f'Reserva de {nome} cancelada')
            recarregar()

            for m in buscar_mesas():
                if m[0] == id_mesa:
                    abrir_mesa(ev, m)
                    break

        conteudo = [
            ft.Text(f'Capacidade: {capacidade} pessoas'),
            ft.Text(f'Situação: {situacao}', weight=ft.FontWeight.BOLD, color=COR[situacao]),
        ]

        if reservas:
            conteudo.append(ft.Divider(height=1))
            conteudo.append(ft.Text('Reservas', weight=ft.FontWeight.BOLD))

            linhas = []
            for id_reserva, nome, pessoas, data_hora in reservas:
                linhas.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=0,
                                expand=True,
                                controls=[
                                    ft.Text(nome, weight=ft.FontWeight.W_500),
                                    ft.Text(f'{data_hora:%d/%m/%Y às %H:%M}  ·  '
                                            f'{pessoas} pessoas',
                                            size=13, color='#6B778C'),
                                ]
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EVENT_BUSY,
                                icon_color='#C62828',
                                tooltip='Cancelar esta reserva',
                                on_click=lambda ev, i=id_reserva, n=nome: cancelar(ev, i, n)
                            ),
                        ]
                    )
                )

            conteudo.append(
                ft.Column(
                    spacing=4,
                    height=min(len(linhas) * 60, 240),
                    scroll=ft.ScrollMode.AUTO,
                    controls=linhas
                )
            )
        else:
            conteudo.append(ft.Text('Nenhuma reserva para esta mesa.', color='#6B778C'))

        acoes = [ft.TextButton('Fechar', on_click=lambda ev: page.pop_dialog())]

        if situacao != 'Ocupada':
            acoes.append(
                ft.Button(content=ft.Text('Reservar'),
                          on_click=lambda ev: abrir_reserva(ev, mesa),
                          style=ft.ButtonStyle(bgcolor='#168C8C', color='white'))
            )

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Mesa {numero}'),
            content=ft.Column(tight=True, spacing=8, width=360, controls=conteudo),
            actions=acoes
        ))

    def item_legenda(texto, cor):
        return ft.Row(
            tight=True,
            spacing=6,
            controls=[
                ft.Container(width=14, height=14, border_radius=3, bgcolor=cor),
                ft.Text(texto, size=13),
            ]
        )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=20,
        controls=[
            ft.Container(height=10),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
                controls=[
                    ft.Text('Mesas', size=26, weight=ft.FontWeight.BOLD, color='#172B4D'),
                    ft.IconButton(icon=ft.Icons.REFRESH, icon_color='#168C8C',
                                  tooltip='Atualizar', on_click=recarregar),
                    ft.Button(content=ft.Text('Nova mesa'), icon=ft.Icons.ADD,
                              on_click=abrir_nova_mesa,
                              style=ft.ButtonStyle(bgcolor='#168C8C', color='white')),
                ]
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=25,
                controls=[item_legenda(s, c) for s, c in COR.items()]
            ),
            grade,
        ]
    )