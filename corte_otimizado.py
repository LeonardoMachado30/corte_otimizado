import tkinter as tk
from tkinter import ttk, Menu
from tkinter import messagebox, simpledialog, filedialog
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import os

# --- Algoritmo de Corte ---
def cortar_chapas(largura_chapa_cm, altura_chapa_cm, pecas_cm_com_id_e_qtd_original):
    chapas_utilizadas = []
    pecas_para_alocar_geral = sorted(
        [dict(p) for p in pecas_cm_com_id_e_qtd_original],
        key=lambda p: p['larg'] * p['alt'], 
        reverse=True
    )
    pecas_nao_alocadas_final = []
    chapa_idx_global = 0

    while pecas_para_alocar_geral:
        chapa_idx_global += 1
        chapa_atual = {
            'id_chapa': chapa_idx_global, 'largura_total': largura_chapa_cm,
            'altura_total': altura_chapa_cm, 'pecas_alocadas': [],
            'espacos_disponiveis': [(0,0,largura_chapa_cm,altura_chapa_cm)]}
        alguma_peca_foi_colocada_na_chapa_idx_global = False

        while True: # Loop para saturar a chapa atual
            peca_colocada_nesta_passada_na_chapa = False
            idx_iter_peca_geral = 0
            while idx_iter_peca_geral < len(pecas_para_alocar_geral):
                peca_candidata = pecas_para_alocar_geral[idx_iter_peca_geral]
                orientacoes_peca = [(peca_candidata['larg'], peca_candidata['alt'], False)]
                if peca_candidata['larg'] != peca_candidata['alt']:
                    orientacoes_peca.append((peca_candidata['alt'], peca_candidata['larg'], True))
                
                peca_candidata_foi_efetivamente_colocada = False
                melhor_encaixe_para_peca_candidata = None 

                for larg_orient, alt_orient, status_rotacao in orientacoes_peca:
                    melhor_espaco_para_esta_orientacao = None
                    for idx_espaco_na_lista, espaco_tupla_atual in enumerate(chapa_atual['espacos_disponiveis']):
                        ex, ey, ew, eh = espaco_tupla_atual
                        if larg_orient <= ew and alt_orient <= eh:
                            pontuacao_atual = float('inf')
                            if larg_orient == ew and alt_orient == eh: 
                                pontuacao_atual = 0  
                            elif alt_orient == eh: 
                                pontuacao_atual = 100000 + (ew - larg_orient) 
                            elif larg_orient == ew: 
                                pontuacao_atual = 200000 + (eh - alt_orient) 
                            else: 
                                pontuacao_atual = 300000 + (ew * eh) - (larg_orient * alt_orient) 

                            if melhor_espaco_para_esta_orientacao is None or pontuacao_atual < melhor_espaco_para_esta_orientacao[2]:
                                melhor_espaco_para_esta_orientacao = (espaco_tupla_atual, idx_espaco_na_lista, pontuacao_atual)
                    
                    if melhor_espaco_para_esta_orientacao:
                        if melhor_encaixe_para_peca_candidata is None or melhor_espaco_para_esta_orientacao[2] < melhor_encaixe_para_peca_candidata[5]:
                            esp_tupla, idx_esp, pont_esp = melhor_espaco_para_esta_orientacao
                            melhor_encaixe_para_peca_candidata = (
                                larg_orient, alt_orient, status_rotacao,
                                esp_tupla, idx_esp, pont_esp
                            )
                
                if melhor_encaixe_para_peca_candidata:
                    larg_final, alt_final, rot_final, esp_final, idx_esp_pop, _ = melhor_encaixe_para_peca_candidata
                    ex, ey, ew, eh = esp_final

                    chapa_atual['pecas_alocadas'].append({
                        'id': peca_candidata['id'], 'x': ex, 'y': ey,
                        'largura': larg_final, 'altura': alt_final,
                        'original_idx': peca_candidata['original_idx'], 'rotacionada': rot_final
                    })
                    chapa_atual['espacos_disponiveis'].pop(idx_esp_pop)
                    novos_espacos = []
                    if ew - larg_final > 0: novos_espacos.append((ex + larg_final, ey, ew - larg_final, eh))
                    if eh - alt_final > 0: novos_espacos.append((ex, ey + alt_final, larg_final, eh - alt_final))
                    chapa_atual['espacos_disponiveis'].extend(novos_espacos)
                    
                    pecas_para_alocar_geral.pop(idx_iter_peca_geral)
                    peca_colocada_nesta_passada_na_chapa = True
                    alguma_peca_foi_colocada_na_chapa_idx_global = True
                    peca_candidata_foi_efetivamente_colocada = True 
                
                if not peca_candidata_foi_efetivamente_colocada:
                    idx_iter_peca_geral += 1
            
            if not peca_colocada_nesta_passada_na_chapa:
                break 
        
        if chapa_atual['pecas_alocadas']:
            chapas_utilizadas.append(chapa_atual)
        elif not alguma_peca_foi_colocada_na_chapa_idx_global and pecas_para_alocar_geral:
            pecas_nao_alocadas_final.extend(pecas_para_alocar_geral)
            pecas_para_alocar_geral.clear()
            break
            
    if pecas_para_alocar_geral:
        pecas_nao_alocadas_final.extend(pecas_para_alocar_geral)
    return chapas_utilizadas, pecas_nao_alocadas_final

# --- Funções Auxiliares de Plotagem ---
def plotar_chapas_todas(chapas_resultado, largura_chapa_cm, altura_chapa_cm):
    num_chapas = len(chapas_resultado)
    if num_chapas == 0: messagebox.showinfo("Resultado", "Nenhuma chapa utilizada."); return
    cols=2; rows=(num_chapas+cols-1)//cols
    fig,axes = plt.subplots(rows,cols,figsize=(7*cols,5*rows),squeeze=False)
    fig.suptitle("Planos de Corte Otimizados (cm)", fontsize=16)
    for idx, chapa_info in enumerate(chapas_resultado):
        row_idx=idx//cols; col_idx=idx%cols; ax=axes[row_idx,col_idx]
        ax.set_title(f'Chapa {chapa_info["id_chapa"]}'); ax.set_xlim(0,largura_chapa_cm); ax.set_ylim(0,altura_chapa_cm)
        ax.set_aspect('equal',adjustable='box'); ax.invert_yaxis()
        ax.add_patch(patches.Rectangle((0,0),largura_chapa_cm,altura_chapa_cm,fill=False,edgecolor='black',lw=0.5))
        pecas_na_chapa = chapa_info['pecas_alocadas']; num_pecas_na_chapa = len(pecas_na_chapa)
        for i, peca in enumerate(pecas_na_chapa):
            x,y,w,h=peca['x'],peca['y'],peca['largura'],peca['altura']; id_texto=peca.get("id","")
            cor_face = plt.cm.get_cmap('viridis', num_pecas_na_chapa if num_pecas_na_chapa > 0 else 1)(i/num_pecas_na_chapa if num_pecas_na_chapa > 1 else 0.5)
            rect = patches.Rectangle((x,y),w,h,edgecolor='black',facecolor=cor_face,lw=1,alpha=0.75); ax.add_patch(rect)
            texto_cor = 'white' if (cor_face[0]*0.299 + cor_face[1]*0.587 + cor_face[2]*0.114) < 0.5 else 'black'
            ax.text(x+w/2, y+h/2, f'{id_texto}\n{w}x{h}', ha='center',va='center',fontsize=7,color=texto_cor)
        ax.set_xlabel('Largura (cm)'); ax.set_ylabel('Altura (cm)'); ax.grid(True,linestyle=':',linewidth=0.5,alpha=0.7)
    for idx in range(num_chapas, rows*cols): row_idx=idx//cols; col_idx=idx%cols; fig.delaxes(axes[row_idx,col_idx])
    plt.tight_layout(rect=[0,0,1,0.96]); plt.show()

class CorteGUI:
    def __init__(self, master):
        self.master = master
        master.title("Otimizador de Corte de Chapas v1.8") 
        master.resizable(width=False, height=False)

        menubar = Menu(master)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Importar Lista de Peças (Excel)...", command=self.importar_lista_pecas_excel)
        exportmenu = Menu(filemenu, tearoff=0)
        exportmenu.add_command(label="Lista de Peças para Excel...", command=self.exportar_lista_pecas_para_excel)
        filemenu.add_cascade(label="Exportar", menu=exportmenu)
        filemenu.add_separator()
        filemenu.add_command(label="Sair", command=master.quit)
        menubar.add_cascade(label="Arquivo", menu=filemenu)
        master.config(menu=menubar)
        
        pad_options = {'padx': 5, 'pady': 3}
        sticky_options = {'sticky': "ew"}

        chapa_frame = tk.LabelFrame(master, text="Dimensões da Chapa (cm)", **pad_options)
        chapa_frame.grid(row=0, column=0, columnspan=2, **pad_options, **sticky_options)
        tk.Label(chapa_frame, text="Largura:").grid(row=0, column=0, sticky="w", **pad_options)
        self.largura_chapa_entry = tk.Entry(chapa_frame, width=10); self.largura_chapa_entry.grid(row=0,column=1,sticky="ew",**pad_options); self.largura_chapa_entry.insert(0,"275")
        tk.Label(chapa_frame, text="Altura:").grid(row=1, column=0, sticky="w", **pad_options)
        self.altura_chapa_entry = tk.Entry(chapa_frame, width=10); self.altura_chapa_entry.grid(row=1,column=1,sticky="ew",**pad_options); self.altura_chapa_entry.insert(0,"200")
        chapa_frame.columnconfigure(1, weight=1)

        pecas_frame = tk.LabelFrame(master, text="Peças a Cortar", **pad_options)
        pecas_frame.grid(row=1, column=0, columnspan=2, **pad_options, **sticky_options)
        self.treeview_pecas = ttk.Treeview(pecas_frame, columns=("id_nome","altura","largura","quantidade"),show="headings",height=7)
        self.treeview_pecas.heading("id_nome",text="ID/Nome"); self.treeview_pecas.heading("altura",text="Altura (cm)")
        self.treeview_pecas.heading("largura",text="Largura (cm)"); self.treeview_pecas.heading("quantidade",text="Qtd.")
        self.treeview_pecas.column("id_nome",width=150,anchor=tk.W); self.treeview_pecas.column("altura",width=80,anchor=tk.CENTER)
        self.treeview_pecas.column("largura",width=80,anchor=tk.CENTER); self.treeview_pecas.column("quantidade",width=50,anchor=tk.CENTER)
        self.treeview_pecas.grid(row=0,column=0,columnspan=2,**pad_options,sticky="nsew")
        pecas_frame.columnconfigure(0,weight=1); pecas_frame.rowconfigure(0,weight=1)
        scrollbar = ttk.Scrollbar(pecas_frame,orient="vertical",command=self.treeview_pecas.yview)
        self.treeview_pecas.configure(yscrollcommand=scrollbar.set); scrollbar.grid(row=0,column=1,sticky="ns",rowspan=4)

        btn_manage_frame = tk.Frame(pecas_frame)
        btn_manage_frame.grid(row=1,column=0,sticky="ew",**pad_options)
        self.add_peca_btn = tk.Button(btn_manage_frame,text="Adicionar",command=self.adicionar_peca_dialog); self.add_peca_btn.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=2)
        self.edit_peca_btn = tk.Button(btn_manage_frame,text="Editar",command=self.editar_peca_dialog); self.edit_peca_btn.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=2)
        self.duplicate_peca_btn = tk.Button(btn_manage_frame,text="Duplicar",command=self.duplicar_peca_selecionada); self.duplicate_peca_btn.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=2)

        btn_remove_frame = tk.Frame(pecas_frame)
        btn_remove_frame.grid(row=2,column=0,sticky="ew",**pad_options)
        self.remove_peca_btn = tk.Button(btn_remove_frame,text="Remover",command=self.remover_peca_selecionada); self.remove_peca_btn.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=2)
        self.undo_remove_btn = tk.Button(btn_remove_frame,text="Desfazer Remoção",command=self.desfazer_remocao,state=tk.DISABLED); self.undo_remove_btn.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=2)
        
        btn_order_frame = tk.Frame(pecas_frame)
        btn_order_frame.grid(row=3,column=0,sticky="ew",**pad_options)
        self.move_up_btn = tk.Button(btn_order_frame,text="Mover Acima ↑",command=lambda:self.mover_peca_selecionada("cima")); self.move_up_btn.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=2)
        self.move_down_btn = tk.Button(btn_order_frame,text="Mover Abaixo ↓",command=lambda:self.mover_peca_selecionada("baixo")); self.move_down_btn.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=2)
        
        acoes_frame = tk.Frame(master)
        acoes_frame.grid(row=2,column=0,columnspan=2,pady=(10,5),padx=5,sticky="ew")
        self.executar_corte_btn = tk.Button(acoes_frame,text="Executar Otimização de Corte",command=self.processar_cortes,bg="lightblue",font=('Arial',10,'bold')); self.executar_corte_btn.pack(side=tk.LEFT,expand=True,fill=tk.X,padx=2)

        self.pecas_a_cortar = []
        self.resultado_cortes = None 
        self.proximo_id_original = 0
        self.ultima_peca_removida_info = None

    def _get_selected_treeview_index(self):
        selected_item_id = self.treeview_pecas.focus()
        if selected_item_id:
            try:
                return self.treeview_pecas.index(selected_item_id)
            except tk.TclError: # Pode acontecer se o item não for encontrado (raro com focus)
                return None
        return None

    def _validar_dimensoes_chapa(self):
        try:
            largura = int(self.largura_chapa_entry.get())
            altura = int(self.altura_chapa_entry.get())
            if largura <= 0 or altura <= 0:
                messagebox.showerror("Erro", "Dimensões da chapa devem ser números inteiros positivos.")
                return None, None
            return largura, altura
        except ValueError:
            messagebox.showerror("Erro", "Dimensões da chapa devem ser números inteiros válidos.")
            return None, None

    def atualizar_treeview_pecas(self):
        for i in self.treeview_pecas.get_children(): self.treeview_pecas.delete(i)
        for i,p in enumerate(self.pecas_a_cortar):
            id_d = p.get('id_display',f"P{p['original_idx']+1}")
            self.treeview_pecas.insert("","end",text=str(i),values=(id_d,p['alt'],p['larg'],p['quant']))

    def adicionar_peca_dialog(self):
        d=PecaDialog(self.master,title="Adicionar Peça");
        if d.result:
            npi=d.result; npi['original_idx']=self.proximo_id_original
            if not npi.get('id'): npi['id']=f"P{self.proximo_id_original+1}"
            npi['id_display']=npi['id']; self.pecas_a_cortar.append(npi); self.proximo_id_original+=1
            self.atualizar_treeview_pecas(); self.undo_remove_btn.config(state=tk.DISABLED); self.ultima_peca_removida_info=None

    def editar_peca_dialog(self):
        idx=self._get_selected_treeview_index();
        if idx is None: messagebox.showwarning("Aviso","Selecione uma peça para editar."); return
        d=PecaDialog(self.master,title="Editar Peça",initial_data=self.pecas_a_cortar[idx])
        if d.result:
            self.pecas_a_cortar[idx]=d.result; self.pecas_a_cortar[idx]['id_display']=self.pecas_a_cortar[idx]['id']
            self.atualizar_treeview_pecas(); self.undo_remove_btn.config(state=tk.DISABLED); self.ultima_peca_removida_info=None

    def duplicar_peca_selecionada(self):
        idx=self._get_selected_treeview_index();
        if idx is None: messagebox.showwarning("Aviso","Selecione uma peça para duplicar."); return
        orig=self.pecas_a_cortar[idx]; dup=orig.copy(); dup['original_idx']=self.proximo_id_original
        dup['id']=f"{orig.get('id','P')} (Cópia)"; dup['id_display']=dup['id']
        self.pecas_a_cortar.append(dup); self.proximo_id_original+=1; self.atualizar_treeview_pecas()
        if self.treeview_pecas.get_children():
            last_iid=self.treeview_pecas.get_children()[-1]
            self.treeview_pecas.selection_set(last_iid);self.treeview_pecas.focus(last_iid);self.treeview_pecas.see(last_iid)
        self.undo_remove_btn.config(state=tk.DISABLED); self.ultima_peca_removida_info=None

    def remover_peca_selecionada(self):
        idx=self._get_selected_treeview_index();
        if idx is None: messagebox.showwarning("Aviso","Selecione uma peça para remover."); return
        pd_data=self.pecas_a_cortar[idx]; msg=f"ID: {pd_data.get('id_display','N/A')}\n{pd_data['alt']}A x {pd_data['larg']}L (Qtd: {pd_data['quant']})"
        if messagebox.askyesno("Confirmar",f"Remover:\n{msg}?"):
            rem=self.pecas_a_cortar.pop(idx); self.ultima_peca_removida_info=(idx,rem)
            self.atualizar_treeview_pecas(); self.undo_remove_btn.config(state=tk.NORMAL)
            if self.pecas_a_cortar: # Tenta selecionar o próximo ou anterior
                new_idx_to_select=min(idx,len(self.pecas_a_cortar)-1)
                if new_idx_to_select>=0 and self.treeview_pecas.get_children():
                    iid_to_select=self.treeview_pecas.get_children()[new_idx_to_select]
                    self.treeview_pecas.selection_set(iid_to_select); self.treeview_pecas.focus(iid_to_select)
        else: self.ultima_peca_removida_info=None

    def desfazer_remocao(self):
        if self.ultima_peca_removida_info:
            idx,p=self.ultima_peca_removida_info; self.pecas_a_cortar.insert(idx,p); self.atualizar_treeview_pecas()
            if idx < len(self.treeview_pecas.get_children()):
                iid_to_select=self.treeview_pecas.get_children()[idx]
                self.treeview_pecas.selection_set(iid_to_select);self.treeview_pecas.focus(iid_to_select);self.treeview_pecas.see(iid_to_select)
            self.ultima_peca_removida_info=None; self.undo_remove_btn.config(state=tk.DISABLED)
        else: messagebox.showinfo("Info","Nada para desfazer.")

    def mover_peca_selecionada(self,direcao):
        idx_a=self._get_selected_treeview_index();
        if idx_a is None: messagebox.showwarning("Aviso","Selecione uma peça para mover."); return
        n_pecas=len(self.pecas_a_cortar); idx_n=-1
        if direcao=="cima" and idx_a>0: 
            idx_n=idx_a-1
            self.pecas_a_cortar[idx_a],self.pecas_a_cortar[idx_n] = self.pecas_a_cortar[idx_n],self.pecas_a_cortar[idx_a]
        elif direcao=="baixo" and idx_a<n_pecas-1: 
            idx_n=idx_a+1
            self.pecas_a_cortar[idx_a],self.pecas_a_cortar[idx_n] = self.pecas_a_cortar[idx_n],self.pecas_a_cortar[idx_a]
        else: return # Movimento inválido ou no limite
        
        if idx_n!=-1: # Se o movimento ocorreu
            self.atualizar_treeview_pecas()
            if self.treeview_pecas.get_children() and 0<=idx_n<len(self.treeview_pecas.get_children()):
                iid_to_select=self.treeview_pecas.get_children()[idx_n]
                self.treeview_pecas.selection_set(iid_to_select);self.treeview_pecas.focus(iid_to_select);self.treeview_pecas.see(iid_to_select)
            self.undo_remove_btn.config(state=tk.DISABLED); self.ultima_peca_removida_info=None
    
    def processar_cortes(self):
        largura_chapa, altura_chapa = self._validar_dimensoes_chapa()
        if largura_chapa is None: return
        if not self.pecas_a_cortar: messagebox.showwarning("Aviso", "Adicione peças para o corte."); return
        pecas_exp = []
        for p_info in self.pecas_a_cortar:
            for _ in range(p_info['quant']):
                pecas_exp.append({'id': p_info['id'], 'larg': p_info['larg'], 'alt': p_info['alt'], 'original_idx': p_info['original_idx'] })
        self.resultado_cortes, nao_alocadas = cortar_chapas(largura_chapa, altura_chapa, pecas_exp)
        if self.resultado_cortes:
            plotar_chapas_todas(self.resultado_cortes, largura_chapa, altura_chapa)
            if nao_alocadas:
                msg = "Peças não alocadas:\n"; mapa = {}
                for p_na in nao_alocadas:
                    desc = next((item for item in self.pecas_a_cortar if item["original_idx"] == p_na['original_idx']), None)
                    if desc: nome = f"{desc.get('id_display','P')} ({desc['larg']}x{desc['alt']})"; mapa[nome] = mapa.get(nome,0)+1
                for nome, qtd in mapa.items(): msg += f"- {nome}: {qtd} un.\n"
                messagebox.showwarning("Aviso", msg)
            else: messagebox.showinfo("Sucesso", "Todas as peças foram alocadas!")
        else:
            messagebox.showerror("Erro", "Não foi possível alocar nenhuma peça.")
        self.undo_remove_btn.config(state=tk.DISABLED); self.ultima_peca_removida_info = None
    
    def importar_lista_pecas_excel(self):
        if self.pecas_a_cortar and not messagebox.askyesno("Confirmar Importação", "Isso substituirá a lista de peças atual. Deseja continuar?"): return
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo Excel com lista de peças",
            filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*")], defaultextension=".xlsx")
        if not filepath: return
        try:
            df = pd.read_excel(filepath); col_map = {'id': None, 'largura': None, 'altura': None, 'quantidade': None}
            std_id_col = 'ID/Nome da Peça'; std_alt_col = 'Altura (cm)'; std_larg_col = 'Largura (cm)'; std_quant_col = 'Quantidade'
            possible_id_cols = [std_id_col.lower(), 'id', 'nome', 'id peça', 'id_peca', 'id/nome']
            possible_larg_cols = [std_larg_col.lower(), 'largura', 'larg']
            possible_alt_cols = [std_alt_col.lower(), 'altura', 'alt']
            possible_quant_cols = [std_quant_col.lower(), 'qtd.', 'qtd', 'quant']
            for col in df.columns:
                col_lower = str(col).lower()
                if not col_map['id'] and col_lower in possible_id_cols: col_map['id'] = col
                elif not col_map['largura'] and col_lower in possible_larg_cols: col_map['largura'] = col
                elif not col_map['altura'] and col_lower in possible_alt_cols: col_map['altura'] = col
                elif not col_map['quantidade'] and col_lower in possible_quant_cols: col_map['quantidade'] = col
            if not all(col_map.values()):
                missing = [k for k, v in col_map.items() if v is None];
                messagebox.showerror("Erro de Importação", f"Não foi possível encontrar as colunas: {', '.join(missing)}.\nVerifique se o Excel contém colunas como '{std_id_col}', '{std_alt_col}', '{std_larg_col}', '{std_quant_col}'."); return
            novas_pecas = []; temp_proximo_id_original = 0 
            for index, row in df.iterrows():
                try:
                    peca_id = str(row[col_map['id']]); largura = int(row[col_map['largura']])
                    altura = int(row[col_map['altura']]); quantidade = int(row[col_map['quantidade']])
                    if largura <= 0 or altura <= 0 or quantidade <= 0: raise ValueError(f"Dados inválidos na linha {index+2}: Dimensões/quantidade devem ser positivas.")
                    novas_pecas.append({'id': peca_id, 'larg': largura, 'alt': altura, 'quant': quantidade, 'original_idx': temp_proximo_id_original, 'id_display': peca_id })
                    temp_proximo_id_original += 1
                except ValueError as ve: messagebox.showwarning("Aviso de Importação", f"Ignorando linha {index+2} do Excel: {ve}"); continue
                except KeyError as ke: messagebox.showwarning("Aviso de Importação", f"Ignorando linha {index+2} do Excel: coluna {ke} não encontrada."); continue
            if novas_pecas:
                self.pecas_a_cortar = novas_pecas; self.proximo_id_original = temp_proximo_id_original 
                self.atualizar_treeview_pecas(); self.undo_remove_btn.config(state=tk.DISABLED)
                self.ultima_peca_removida_info = None; self.resultado_cortes = None 
                messagebox.showinfo("Importação Concluída", f"{len(novas_pecas)} grupo(s) de peças importado(s) com sucesso!")
            else: messagebox.showwarning("Importação", "Nenhuma peça válida encontrada no arquivo Excel para importar.")
        except Exception as e: messagebox.showerror("Erro de Importação", f"Ocorreu um erro ao importar o arquivo Excel:\n{e}")

    def exportar_lista_pecas_para_excel(self):
        if not self.pecas_a_cortar: messagebox.showwarning("Exportar Lista", "Não há peças na lista para exportar."); return
        col_id = 'ID/Nome da Peça'; col_alt = 'Altura (cm)'; col_larg = 'Largura (cm)'; col_quant = 'Quantidade'
        dados_para_exportar = []
        for peca in self.pecas_a_cortar:
            dados_para_exportar.append({
                col_id: peca.get('id_display', peca.get('id', '')),
                col_alt: peca['alt'], col_larg: peca['larg'], col_quant: peca['quant'] })
        df = pd.DataFrame(dados_para_exportar, columns=[col_id, col_alt, col_larg, col_quant])
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx", filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
                title="Exportar Lista de Peças como...", initialdir=os.getcwd() )
            if filepath: df.to_excel(filepath, index=False); messagebox.showinfo("Sucesso", f"Lista de peças exportada para:\n{filepath}")
        except Exception as e: messagebox.showerror("Erro ao Exportar", f"Não foi possível exportar a lista de peças.\nErro: {e}")

class PecaDialog(simpledialog.Dialog): 
    def __init__(self,parent,title=None,initial_data=None):
        self.initial_data=initial_data if initial_data else {}
        # print(f"DEBUG: PecaDialog.__init__ - parent: {parent}, title: {title}") # Linha de depuração 1
        
        # Chama o __init__ da classe pai (simpledialog.Dialog)
        # É aqui que self.top (a janela Toplevel) deveria ser criada.
        super().__init__(parent,title) 
        
        # print(f"DEBUG: PecaDialog.__init__ - super().__init__ completed.") # Linha de depuração 2
        # print(f"DEBUG: PecaDialog.__init__ - hasattr(self, 'top'): {hasattr(self, 'top')}") # Linha de depuração 3
        
        if hasattr(self, 'top') and self.top is not None:
            # print(f"DEBUG: PecaDialog.__init__ - self.top exists: {self.top}. Setting resizable.") # Linha de depuração 4
            try:
                self.top.resizable(width=False, height=False)
            except tk.TclError as e:
                print(f"DEBUG: PecaDialog.__init__ - Could not set resizable on self.top: {e}")
        # else:
            # print("DEBUG: PecaDialog.__init__ - self.top was NOT found or is None after super().__init__.") # Linha de depuração 5

    def body(self,master_frame): # O argumento é o frame onde o corpo do diálogo é construído
        tk.Label(master_frame,text="ID/Nome:").grid(row=0,column=0,sticky="w"); self.id_entry=tk.Entry(master_frame,width=20); self.id_entry.grid(row=0,column=1)
        if self.initial_data.get('id'):self.id_entry.insert(0,self.initial_data['id'])
        
        tk.Label(master_frame,text="Largura (cm):").grid(row=1,column=0,sticky="w"); self.larg_entry=tk.Entry(master_frame,width=10); self.larg_entry.grid(row=1,column=1)
        if self.initial_data.get('larg'):self.larg_entry.insert(0,self.initial_data['larg'])
        
        tk.Label(master_frame,text="Altura (cm):").grid(row=2,column=0,sticky="w"); self.alt_entry=tk.Entry(master_frame,width=10); self.alt_entry.grid(row=2,column=1)
        if self.initial_data.get('alt'):self.alt_entry.insert(0,self.initial_data['alt'])
        
        tk.Label(master_frame,text="Quantidade:").grid(row=3,column=0,sticky="w"); self.quant_entry=tk.Entry(master_frame,width=10); self.quant_entry.grid(row=3,column=1)
        self.quant_entry.insert(0,self.initial_data.get('quant',"1"))
        
        return self.id_entry # Retorna o widget que deve receber o foco inicial
    
    def apply(self):
        try:
            id_p=self.id_entry.get().strip(); l=int(self.larg_entry.get()); a=int(self.alt_entry.get()); q=int(self.quant_entry.get())
            if l<=0 or a<=0 or q<=0: messagebox.showerror("Erro","Dimensões/qtd devem ser >0.",parent=self); self.result=None; return
            self.result={'id':id_p,'larg':l,'alt':a,'quant':q}
            if self.initial_data and 'original_idx' in self.initial_data: self.result['original_idx']=self.initial_data['original_idx']
        except ValueError: messagebox.showerror("Erro","Dimensões/qtd devem ser inteiros.",parent=self); self.result=None

if __name__ == "__main__":
    try:
        root = tk.Tk()
        # master.resizable(width=False, height=False) deve ser root.resizable(...)
        root.resizable(width=False, height=False) # Correção: Aplicar na instância root
        app = CorteGUI(root)
        root.mainloop()
    except Exception as e:
        import traceback
        error_message = f"Ocorreu um erro fatal ao iniciar o programa:\n\n{traceback.format_exc()}"
        print(error_message) 
        try:
            error_root = tk.Tk()
            error_root.withdraw() 
            messagebox.showerror("Erro Fatal na Inicialização", error_message)
            error_root.destroy()
        except:
            pass
