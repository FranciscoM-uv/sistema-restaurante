import flet as ft
from datetime import datetime
from conexao import conectar

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


def buscar_reserva(id_mesa):
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
                LIMIT 1
                ''',
                (id_mesa,)
            )
            return cursor.fetchone()


def criar_reserva(id_mesa, nome, telefone, pessoas, data_hora):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO reserva(id_mesa, nome_reserva, telefone, num_pessoas, data_hora)
                VALUES (%s, %s, %s, %s, %s)
                ''',
                (id_mesa, nome, telefone, pessoas, data_hora)
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

        campo_nome = ft.TextField(label='Nome da reserva', width=300)
        campo_telefone = ft.TextField(label='Telefone', width=300)
        campo_pessoas = ft.TextField(label=f'Pessoas (máx. {capacidade})', width=300,
                                     keyboard_type=ft.KeyboardType.NUMBER)
        campo_data = ft.TextField(label='Data (DD/MM/AAAA)', width=300,
                                  value=datetime.now().strftime('%d/%m/%Y'))
        campo_hora = ft.TextField(label='Hora (HH:MM)', width=300, hint_text='19:30')

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
                snack(page, 'Data ou hora inválida', '#C62828')
                return

            criar_reserva(id_mesa, campo_nome.value.strip(), campo_telefone.value.strip(),
                          pessoas, data_hora)
            page.pop_dialog()
            snack(page, f'Mesa {numero} reservada para {campo_nome.value.strip()}')
            recarregar()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Reservar mesa {numero}'),
            content=ft.Column(
                tight=True, spacing=12,
                controls=[campo_nome, campo_telefone, campo_pessoas, campo_data, campo_hora]
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
        reserva = buscar_reserva(id_mesa)

        conteudo = [
            ft.Text(f'Capacidade: {capacidade} pessoas'),
            ft.Text(f'Situação: {situacao}', weight=ft.FontWeight.BOLD, color=COR[situacao]),
        ]
        acoes = [ft.TextButton('Fechar', on_click=lambda ev: page.pop_dialog())]

        if reserva:
            id_reserva, nome, pessoas, data_hora = reserva
            conteudo.append(
                ft.Text(f'Próxima reserva: {nome}, {pessoas} pessoas, '
                        f'{data_hora:%d/%m às %H:%M}')
            )

            def cancelar(ev):
                cancelar_reserva(id_reserva)
                page.pop_dialog()
                snack(page, 'Reserva cancelada')
                recarregar()

            acoes.append(ft.TextButton('Cancelar reserva', on_click=cancelar))

        if situacao != 'Ocupada':
            acoes.append(
                ft.Button(content=ft.Text('Reservar'),
                          on_click=lambda ev: abrir_reserva(ev, mesa),
                          style=ft.ButtonStyle(bgcolor='#168C8C', color='white'))
            )

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f'Mesa {numero}'),
            content=ft.Column(tight=True, spacing=8, controls=conteudo),
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