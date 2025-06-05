import tkinter as tk
from tkinter import ttk, Menu, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import os

from algoritmo.corte import cortar_chapas
from utils.visualizacao import plotar_chapas_na_figura
from .canvas_view import CorteCanvasView
from .dialog import PecaDialog

class CorteGUI:
    """
    Interface gráfica principal da aplicação de otimização de corte.
    """
    def __init__(self, master):
        self.master = master
        master.title("Otimizador de Corte de Chapas v1.9")
        master.geometry("1000x700")  # Tamanho inicial padrão
        
        # Configuração do grid para redimensionamento
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        
        # Habilita o botão de maximizar
        self.master.resizable(True, True)
        
        # Variável para armazenar a peça copiada
        self.peca_copiada = None
        
        # Variável para controlar a segunda chapa
        self.segunda_chapa_habilitada = True
        
        self._setup_menu()
        self._setup_layout()
        self._setup_variables()
        self._setup_initial_state()
        
        # Bind para redimensionamento da janela
        self.master.bind('<Configure>', self._on_window_resize)
        
        # Bind para tecla F11 (fullscreen)
        self.master.bind('<F11>', self._toggle_fullscreen)
        
        # Bind para CTRL+C e CTRL+V
        self.master.bind('<Control-c>', self._copiar_peca)
        self.master.bind('<Control-v>', self._colar_peca)
        
        # Estado inicial do fullscreen
        self.fullscreen = False

    def _setup_menu(self):
        """Configura o menu da aplicação."""
        menubar = Menu(self.master)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Importar Lista de Peças (Excel)...", 
                           command=self.importar_lista_pecas_excel)
        
        exportmenu = Menu(filemenu, tearoff=0)
        exportmenu.add_command(label="Lista de Peças para Excel...", 
                             command=self.exportar_lista_pecas_para_excel)
        filemenu.add_cascade(label="Exportar", menu=exportmenu)
        filemenu.add_separator()
        filemenu.add_command(label="Sair", command=self.master.quit)
        menubar.add_cascade(label="Arquivo", menu=filemenu)
        self.master.config(menu=menubar)

    def _setup_layout(self):
        """Configura o layout da interface."""
        # Frame principal que ocupa toda a janela
        main_frame = ttk.Frame(self.master)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)  # Coluna do canvas tem peso 1
        
        # Frame esquerdo (menu) - largura fixa de 200px
        self.frame_direito = ttk.Frame(main_frame, width=200)
        self.frame_direito.grid(row=0, column=0, sticky="nsew")
        self.frame_direito.grid_propagate(False)  # Mantém a largura fixa
        
        # Frame direito (canvas) - ocupa o espaço restante
        self.frame_esquerdo = ttk.Frame(main_frame)
        self.frame_esquerdo.grid(row=0, column=1, sticky="nsew")
        
        # Canvas interativo
        self.canvas_view = CorteCanvasView(self)
        self.canvas_view.pack(fill=tk.BOTH, expand=True)
        
        self._setup_chapa_frame()
        self._setup_pecas_frame()
        self._setup_acoes_frame()

    def _setup_chapa_frame(self):
        """Configura o frame de dimensões da chapa."""
        pad_options = {'padx': 5, 'pady': 3}
        chapa_frame = tk.LabelFrame(self.frame_direito, text="Dimensões da Chapa (cm)", **pad_options)
        chapa_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(chapa_frame, text="Largura:").grid(row=0, column=0, sticky="w", **pad_options)
        self.largura_chapa_entry = tk.Entry(
            chapa_frame, 
            width=10,
            validate="key",
            validatecommand=(chapa_frame.register(self._validar_decimal), '%P')
        )
        self.largura_chapa_entry.grid(row=0, column=1, sticky="ew", **pad_options)
        
        tk.Label(chapa_frame, text="Altura:").grid(row=1, column=0, sticky="w", **pad_options)
        self.altura_chapa_entry = tk.Entry(
            chapa_frame, 
            width=10,
            validate="key",
            validatecommand=(chapa_frame.register(self._validar_decimal), '%P')
        )
        self.altura_chapa_entry.grid(row=1, column=1, sticky="ew", **pad_options)
        
        chapa_frame.columnconfigure(1, weight=1)

    def _setup_pecas_frame(self):
        """Configura o frame de peças."""
        pad_options = {'padx': 5, 'pady': 3}
        pecas_frame = tk.LabelFrame(self.frame_direito, text="Peças a Cortar", **pad_options)
        pecas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview para lista de peças
        tree_frame = ttk.Frame(pecas_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.treeview_pecas = ttk.Treeview(
            tree_frame,
            columns=("id_nome", "altura", "largura", "quantidade"),
            show="headings",
            height=5
        )
        
        # Configuração das colunas
        self.treeview_pecas.heading("id_nome", text="ID/Nome")
        self.treeview_pecas.heading("altura", text="Altura")
        self.treeview_pecas.heading("largura", text="Largura")
        self.treeview_pecas.heading("quantidade", text="Qtd.")
        
        self.treeview_pecas.column("id_nome", width=120, anchor=tk.W, stretch=tk.YES)
        self.treeview_pecas.column("altura", width=60, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview_pecas.column("largura", width=60, anchor=tk.CENTER, stretch=tk.YES)
        self.treeview_pecas.column("quantidade", width=40, anchor=tk.CENTER, stretch=tk.NO)
        
        self.treeview_pecas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.treeview_pecas.yview)
        self.treeview_pecas.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind do evento de seleção na treeview
        self.treeview_pecas.bind('<<TreeviewSelect>>', self._on_treeview_select)

        # Botões de controle
        self._setup_pecas_buttons(pecas_frame)

    def _setup_pecas_buttons(self, pecas_frame):
        """Configura os botões de controle das peças."""
        # Primeira linha de botões
        btn_row1_frame = ttk.Frame(pecas_frame)
        btn_row1_frame.pack(fill=tk.X, pady=2)
        
        self.add_peca_btn = tk.Button(
            btn_row1_frame,
            text="Adicionar",
            command=self.adicionar_peca_dialog
        )
        self.add_peca_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.edit_peca_btn = tk.Button(
            btn_row1_frame,
            text="Editar",
            command=self.editar_peca_dialog
        )
        self.edit_peca_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.duplicate_peca_btn = tk.Button(
            btn_row1_frame,
            text="Duplicar",
            command=self.duplicar_peca_selecionada
        )
        self.duplicate_peca_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Segunda linha de botões
        btn_row2_frame = ttk.Frame(pecas_frame)
        btn_row2_frame.pack(fill=tk.X, pady=2)
        
        self.remove_peca_btn = tk.Button(
            btn_row2_frame,
            text="Remover",
            command=self.remover_peca_selecionada
        )
        self.remove_peca_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.undo_remove_btn = tk.Button(
            btn_row2_frame,
            text="Desfazer Remoção",
            command=self.desfazer_remocao,
            state=tk.DISABLED
        )
        self.undo_remove_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Terceira linha de botões
        btn_row3_frame = ttk.Frame(pecas_frame)
        btn_row3_frame.pack(fill=tk.X, pady=2)
        
        self.move_up_btn = tk.Button(
            btn_row3_frame,
            text="Mover Acima ↑",
            command=lambda: self.mover_peca_selecionada("cima")
        )
        self.move_up_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.move_down_btn = tk.Button(
            btn_row3_frame,
            text="Mover Abaixo ↓",
            command=lambda: self.mover_peca_selecionada("baixo")
        )
        self.move_down_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    def _setup_acoes_frame(self):
        """Configura o frame de ações."""
        pad_options = {'padx': 5, 'pady': 3}
        acoes_frame = tk.LabelFrame(self.frame_direito, text="Ações", **pad_options)
        acoes_frame.pack(fill=tk.X, padx=5, pady=(10,5))
        
        # Frame para os botões
        botoes_frame = ttk.Frame(acoes_frame)
        botoes_frame.pack(fill=tk.X, padx=2, pady=5)
        
        # Botão de segunda chapa
        self.segunda_chapa_btn = tk.Button(
            botoes_frame,
            text="Desabilitar Segunda Chapa",
            command=self._toggle_segunda_chapa,
            bg="lightgreen",
            font=('Arial', 10)
        )
        self.segunda_chapa_btn.pack(fill=tk.X, pady=(0,5))
        
        # Botão de otimizar
        self.executar_corte_btn = tk.Button(
            botoes_frame,
            text="Otimizar e Visualizar Cortes",
            command=self.atualizar_visualizacao_e_otimizar,
            bg="lightblue",
            font=('Arial', 10, 'bold')
        )
        self.executar_corte_btn.pack(fill=tk.X)

    def _setup_variables(self):
        """Inicializa as variáveis da aplicação."""
        self.pecas_a_cortar = []
        self.resultado_cortes_otimizado = None
        self.proximo_id_original = 0
        self.ultima_peca_removida_info = None

    def _setup_initial_state(self):
        """Configura o estado inicial da aplicação."""
        self.desenhar_placeholder_visualizacao()

    def desenhar_placeholder_visualizacao(self):
        """Desenha a visualização inicial."""
        self.canvas_view.atualizar_visualizacao([], 0, 0)

    def atualizar_peca_redimensionada(self, peca):
        """Atualiza uma peça após redimensionamento."""
        # Encontra a peça na lista de peças
        for i, p in enumerate(self.pecas_a_cortar):
            if p['original_idx'] == peca['original_idx']:
                # Atualiza as dimensões da peça
                self.pecas_a_cortar[i]['larg'] = peca['largura']
                self.pecas_a_cortar[i]['alt'] = peca['altura']
                
                # Atualiza a treeview imediatamente
                self.atualizar_treeview_pecas()
                
                # Seleciona a peça atualizada na treeview
                if self.treeview_pecas.get_children():
                    iid = self.treeview_pecas.get_children()[i]
                    self.treeview_pecas.selection_set(iid)
                    self.treeview_pecas.focus(iid)
                    self.treeview_pecas.see(iid)
                break
                
        # Atualiza a visualização e otimiza o layout
        self.atualizar_visualizacao_e_otimizar()

    def atualizar_treeview_pecas(self):
        """Atualiza a visualização da lista de peças."""
        # Limpa a treeview
        for item in self.treeview_pecas.get_children():
            self.treeview_pecas.delete(item)
            
        # Adiciona as peças atualizadas
        for p in self.pecas_a_cortar:
            id_d = p.get('id_display', f"P{p['original_idx']+1}")
            self.treeview_pecas.insert("", "end", text=str(p['original_idx']),
                                     values=(id_d, f"{p['alt']:.2f}", f"{p['larg']:.2f}", "1"))

    def remover_peca_selecionada(self, peca=None):
        """Remove a peça selecionada."""
        if peca is None:
            # Se não foi passada uma peça, tenta remover a selecionada no canvas
            if self.canvas_view.peca_selecionada:
                peca = self.canvas_view.peca_selecionada
            else:
                # Tenta obter a peça selecionada na treeview
                selected_items = self.treeview_pecas.selection()
                if selected_items:
                    idx = self.treeview_pecas.index(selected_items[0])
                    if 0 <= idx < len(self.pecas_a_cortar):
                        peca = self.pecas_a_cortar[idx]
                    else:
                        messagebox.showwarning("Aviso", "Selecione uma peça para remover.")
                        return
                else:
                    messagebox.showwarning("Aviso", "Selecione uma peça para remover.")
                    return
                
        # Encontra e remove a peça da lista
        for i, p in enumerate(self.pecas_a_cortar):
            if p['original_idx'] == peca['original_idx']:
                # Armazena informações para possível desfazer
                self.ultima_peca_removida_info = (i, p.copy())
                self.pecas_a_cortar.pop(i)
                break
                
        # Atualiza a visualização
        self.atualizar_treeview_pecas()
        self.atualizar_visualizacao_e_otimizar()
        
        # Limpa a seleção no canvas
        self.canvas_view.peca_selecionada = None
        self.canvas_view.peca_em_redimensionamento = None
        self.canvas_view.borda_redimensionamento = None
        self.canvas_view.dimensoes_iniciais = None
        self.canvas_view._redesenhar()
        
        # Atualiza o estado do botão de desfazer
        self.undo_remove_btn.config(state=tk.NORMAL if self.ultima_peca_removida_info else tk.DISABLED)
        
        # Atualiza o estado dos outros botões
        self.atualizar_menu()

    def atualizar_visualizacao_e_otimizar(self):
        """Atualiza a visualização e otimiza o layout das peças."""
        # Obtém as dimensões da chapa
        largura_chapa = self._validar_dimensoes_chapa(mostrar_erro=True)
        altura_chapa = self._validar_dimensoes_chapa(mostrar_erro=True)
        
        if largura_chapa is None or altura_chapa is None:
            return
            
        # Prepara as peças para o algoritmo
        pecas_exp = []
        for i, peca in enumerate(self.pecas_a_cortar):
            pecas_exp.append({
                'id': peca['id'],
                'larg': peca['larg'],
                'alt': peca['alt'],
                'original_idx': i
            })
            
        # Executa o algoritmo de corte
        self.resultado_cortes_otimizado, nao_alocadas = cortar_chapas(
            largura_chapa, altura_chapa, pecas_exp)
            
        # Se não está habilitada a segunda chapa e há peças não alocadas
        if not self.segunda_chapa_habilitada and nao_alocadas:
            # Verifica se alguma peça excede o limite da chapa
            for peca in nao_alocadas:
                if peca['larg'] > largura_chapa or peca['alt'] > altura_chapa:
                    if self._mostrar_dialog_segunda_chapa(peca):
                        # Reexecuta o algoritmo com segunda chapa habilitada
                        self.resultado_cortes_otimizado, nao_alocadas = cortar_chapas(
                            largura_chapa, altura_chapa, pecas_exp)
                    else:
                        # Se o usuário não quer segunda chapa, mantém apenas a primeira
                        if self.resultado_cortes_otimizado and len(self.resultado_cortes_otimizado) > 1:
                            self.resultado_cortes_otimizado = [self.resultado_cortes_otimizado[0]]
                    break
            
        # Atualiza a visualização
        self.canvas_view.atualizar_visualizacao(
            self.resultado_cortes_otimizado,
            largura_chapa,
            altura_chapa
        )
        
        # Mostra mensagem com peças não alocadas
        if nao_alocadas:
            self._mostrar_pecas_nao_alocadas(nao_alocadas)
            
        # Atualiza o menu
        self.atualizar_menu()

    def _mostrar_pecas_nao_alocadas(self, nao_alocadas):
        """Mostra mensagem com as peças não alocadas."""
        msg = "Peças não alocadas:\n"
        mapa = {}
        
        for p_na in nao_alocadas:
            desc = next((item for item in self.pecas_a_cortar
                        if item["original_idx"] == p_na['original_idx']), None)
            if desc:
                nome = f"{desc.get('id_display','P')} ({desc['larg']}x{desc['alt']})"
                mapa[nome] = mapa.get(nome, 0) + 1
                
        for nome, qtd in mapa.items():
            msg += f"- {nome}: {qtd} un.\n"
            
        messagebox.showwarning("Aviso de Otimização", msg)

    def _get_selected_treeview_index(self):
        """Retorna o índice da peça selecionada na treeview."""
        selected_item_id = self.treeview_pecas.focus()
        if selected_item_id:
            try:
                return self.treeview_pecas.index(selected_item_id)
            except tk.TclError:
                return None
        return None

    def _validar_decimal(self, valor):
        """Valida se o valor é um número decimal válido com até 2 casas decimais."""
        if valor == "":
            return True
        try:
            if valor.count('.') > 1:
                return False
            if valor.count('.') == 1:
                parte_decimal = valor.split('.')[1]
                if len(parte_decimal) > 2:
                    return False
            float(valor)
            return True
        except ValueError:
            return False

    def _validar_dimensoes_chapa(self, mostrar_erro=True):
        """Valida as dimensões da chapa."""
        try:
            # Verifica se os campos estão vazios
            largura_texto = self.largura_chapa_entry.get().strip()
            altura_texto = self.altura_chapa_entry.get().strip()
            
            if not largura_texto or not altura_texto:
                return None
                
            valor = float(largura_texto if self.largura_chapa_entry.focus_get() == self.largura_chapa_entry else altura_texto)
            
            if valor <= 0:
                if mostrar_erro:
                    messagebox.showerror("Erro",
                                       "Dimensões da chapa devem ser números positivos.")
                return None
                
            return valor
            
        except ValueError:
            if mostrar_erro:
                messagebox.showerror("Erro",
                                   "Dimensões da chapa devem ser números válidos.")
            return None

    def adicionar_peca_dialog(self):
        """Abre diálogo para adicionar nova peça."""
        d = PecaDialog(self.master, title="Adicionar Peça")
        if d.result:
            npi = d.result
            quantidade = npi.get('quant', 1)
            
            # Remove a quantidade do dicionário original
            if 'quant' in npi:
                del npi['quant']
            
            # Cria cópias independentes da peça
            for i in range(quantidade):
                nova_peca = npi.copy()
                nova_peca['original_idx'] = self.proximo_id_original
                
                if not nova_peca.get('id'):
                    nova_peca['id'] = f"P{self.proximo_id_original+1}"
                    
                nova_peca['id_display'] = nova_peca['id']
                
                # Valida se as dimensões cabem na chapa
                largura_chapa = self._validar_dimensoes_chapa()
                altura_chapa = self._validar_dimensoes_chapa()
                if largura_chapa is None or altura_chapa is None:
                    return
                    
                if nova_peca['larg'] > largura_chapa or nova_peca['alt'] > altura_chapa:
                    messagebox.showerror(
                        "Erro",
                        f"As dimensões da peça ({nova_peca['larg']}x{nova_peca['alt']}) "
                        f"excedem as dimensões da chapa ({largura_chapa}x{altura_chapa})."
                    )
                    return
                    
                self.pecas_a_cortar.append(nova_peca)
                self.proximo_id_original += 1
            
            self.atualizar_treeview_pecas()
            self.atualizar_visualizacao_e_otimizar()
            self.undo_remove_btn.config(state=tk.DISABLED)
            self.ultima_peca_removida_info = None

    def editar_peca_dialog(self):
        """Abre diálogo para editar peça selecionada."""
        idx = self._get_selected_treeview_index()
        if idx is None:
            messagebox.showwarning("Aviso", "Selecione uma peça para editar.")
            return
            
        # Prepara os dados iniciais para o diálogo
        peca_atual = self.pecas_a_cortar[idx]
        dados_iniciais = {
            'id': peca_atual.get('id', ''),
            'larg': peca_atual['larg'],
            'alt': peca_atual['alt'],
            'quant': peca_atual.get('quant', 1)
        }
            
        d = PecaDialog(self.master,
                      title="Editar Peça",
                      initial_data=dados_iniciais)
                      
        if d.result:
            self.pecas_a_cortar[idx] = d.result
            self.pecas_a_cortar[idx]['id_display'] = self.pecas_a_cortar[idx]['id']
            
            self.atualizar_treeview_pecas()
            self.atualizar_visualizacao_e_otimizar()
            self.undo_remove_btn.config(state=tk.DISABLED)
            self.ultima_peca_removida_info = None

    def duplicar_peca_selecionada(self):
        """Duplica a peça selecionada."""
        idx = self._get_selected_treeview_index()
        if idx is None:
            messagebox.showwarning("Aviso", "Selecione uma peça para duplicar.")
            return
            
        orig = self.pecas_a_cortar[idx]
        dup = orig.copy()
        dup['original_idx'] = self.proximo_id_original
        dup['id'] = f"{orig.get('id','P')} (Cópia)"
        dup['id_display'] = dup['id']
        
        self.pecas_a_cortar.append(dup)
        self.proximo_id_original += 1
        
        self.atualizar_treeview_pecas()
        
        if self.treeview_pecas.get_children():
            last_iid = self.treeview_pecas.get_children()[-1]
            self.treeview_pecas.selection_set(last_iid)
            self.treeview_pecas.focus(last_iid)
            self.treeview_pecas.see(last_iid)
            
        self.atualizar_visualizacao_e_otimizar()
        self.undo_remove_btn.config(state=tk.DISABLED)
        self.ultima_peca_removida_info = None

    def desfazer_remocao(self):
        """Desfaz a última remoção de peça."""
        if self.ultima_peca_removida_info:
            idx, p = self.ultima_peca_removida_info
            self.pecas_a_cortar.insert(idx, p)
            self.atualizar_treeview_pecas()
            
            if idx < len(self.treeview_pecas.get_children()):
                iid_to_select = self.treeview_pecas.get_children()[idx]
                self.treeview_pecas.selection_set(iid_to_select)
                self.treeview_pecas.focus(iid_to_select)
                self.treeview_pecas.see(iid_to_select)
                
            self.atualizar_visualizacao_e_otimizar()
            self.ultima_peca_removida_info = None
            self.undo_remove_btn.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("Info", "Nada para desfazer.")

    def mover_peca_selecionada(self, direcao):
        """Move a peça selecionada para cima ou para baixo na lista."""
        idx_a = self._get_selected_treeview_index()
        if idx_a is None:
            messagebox.showwarning("Aviso", "Selecione uma peça para mover.")
            return
            
        n_pecas = len(self.pecas_a_cortar)
        idx_n = -1
        
        if direcao == "cima" and idx_a > 0:
            idx_n = idx_a - 1
            self.pecas_a_cortar[idx_a], self.pecas_a_cortar[idx_n] = (
                self.pecas_a_cortar[idx_n], self.pecas_a_cortar[idx_a])
        elif direcao == "baixo" and idx_a < n_pecas - 1:
            idx_n = idx_a + 1
            self.pecas_a_cortar[idx_a], self.pecas_a_cortar[idx_n] = (
                self.pecas_a_cortar[idx_n], self.pecas_a_cortar[idx_a])
        else:
            return
            
        if idx_n != -1:
            self.atualizar_treeview_pecas()
            
            if (self.treeview_pecas.get_children() and
                0 <= idx_n < len(self.treeview_pecas.get_children())):
                iid_to_select = self.treeview_pecas.get_children()[idx_n]
                self.treeview_pecas.selection_set(iid_to_select)
                self.treeview_pecas.focus(iid_to_select)
                self.treeview_pecas.see(iid_to_select)
                
            self.atualizar_visualizacao_e_otimizar()
            self.undo_remove_btn.config(state=tk.DISABLED)
            self.ultima_peca_removida_info = None

    def importar_lista_pecas_excel(self):
        """Importa lista de peças de arquivo Excel."""
        if self.pecas_a_cortar and not messagebox.askyesno(
            "Confirmar Importação",
            "Isso substituirá a lista de peças atual. Deseja continuar?"):
            return
            
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo Excel com lista de peças",
            filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
            defaultextension=".xlsx"
        )
        
        if not filepath:
            return
            
        try:
            df = pd.read_excel(filepath)
            col_map = {'id': None, 'largura': None, 'altura': None, 'quantidade': None}
            
            # Mapeamento de colunas
            std_id_col = 'ID/Nome da Peça'
            std_alt_col = 'Altura (cm)'
            std_larg_col = 'Largura (cm)'
            std_quant_col = 'Quantidade'
            
            possible_id_cols = [std_id_col.lower(), 'id', 'nome', 'id peça', 'id_peca', 'id/nome']
            possible_larg_cols = [std_larg_col.lower(), 'largura', 'larg']
            possible_alt_cols = [std_alt_col.lower(), 'altura', 'alt']
            possible_quant_cols = [std_quant_col.lower(), 'qtd.', 'qtd', 'quant']
            
            # Identifica as colunas no arquivo
            for col in df.columns:
                col_lower = str(col).lower()
                if not col_map['id'] and col_lower in possible_id_cols:
                    col_map['id'] = col
                elif not col_map['largura'] and col_lower in possible_larg_cols:
                    col_map['largura'] = col
                elif not col_map['altura'] and col_lower in possible_alt_cols:
                    col_map['altura'] = col
                elif not col_map['quantidade'] and col_lower in possible_quant_cols:
                    col_map['quantidade'] = col
                    
            # Verifica se todas as colunas foram encontradas
            if not all(col_map.values()):
                missing = [k for k, v in col_map.items() if v is None]
                messagebox.showerror(
                    "Erro de Importação",
                    f"Não foi possível encontrar as colunas: {', '.join(missing)}.\n"
                    f"Verifique se o Excel contém colunas como '{std_id_col}', "
                    f"'{std_alt_col}', '{std_larg_col}', '{std_quant_col}'."
                )
                return
                
            # Processa as peças
            novas_pecas = []
            temp_proximo_id_original = 0
            
            for index, row in df.iterrows():
                try:
                    peca_id = str(row[col_map['id']])
                    largura = int(row[col_map['largura']])
                    altura = int(row[col_map['altura']])
                    quantidade = int(row[col_map['quantidade']])
                    
                    if largura <= 0 or altura <= 0 or quantidade <= 0:
                        raise ValueError(
                            f"Dados inválidos na linha {index+2}: "
                            "Dimensões/quantidade devem ser positivas."
                        )
                        
                    novas_pecas.append({
                        'id': peca_id,
                        'larg': largura,
                        'alt': altura,
                        'quant': quantidade,
                        'original_idx': temp_proximo_id_original,
                        'id_display': peca_id
                    })
                    temp_proximo_id_original += 1
                    
                except ValueError as ve:
                    messagebox.showwarning(
                        "Aviso de Importação",
                        f"Ignorando linha {index+2} do Excel: {ve}"
                    )
                    continue
                except KeyError as ke:
                    messagebox.showwarning(
                        "Aviso de Importação",
                        f"Ignorando linha {index+2} do Excel: coluna {ke} não encontrada."
                    )
                    continue
                    
            if novas_pecas:
                self.pecas_a_cortar = novas_pecas
                self.proximo_id_original = temp_proximo_id_original
                
                self.atualizar_treeview_pecas()
                self.atualizar_visualizacao_e_otimizar()
                self.undo_remove_btn.config(state=tk.DISABLED)
                self.ultima_peca_removida_info = None
                self.resultado_cortes_otimizado = None
                
                messagebox.showinfo(
                    "Importação Concluída",
                    f"{len(novas_pecas)} grupo(s) de peças importado(s) com sucesso!"
                )
            else:
                messagebox.showwarning(
                    "Importação",
                    "Nenhuma peça válida encontrada no arquivo Excel para importar."
                )
                self.desenhar_placeholder_visualizacao()
                
        except Exception as e:
            messagebox.showerror(
                "Erro de Importação",
                f"Ocorreu um erro ao importar o arquivo Excel:\n{e}"
            )
            self.desenhar_placeholder_visualizacao()

    def exportar_lista_pecas_para_excel(self):
        """Exporta a lista de peças para arquivo Excel."""
        if not self.pecas_a_cortar:
            messagebox.showwarning("Exportar Lista",
                                 "Não há peças na lista para exportar.")
            return
            
        col_id = 'ID/Nome da Peça'
        col_alt = 'Altura (cm)'
        col_larg = 'Largura (cm)'
        col_quant = 'Quantidade'
        
        dados_para_exportar = []
        for peca in self.pecas_a_cortar:
            dados_para_exportar.append({
                col_id: peca.get('id_display', peca.get('id', '')),
                col_alt: peca['alt'],
                col_larg: peca['larg'],
                col_quant: peca['quant']
            })
            
        df = pd.DataFrame(dados_para_exportar,
                         columns=[col_id, col_alt, col_larg, col_quant])
                         
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
                title="Exportar Lista de Peças como...",
                initialdir=os.getcwd()
            )
            
            if filepath:
                df.to_excel(filepath, index=False)
                messagebox.showinfo("Sucesso",
                                  f"Lista de peças exportada para:\n{filepath}")
                                  
        except Exception as e:
            messagebox.showerror("Erro ao Exportar",
                               f"Não foi possível exportar a lista de peças.\nErro: {e}")

    def selecionar_peca_canvas(self, peca):
        """Seleciona uma peça no canvas e destaca no menu."""
        # Encontra o índice da peça na lista
        for i, p in enumerate(self.pecas_a_cortar):
            if p['original_idx'] == peca['original_idx']:
                # Seleciona a peça na treeview
                if self.treeview_pecas.get_children():
                    iid = self.treeview_pecas.get_children()[i]
                    self.treeview_pecas.selection_set(iid)
                    self.treeview_pecas.focus(iid)
                    self.treeview_pecas.see(iid)
                break

    def _on_treeview_select(self, event):
        """Manipula a seleção de uma peça na treeview."""
        selected_items = self.treeview_pecas.selection()
        if not selected_items:
            return
            
        # Obtém o índice da peça selecionada
        idx = self.treeview_pecas.index(selected_items[0])
        if 0 <= idx < len(self.pecas_a_cortar):
            # Encontra a peça correspondente no resultado do corte
            peca_original = self.pecas_a_cortar[idx]
            for chapa in self.resultado_cortes_otimizado:
                for peca in chapa['pecas_alocadas']:
                    if peca['original_idx'] == peca_original['original_idx']:
                        # Seleciona a peça no canvas
                        self.canvas_view.selecionar_peca(peca)
                        return 

    def _on_window_resize(self, event):
        """Manipula o redimensionamento da janela."""
        if event.widget == self.master:
            # Só atualiza a visualização se houver peças para mostrar
            if self.pecas_a_cortar:
                self.atualizar_visualizacao_e_otimizar()

    def _toggle_fullscreen(self, event=None):
        """Alterna entre modo tela cheia e normal."""
        self.fullscreen = not self.fullscreen
        self.master.attributes('-fullscreen', self.fullscreen)
        
    def _setup_initial_state(self):
        """Configura o estado inicial da aplicação."""
        self.desenhar_placeholder_visualizacao() 

    def atualizar_menu(self):
        """Atualiza o estado dos botões do menu."""
        # Atualiza o estado do botão de desfazer
        self.undo_remove_btn.config(state=tk.NORMAL if self.ultima_peca_removida_info else tk.DISABLED)
        
        # Atualiza o estado dos botões de edição
        tem_pecas = len(self.pecas_a_cortar) > 0
        self.edit_peca_btn.config(state=tk.NORMAL if tem_pecas else tk.DISABLED)
        self.duplicate_peca_btn.config(state=tk.NORMAL if tem_pecas else tk.DISABLED)
        self.remove_peca_btn.config(state=tk.NORMAL if tem_pecas else tk.DISABLED)
        self.move_up_btn.config(state=tk.NORMAL if tem_pecas else tk.DISABLED)
        self.move_down_btn.config(state=tk.NORMAL if tem_pecas else tk.DISABLED)
        
        # Limpa a seleção se não houver peças
        if not tem_pecas:
            self.canvas_view.peca_selecionada = None
            self.canvas_view.peca_em_redimensionamento = None
            self.canvas_view.borda_redimensionamento = None
            self.canvas_view.dimensoes_iniciais = None
            self.canvas_view._redesenhar()

    def _copiar_peca(self, event=None):
        """Copia a peça selecionada para a área de transferência."""
        if self.canvas_view.peca_selecionada:
            # Encontra a peça original na lista
            for peca in self.pecas_a_cortar:
                if peca['original_idx'] == self.canvas_view.peca_selecionada['original_idx']:
                    # Cria uma cópia da peça
                    self.peca_copiada = {
                        'id': peca['id'],
                        'larg': peca['larg'],
                        'alt': peca['alt'],
                        'quant': peca.get('quant', 1)
                    }
                    messagebox.showinfo("Copiar", "Peça copiada com sucesso!")
                    break
        else:
            messagebox.showwarning("Aviso", "Selecione uma peça para copiar.")

    def _colar_peca(self, event=None):
        """Cola a peça copiada como uma nova peça."""
        if not self.peca_copiada:
            messagebox.showwarning("Aviso", "Nenhuma peça copiada para colar.")
            return
            
        # Cria uma nova peça baseada na copiada
        nova_peca = self.peca_copiada.copy()
        nova_peca['original_idx'] = self.proximo_id_original
        nova_peca['id'] = f"{nova_peca['id']} (Cópia)"
        nova_peca['id_display'] = nova_peca['id']
        
        # Valida se as dimensões cabem na chapa
        largura_chapa = self._validar_dimensoes_chapa()
        altura_chapa = self._validar_dimensoes_chapa()
        if largura_chapa is None or altura_chapa is None:
            return
            
        if nova_peca['larg'] > largura_chapa or nova_peca['alt'] > altura_chapa:
            messagebox.showerror(
                "Erro",
                f"As dimensões da peça ({nova_peca['larg']}x{nova_peca['alt']}) "
                f"excedem as dimensões da chapa ({largura_chapa}x{altura_chapa})."
            )
            return
            
        self.pecas_a_cortar.append(nova_peca)
        self.proximo_id_original += 1
        
        self.atualizar_treeview_pecas()
        self.atualizar_visualizacao_e_otimizar()
        self.undo_remove_btn.config(state=tk.DISABLED)
        self.ultima_peca_removida_info = None
        
        # Seleciona a nova peça na treeview
        if self.treeview_pecas.get_children():
            last_iid = self.treeview_pecas.get_children()[-1]
            self.treeview_pecas.selection_set(last_iid)
            self.treeview_pecas.focus(last_iid)
            self.treeview_pecas.see(last_iid) 

    def _toggle_segunda_chapa(self):
        """Alterna o estado da segunda chapa."""
        self.segunda_chapa_habilitada = not self.segunda_chapa_habilitada
        if self.segunda_chapa_habilitada:
            self.segunda_chapa_btn.config(text="Desabilitar Segunda Chapa", bg="lightgreen")
        else:
            self.segunda_chapa_btn.config(text="Habilitar Segunda Chapa", bg="lightcoral")
            # Remove a segunda chapa se existir
            if self.resultado_cortes_otimizado and len(self.resultado_cortes_otimizado) > 1:
                self.resultado_cortes_otimizado = [self.resultado_cortes_otimizado[0]]
                self.atualizar_visualizacao_e_otimizar()

    def _mostrar_dialog_segunda_chapa(self, peca):
        """Mostra diálogo para adicionar peça na segunda chapa."""
        msg = f"A peça {peca.get('id_display', peca['id'])} excede o limite da chapa.\n"
        msg += "Deseja adicionar uma segunda chapa?"
        
        if messagebox.askyesno("Segunda Chapa", msg):
            self.segunda_chapa_habilitada = True
            self.segunda_chapa_btn.config(text="Desabilitar Segunda Chapa", bg="lightgreen")
            return True
        return False 