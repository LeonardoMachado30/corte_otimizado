import tkinter as tk
from tkinter import messagebox
import traceback

from gui.main_window import CorteGUI

def main():
    """
    Função principal que inicia a aplicação.
    """
    try:
        root = tk.Tk()
        root.resizable(width=False, height=False)
        app = CorteGUI(root)
        root.mainloop()
    except Exception as e:
        error_message = f"Ocorreu um erro fatal ao iniciar o programa:\n\n{traceback.format_exc()}"
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            messagebox.showerror("Erro Fatal na Inicialização", error_message)
            temp_root.destroy()
        except:
            print(error_message)

if __name__ == "__main__":
    main() 