import flet as ft
from conexao import conectar


def produtos_view(page):
    nome_produto = ft.TextField(
        label='Nome do produto',
        prefix=ft.Icon(ft.Icons.RESTAURANT_MENU, color='#168C8C'),
        hint_text='Digite o nome do produto',
        width=400
    )
    categoria_produto = ft.Dropdown(
        label='Categoria',
        options=[
            ft.DropdownOption('Prato'),
            ft.DropdownOption('Bebida'),
            ft.DropdownOption('Sobremesa')
        ],
        width=400
    )
    preco_produto = ft.TextField(
        label='Preço',
        prefix=ft.Icon(ft.Icons.ATTACH_MONEY, color='#168C8C'),
        hint_text='Digite o preço',
        input_filter=ft.InputFilter(
            allow=True,
            regex_string=r'^[0-9]*[.,]?[0-9]{0,2}$',
            replacement_string=''
        ),
        width=400
    )

    def cadastrar_produto(e):
        nome_tratado = nome_produto.value.strip().title()

        if not nome_tratado or not categoria_produto.value or not preco_produto.value:
            page.show_dialog(ft.SnackBar(
                content=ft.Text('Preencha nome, categoria e preço', color='white'),
                bgcolor='#E65100'
            ))
            return

        try:
            preco = float(preco_produto.value.replace(',', '.'))

            with conectar() as conexao:
                with conexao.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO produto(nome, categoria, preco) VALUES (%s, %s, %s)',
                        (nome_tratado, categoria_produto.value, preco)
                    )

            nome_produto.value = ''
            categoria_produto.value = None
            preco_produto.value = ''
            page.show_dialog(ft.SnackBar(
                content=ft.Text('Produto cadastrado com sucesso', color='white'),
                bgcolor='#168C8C'
            ))
            page.update()

        except Exception:
            page.show_dialog(ft.SnackBar(
                content=ft.Text('Erro ao cadastrar produto', color='white'),
                bgcolor='#C62828'
            ))

    return ft.Column(
        controls=[
            ft.Text(
                'Cadastro de Produtos',
                size=30,
                weight=ft.FontWeight.BOLD,
                color='#172B4D'
            ),
            nome_produto,
            categoria_produto,
            preco_produto,
            ft.Button(
                content=ft.Text('Cadastrar'),
                on_click=cadastrar_produto,
                style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        spacing=15
    )