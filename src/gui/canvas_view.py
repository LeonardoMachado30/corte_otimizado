import tkinter as tk
from tkinter import ttk
import math

class CorteCanvasView(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent.frame_esquerdo, **kwargs)
        self.parent = parent
        
        # Configuração do canvas
        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Variáveis de controle
        self.chapas = []
        self.peca_selecionada = None
        self.peca_em_redimensionamento = None
        self.ponto_inicial = None
        self.escala = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.borda_redimensionamento = None  # 'left', 'right', 'top', 'bottom'
        self.dimensoes_iniciais = None
        
        # Configuração dos cursores
        self.cursor_resize_h = "sb_h_double_arrow"
        self.cursor_resize_v = "sb_v_double_arrow"
        self.cursor_default = "arrow"
        
        # Bindings do mouse
        self.canvas.bind('<Motion>', self._on_motion)
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.canvas.bind('<MouseWheel>', self._on_zoom)
        
        # Bindings do teclado
        self.bind_all('<r>', self._rotacionar_peca_selecionada)
        self.bind_all('<Delete>', self._remover_peca_selecionada)
        
    def atualizar_visualizacao(self, chapas, largura_chapa, altura_chapa):
        """Atualiza a visualização com as novas chapas."""
        self.chapas = chapas
        self.largura_chapa = largura_chapa
        self.altura_chapa = altura_chapa
        self._redesenhar()
        
    def _redesenhar(self):
        """Redesenha todo o canvas."""
        self.canvas.delete('all')
        
        # Calcula a escala para caber todas as chapas
        if not self.chapas:
            return
            
        # Calcula dimensões totais
        total_width = self.largura_chapa * len(self.chapas)
        total_height = self.altura_chapa
        
        # Calcula escala para caber na janela
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Evita divisão por zero
            scale_x = (canvas_width - 40) / total_width
            scale_y = (canvas_height - 40) / total_height
            self.escala = min(scale_x, scale_y)
            
        # Desenha as chapas
        for i, chapa in enumerate(self.chapas):
            x = i * self.largura_chapa * self.escala + 20
            y = 20
            
            # Desenha o contorno da chapa
            self.canvas.create_rectangle(
                x, y,
                x + self.largura_chapa * self.escala,
                y + self.altura_chapa * self.escala,
                outline='black', width=2
            )
            
            # Desenha as peças
            for peca in chapa['pecas_alocadas']:
                # Verifica se a peça tem todas as propriedades necessárias
                if not all(key in peca for key in ['x', 'y', 'largura', 'altura']):
                    continue
                    
                px = x + peca['x'] * self.escala
                py = y + peca['y'] * self.escala
                pw = peca['largura'] * self.escala
                ph = peca['altura'] * self.escala
                
                # Define a cor e largura da borda baseado na seleção
                is_selected = (self.peca_selecionada and 
                             self.peca_selecionada['original_idx'] == peca['original_idx'])
                outline_color = 'red' if is_selected else 'blue'
                outline_width = 3 if is_selected else 1
                
                # Cria o retângulo da peça
                rect_id = self.canvas.create_rectangle(
                    px, py, px + pw, py + ph,
                    fill='lightblue', outline=outline_color,
                    width=outline_width,
                    tags=('peca', f"peca_{peca['id']}")
                )
                
                # Adiciona o ID/nome da peça
                self.canvas.create_text(
                    px + pw/2, py + ph/2 - 10,
                    text=peca.get('id_display', peca['id']),
                    tags=('texto', f"texto_id_{peca['id']}")
                )
                
                # Adiciona o texto com as dimensões formatadas com 2 casas decimais
                self.canvas.create_text(
                    px + pw/2, py + ph/2 + 10,
                    text=f"{peca['largura']:.2f}x{peca['altura']:.2f}",
                    tags=('texto', f"texto_dim_{peca['id']}")
                )
                
    def _encontrar_borda(self, x, y, peca, chapa_index=0, margem=10):
        """Encontra qual borda da peça está sendo tocada."""
        px = peca['x']
        py = peca['y']
        pw = peca['largura']
        ph = peca['altura']
        
        # Converte coordenadas do canvas para coordenadas reais
        x_real = (x - (chapa_index * self.largura_chapa * self.escala + 20)) / self.escala
        y_real = (y - 20) / self.escala
        
        # Verifica se está próximo das bordas com margem maior
        if abs(x_real - px) < margem:
            return 'left'
        elif abs(x_real - (px + pw)) < margem:
            return 'right'
        elif abs(y_real - py) < margem:
            return 'top'
        elif abs(y_real - (py + ph)) < margem:
            return 'bottom'
        return None
        
    def _on_motion(self, event):
        """Manipula o movimento do mouse."""
        # Encontra a chapa atual baseado na posição do mouse
        chapa_atual = None
        chapa_index = 0
        
        for i, chapa in enumerate(self.chapas):
            offset_x = i * self.largura_chapa * self.escala + 20
            if offset_x <= event.x <= offset_x + self.largura_chapa * self.escala:
                chapa_atual = chapa
                chapa_index = i
                break
                
        if not chapa_atual:
            self.canvas.config(cursor=self.cursor_default)
            return
            
        # Converte coordenadas do canvas para coordenadas reais
        x = (event.x - (chapa_index * self.largura_chapa * self.escala + 20)) / self.escala
        y = (event.y - 20) / self.escala
        
        # Verifica se está sobre alguma peça
        for peca in chapa_atual['pecas_alocadas']:
            # Verifica se a peça tem todas as propriedades necessárias
            if not all(key in peca for key in ['x', 'y', 'largura', 'altura']):
                continue
                
            if (peca['x'] <= x <= peca['x'] + peca['largura'] and
                peca['y'] <= y <= peca['y'] + peca['altura']):
                
                # Verifica se está em alguma borda
                borda = self._encontrar_borda(event.x, event.y, peca, chapa_index)
                if borda in ['left', 'right']:
                    self.canvas.config(cursor=self.cursor_resize_h)
                elif borda in ['top', 'bottom']:
                    self.canvas.config(cursor=self.cursor_resize_v)
                else:
                    self.canvas.config(cursor=self.cursor_default)
                return
                
        self.canvas.config(cursor=self.cursor_default)
        
    def _on_click(self, event):
        """Manipula o clique do mouse."""
        # Encontra a chapa atual baseado na posição do mouse
        chapa_atual = None
        chapa_index = 0
        
        for i, chapa in enumerate(self.chapas):
            offset_x = i * self.largura_chapa * self.escala + 20
            if offset_x <= event.x <= offset_x + self.largura_chapa * self.escala:
                chapa_atual = chapa
                chapa_index = i
                break
                
        if not chapa_atual:
            self.peca_selecionada = None
            self.peca_em_redimensionamento = None
            self.borda_redimensionamento = None
            self.dimensoes_iniciais = None
            self._redesenhar()
            return
            
        # Converte coordenadas do canvas para coordenadas reais
        x = (event.x - (chapa_index * self.largura_chapa * self.escala + 20)) / self.escala
        y = (event.y - 20) / self.escala
        
        # Encontra a peça clicada
        for peca in chapa_atual['pecas_alocadas']:
            # Verifica se a peça tem todas as propriedades necessárias
            if not all(key in peca for key in ['x', 'y', 'largura', 'altura']):
                continue
                
            if (peca['x'] <= x <= peca['x'] + peca['largura'] and
                peca['y'] <= y <= peca['y'] + peca['altura']):
                
                # Verifica se clicou em alguma borda
                borda = self._encontrar_borda(event.x, event.y, peca, chapa_index)
                if borda:
                    self.peca_em_redimensionamento = peca
                    self.borda_redimensionamento = borda
                    # Armazena as dimensões iniciais
                    self.dimensoes_iniciais = {
                        'x': peca['x'],
                        'y': peca['y'],
                        'largura': peca['largura'],
                        'altura': peca['altura']
                    }
                else:
                    self.peca_selecionada = peca
                    # Notifica a janela principal sobre a seleção
                    self.parent.selecionar_peca_canvas(peca)
                    
                self.ponto_inicial = (event.x, event.y)
                self._redesenhar()
                return
                
        # Se clicou fora de qualquer peça, desmarca a seleção
        self.peca_selecionada = None
        self.peca_em_redimensionamento = None
        self.borda_redimensionamento = None
        self.dimensoes_iniciais = None
        self._redesenhar()
        
    def selecionar_peca(self, peca):
        """Seleciona uma peça no canvas."""
        self.peca_selecionada = peca
        self._redesenhar()
        
    def _on_drag(self, event):
        """Manipula o arrasto do mouse."""
        if not self.peca_em_redimensionamento or not self.ponto_inicial or not self.dimensoes_iniciais:
            return
            
        # Encontra a chapa atual da peça
        chapa_atual = None
        for chapa in self.chapas:
            if self.peca_em_redimensionamento in chapa['pecas_alocadas']:
                chapa_atual = chapa
                break
                
        if not chapa_atual:
            return
            
        # Calcula o offset da chapa atual
        chapa_index = self.chapas.index(chapa_atual)
        offset_x = chapa_index * self.largura_chapa * self.escala + 20
        
        # Converte coordenadas do mouse para coordenadas reais
        x_real = (event.x - offset_x) / self.escala
        y_real = (event.y - 20) / self.escala
        
        # Obtém as dimensões iniciais
        x_inicial = self.dimensoes_iniciais['x']
        y_inicial = self.dimensoes_iniciais['y']
        largura_inicial = self.dimensoes_iniciais['largura']
        altura_inicial = self.dimensoes_iniciais['altura']
        
        # Calcula novas dimensões baseadas na posição exata do mouse
        nova_largura = largura_inicial
        nova_altura = altura_inicial
        novo_x = x_inicial
        novo_y = y_inicial
        
        if self.borda_redimensionamento == 'right':
            nova_largura = max(1, x_real - x_inicial)
        elif self.borda_redimensionamento == 'left':
            nova_largura = max(1, (x_inicial + largura_inicial) - x_real)
            novo_x = x_real
        elif self.borda_redimensionamento == 'bottom':
            nova_altura = max(1, y_real - y_inicial)
        elif self.borda_redimensionamento == 'top':
            nova_altura = max(1, (y_inicial + altura_inicial) - y_real)
            novo_y = y_real
            
        # Verifica se as novas dimensões são válidas
        if nova_largura <= self.largura_chapa and nova_altura <= self.altura_chapa:
            self.peca_em_redimensionamento['x'] = novo_x
            self.peca_em_redimensionamento['y'] = novo_y
            self.peca_em_redimensionamento['largura'] = nova_largura
            self.peca_em_redimensionamento['altura'] = nova_altura
            
            # Atualiza a visualização
            self._redesenhar()
            
    def _on_release(self, event):
        """Manipula o soltar do mouse."""
        if self.peca_em_redimensionamento:
            # Notifica a janela principal sobre a mudança
            self.parent.atualizar_peca_redimensionada(
                self.peca_em_redimensionamento
            )
            # Mantém a seleção da peça após redimensionar
            self.peca_selecionada = self.peca_em_redimensionamento
        self.peca_em_redimensionamento = None
        self.borda_redimensionamento = None
        self.dimensoes_iniciais = None
        self.ponto_inicial = None
        
    def _on_zoom(self, event):
        """Manipula o zoom do mouse."""
        if event.delta > 0:
            self.escala *= 1.1
        else:
            self.escala /= 1.1
        self._redesenhar()
        
    def _rotacionar_peca_selecionada(self, event):
        """Rotaciona a peça selecionada."""
        if self.peca_selecionada:
            largura = self.peca_selecionada['largura']
            altura = self.peca_selecionada['altura']
            
            # Verifica se cabe na chapa após rotação
            if (altura <= self.largura_chapa and
                largura <= self.altura_chapa):
                self.peca_selecionada['largura'] = altura
                self.peca_selecionada['altura'] = largura
                self.peca_selecionada['rotacionada'] = not self.peca_selecionada.get('rotacionada', False)
                self._redesenhar()
                # Notifica a janela principal sobre a mudança
                self.parent.atualizar_peca_redimensionada(self.peca_selecionada)
                
    def _remover_peca_selecionada(self, event):
        """Remove a peça selecionada."""
        if self.peca_selecionada:
            # Notifica a janela principal para remover a peça
            self.parent.remover_peca_selecionada(self.peca_selecionada)
            self.peca_selecionada = None
            self._redesenhar() 