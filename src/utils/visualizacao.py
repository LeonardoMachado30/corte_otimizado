import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plotar_chapas_na_figura(figura, chapas_utilizadas, largura_chapa, altura_chapa):
    """
    Plota as chapas e peças na figura matplotlib.
    
    Args:
        figura (matplotlib.figure.Figure): Figura onde será feito o plot
        chapas_utilizadas (list): Lista de chapas com suas peças alocadas
        largura_chapa (int): Largura da chapa em centímetros
        altura_chapa (int): Altura da chapa em centímetros
    """
    figura.clear()
    n_chapas = len(chapas_utilizadas)
    
    if n_chapas == 0:
        ax = figura.add_subplot(111)
        ax.text(0.5, 0.5, "Nenhuma peça foi alocada.",
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return

    n_cols = min(3, n_chapas)
    n_rows = (n_chapas + n_cols - 1) // n_cols

    for idx, chapa in enumerate(chapas_utilizadas):
        ax = figura.add_subplot(n_rows, n_cols, idx + 1)
        
        # Desenha a chapa
        rect = patches.Rectangle((0, 0), largura_chapa, altura_chapa,
                                linewidth=1, edgecolor='black', facecolor='none')
        ax.add_patch(rect)
        
        # Desenha as peças
        for peca in chapa['pecas_alocadas']:
            rect = patches.Rectangle(
                (peca['x'], peca['y']),
                peca['largura'],
                peca['altura'],
                linewidth=1,
                edgecolor='black',
                facecolor='lightblue',
                alpha=0.5
            )
            ax.add_patch(rect)
            
            # Adiciona o ID da peça
            ax.text(
                peca['x'] + peca['largura']/2,
                peca['y'] + peca['altura']/2,
                peca['id'],
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=8
            )
        
        ax.set_title(f'Chapa {chapa["id_chapa"]}')
        ax.set_xlim(0, largura_chapa)
        ax.set_ylim(0, altura_chapa)
        ax.set_aspect('equal')
        ax.grid(True)
        
    figura.tight_layout()
    figura.canvas.draw_idle() 