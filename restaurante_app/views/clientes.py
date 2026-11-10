import flet as ft
from conexao import conectar


def clientes_view(page):
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