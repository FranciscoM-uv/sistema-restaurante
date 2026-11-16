import flet as ft
from conexao import conectar

def buscar_mesas():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute('SELECT numero_mesa, status FROM mesa ORDER BY numero_mesa')
            return cursor.fetchall()
        
def mesas_view(page):
    cards = []
    
    for numero, status in buscar_mesas():
        
        if status == 'Livre':
            cor = '#168C8C'
        else:
            cor = '#C62828'
        card = ft.Container(
            content=ft.Text(str(numero), color='white', size=28, weight=ft.FontWeight.BOLD),
            width=130,
            height=75,
            bgcolor=cor
            
        )
        cards.append(card)
    return ft.Row(
        controls= cards,
        wrap= True
    )
    