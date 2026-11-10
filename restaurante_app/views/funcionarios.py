import flet as ft
from conexao import conectar


def funcionarios_view(page):
    nome_funcionario = ft.TextField(
        label='Nome',
        prefix=ft.Icon(ft.Icons.PERSON, color='#168C8C'),
        hint_text='Digite o nome',
        width=400
    )
    cargo_funcionario = ft.TextField(
        label='Cargo do Funcionário',
        prefix=ft.Icon(ft.Icons.WORK, color='#168C8C'),
        hint_text='Digite qual é o cargo',
        width=400
    )
    
    def cadastro_funcionario(e):
        if not nome_funcionario.value or not cargo_funcionario.value:
                page.show_dialog(ft.SnackBar(content=ft.Text('Preencha com nome e cargo', bgcolor='#E65100'),
                                             color='white'))
                return
        
        try:
            with conectar() as conexao:
                with conexao.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO funcionario(nome, cargo) VALUES (%s, %s)',
                        (nome_funcionario.value, cargo_funcionario.value)
                    )
        
            nome_funcionario.value = ''
            cargo_funcionario.value = ''
            page.show_dialog(ft.SnackBar(content=ft.Text('Cadastro com sucesso', color='white'),
                                                 bgcolor='#168C8C'))
            page.update()
        
        except Exception:
            page.show_dialog(ft.SnackBar(content=ft.Text('Erro ao cadastrar funcionário', color='white'),
                                                 bgcolor='#C62828'))
        
    return ft.Column(
        controls=[
            ft.Text(
                "Cadastro de Funcionários",
                size=30,
                weight=ft.FontWeight.BOLD,
                color="#172B4D"
            ),
            nome_funcionario,
            cargo_funcionario,
            ft.Button(
                content=ft.Text('Cadastrar'),
                on_click=cadastro_funcionario,
                style=ft.ButtonStyle(bgcolor='#168C8C', color='white')
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        spacing=15
    )
