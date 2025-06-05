import tkinter as tk
from tkinter import simpledialog, messagebox

class PecaDialog(simpledialog.Dialog):
    """
    Diálogo para adicionar ou editar uma peça.
    """
    def __init__(self, parent, title=None, initial_data=None):
        self.initial_data = initial_data
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        # Campos de entrada
        tk.Label(master, text="ID/Nome:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.id_entry = tk.Entry(master, width=20)
        self.id_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        tk.Label(master, text="Largura (cm):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.larg_entry = tk.Entry(master, width=20, validate="key", 
                                 validatecommand=(master.register(self._validar_decimal), '%P'))
        self.larg_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        tk.Label(master, text="Altura (cm):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.alt_entry = tk.Entry(master, width=20, validate="key",
                                validatecommand=(master.register(self._validar_decimal), '%P'))
        self.alt_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        tk.Label(master, text="Quantidade:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.quant_entry = tk.Entry(master, width=20, validate="key",
                                  validatecommand=(master.register(self._validar_numero), '%P'))
        self.quant_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        # Preencher com dados iniciais se for edição
        if self.initial_data:
            self.id_entry.insert(0, self.initial_data.get('id', ''))
            self.larg_entry.insert(0, str(self.initial_data.get('larg', '')))
            self.alt_entry.insert(0, str(self.initial_data.get('alt', '')))
            self.quant_entry.insert(0, str(self.initial_data.get('quant', '')))
        else:
            self.quant_entry.insert(0, "1")
            
        return self.id_entry

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

    def _validar_numero(self, valor):
        """Valida se o valor é um número inteiro válido."""
        if valor == "":
            return True
        try:
            int(valor)
            return True
        except ValueError:
            return False

    def apply(self):
        try:
            id_p = self.id_entry.get().strip()
            l = float(self.larg_entry.get())
            a = float(self.alt_entry.get())
            q = int(self.quant_entry.get())
            
            if l <= 0 or a <= 0 or q <= 0:
                messagebox.showerror("Erro", "Dimensões e quantidade devem ser maiores que zero.", parent=self)
                self.result = None
                return
                
            self.result = {
                'id': id_p,
                'larg': l,
                'alt': a,
                'quant': q
            }
            
            if self.initial_data and 'original_idx' in self.initial_data:
                self.result['original_idx'] = self.initial_data['original_idx']
                
        except ValueError:
            messagebox.showerror("Erro", "Dimensões e quantidade devem ser números válidos.", parent=self)
            self.result = None 