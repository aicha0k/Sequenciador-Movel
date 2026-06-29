import json
import socket
import tkinter as tk
from tkinter import ttk, messagebox

HOST = "127.0.0.1"
PORT = 5000

def send_request(request):
    try:
        with socket.create_connection((HOST, PORT)) as sock:
            message = json.dumps(request) + "\n"
            sock.sendall(message.encode("utf-8"))
            
            response_line = b""
            while not response_line.endswith(b"\n"):
                chunk = sock.recv(4096)
                if not chunk: break
                response_line += chunk
                
            return json.loads(response_line.decode("utf-8"))
    except Exception as e:
        return {"ok": False, "output": f"Erro: {e}"}

class DashboardSequenciador:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador - Sequenciador Móvel")
        self.root.geometry("750x650")
        self.root.configure(bg="#f0f0f0")

        # --- PAINEL SUPERIOR: CONTROLES ---
        frame_controles = tk.Frame(root, bg="#f0f0f0", pady=10)
        frame_controles.pack(fill="x", padx=20)

        tk.Label(frame_controles, text="Emissor:", bg="#f0f0f0").pack(side="left")
        self.emissor_var = tk.StringVar(value="E1")
        ttk.Combobox(frame_controles, textvariable=self.emissor_var, values=["E1", "E2", "E3"], width=5).pack(side="left", padx=5)

        tk.Label(frame_controles, text="Mensagem:", bg="#f0f0f0").pack(side="left")
        self.msg_entry = tk.Entry(frame_controles, width=25)
        self.msg_entry.pack(side="left", padx=5)

        tk.Button(frame_controles, text="📨 Enviar", bg="#4CAF50", fg="white", command=self.enviar).pack(side="left", padx=10)
        tk.Button(frame_controles, text="🔄 Processar 1 Passo (Token)", bg="#2196F3", fg="white", command=self.processar_token).pack(side="right")

        # --- PAINEL DO MEIO: SEQUENCIADORES (O ANEL) ---
        tk.Label(root, text="Grupo Sequenciador (Anel Lógico)", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=(10, 0))
        self.frame_anel = tk.Frame(root, bg="#f0f0f0")
        self.frame_anel.pack(fill="x", padx=20, pady=5)

        self.seq_frames = {}
        self.seq_lists = {}
        
        for s in ["S1", "S2", "S3"]:
            # Frame individual para cada Sequenciador
            f = tk.Frame(self.frame_anel, borderwidth=2, relief="groove", width=200, height=150)
            f.pack(side="left", expand=True, fill="both", padx=10)
            f.pack_propagate(False)
            
            lbl = tk.Label(f, text=s, font=("Arial", 14, "bold"))
            lbl.pack(pady=5)
            
            listbox = tk.Listbox(f, height=5, bg="#ffffff")
            listbox.pack(padx=10, pady=5, fill="both", expand=True)
            
            self.seq_frames[s] = {"frame": f, "label": lbl}
            self.seq_lists[s] = listbox

        # --- PAINEL INFERIOR: RECEPTORES ---
        tk.Label(root, text="Grupo Receptor (Mensagens Entregues)", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=(20, 0))
        self.frame_receptores = tk.Frame(root, bg="#f0f0f0")
        self.frame_receptores.pack(fill="x", padx=20, pady=5)

        self.rec_lists = {}
        for r in ["R1", "R2", "R3"]:
            f = tk.Frame(self.frame_receptores, borderwidth=1, relief="solid", width=200, height=150)
            f.pack(side="left", expand=True, fill="both", padx=10)
            f.pack_propagate(False)
            
            tk.Label(f, text=r, font=("Arial", 12), bg="#e0e0e0").pack(fill="x")
            
            listbox = tk.Listbox(f, height=6)
            listbox.pack(padx=5, pady=5, fill="both", expand=True)
            self.rec_lists[r] = listbox

        # Atualiza a interface logo ao abrir
        self.atualizar_tela()

    def enviar(self):
        txt = self.msg_entry.get().strip()
        if not txt: return
        send_request({"command": "SEND", "sender_id": self.emissor_var.get(), "content": txt})
        self.msg_entry.delete(0, tk.END)
        self.atualizar_tela()

    def processar_token(self):
        send_request({"command": "PROCESS_ONE"})
        self.atualizar_tela()

    def atualizar_tela(self):
        res = send_request({"command": "GET_GUI_STATE"})
        if not res.get("ok"): return
        
        estado = res["output"]
        
        # 1. Atualizar cores e Token nos Sequenciadores
        token_atual = estado["token"]
        for s, obj in self.seq_frames.items():
            if s == token_atual:
                obj["frame"].configure(bg="#fff59d") # Amarelo (com token)
                obj["label"].configure(text=f"🪙 {s} (TOKEN)", bg="#fff59d")
            else:
                obj["frame"].configure(bg="#e0e0e0") # Cinza (sem token)
                obj["label"].configure(text=s, bg="#e0e0e0")
                
            # Atualizar listas de mensagens pendentes
            self.seq_lists[s].delete(0, tk.END)
            for msg in estado["buffers"][s]:
                self.seq_lists[s].insert(tk.END, f"⏳ {msg}")
                
        # 2. Atualizar mensagens nos Receptores
        for r, listbox in self.rec_lists.items():
            listbox.delete(0, tk.END)
            for msg in estado["receivers"][r]:
                listbox.insert(tk.END, f"✅ {msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardSequenciador(root)
    root.mainloop()