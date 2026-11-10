import flet as ft
from views.clientes import clientes_view
from views.funcionarios import funcionarios_view

def main(page: ft.Page):
    page.title = "Sabor de Goiás"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1100
    page.window.height = 750
    page.padding = 0
    page.bgcolor = "#F4F6F9"
    
    page.appbar = ft.AppBar(bgcolor='#168C8C', title=ft.Text('Sabor de Goiás', color='white'))
    opcoes = [
                "Início",
                "Clientes",
                "Funcionários",
                "Produtos",
                "Mesas",
                "Pedidos"
            ]
    conteudo = ft.Container(expand=True)

    def mostrar_inicio():
        conteudo.content = ft.Column(
            controls=[
                ft.Text(
                    "Painel principal",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color="#172B4D"
                ),
                ft.Text(
                    "Bem-vindo ao sistema Sabor da Terra!",
                    color="#64748B"
                ),
                ft.Row(
                    controls=[
                        card("Clientes", ft.Icons.PEOPLE),
                        card("Funcionários", ft.Icons.BADGE),
                    ],
                    spacing=15
                ),
                ft.Row(
                    controls=[
                        card("Produtos", ft.Icons.RESTAURANT),
                        card("Mesas", ft.Icons.TABLE_RESTAURANT),
                    ],
                    spacing=15
                ),
                card("Pedidos", ft.Icons.RECEIPT_LONG, expand=False)
            ],
            spacing=20
        )
        page.update()

    def card(titulo, icone, expand=True):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icone, size=35, color="#168C8C"),
                    ft.Text(
                        titulo,
                        size=18,
                        weight=ft.FontWeight.BOLD
                    )
                ]
            ),
            bgcolor="white",
            padding=25,
            border_radius=12,
            height=85,
            expand=expand,
            on_click=lambda e: mostrar_tela(titulo)
        )

    def navegar(e):
        selecionado = opcoes[e.control.selected_index]
        mostrar_tela(selecionado)
        
    def mostrar_tela(selecionado):
        menu.selected_index = opcoes.index(selecionado)
        
        if selecionado == "Início":
            mostrar_inicio()
        
        elif selecionado == 'Clientes':
            conteudo.content = clientes_view(page)
            page.update()
            
        elif selecionado == 'Funcionários':
            conteudo.content = funcionarios_view(page)
            page.update()
         
        else:
            conteudo.content = ft.Column(
                controls=[
                    ft.Text(
                        selecionado,
                        size=30,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text("Vamos desenvolver esta seção!")
                ]
            )
            page.update()

    menu = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME,
                label="Início"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE,
                label="Clientes"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.BADGE,
                label="Funcionários"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.RESTAURANT,
                label="Produtos"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.TABLE_RESTAURANT,
                label="Mesas"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.RECEIPT_LONG,
                label="Pedidos"
            ),
        ],
        on_change=navegar
    )

    page.add(
        ft.Row(
            controls=[
                menu,
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=conteudo,
                    expand=True,
                    padding=30
                )
            ],
            expand=True,
            spacing=0
        )
    )

    mostrar_inicio()


ft.run(main)
