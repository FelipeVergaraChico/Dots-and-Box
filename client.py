import socket
import threading
import pickle
import tkinter as tk
from tkinter import messagebox

HOST = '127.0.0.1'
PORT = 65432


class DotsAndBoxesClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Dots and Boxes")

        # Configuração da conexão com o servidor
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((HOST, PORT))

        self.game_state = None
        self.player_id = None

        # Configuração do Canvas e o tamanho da grade
        self.canvas_size = 400
        self.grid_size = 4
        self.cell_size = self.canvas_size // (self.grid_size + 1)
        self.canvas = tk.Canvas(master, width=self.canvas_size, height=self.canvas_size)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.make_move)

        threading.Thread(target=self.receive_updates).start()

    def draw_board(self):
        self.canvas.delete("all")
        for x in range(self.grid_size + 1):
            for y in range(self.grid_size + 1):
                self.canvas.create_oval(
                    x * self.cell_size + 10, y * self.cell_size + 10,
                    x * self.cell_size + 20, y * self.cell_size + 20, fill="black"
                )

        if self.game_state:
            # Desenha as linhas horizontais
            for i, row in enumerate(self.game_state["horizontal_lines"]):
                for j, line in enumerate(row):
                    if line:
                        self.canvas.create_line(
                            j * self.cell_size + 15, i * self.cell_size + 15,
                            (j + 1) * self.cell_size + 5, i * self.cell_size + 15, fill="blue", width=2
                        )

            # Desenha as linhas verticais
            for i, row in enumerate(self.game_state["vertical_lines"]):
                for j, line in enumerate(row):
                    if line:
                        self.canvas.create_line(
                            i * self.cell_size + 15, j * self.cell_size + 15,
                            i * self.cell_size + 15, (j + 1) * self.cell_size + 5, fill="red", width=2
                        )

            # Desenha as caixas
            for i, row in enumerate(self.game_state["boxes"]):
                for j, owner in enumerate(row):
                    if owner:
                        color = "blue" if owner == "player1" else "red"
                        self.canvas.create_text(
                            j * self.cell_size + 50, i * self.cell_size + 50,
                            text="X", fill=color, font=("Arial", 24)
                        )

    def make_move(self, event):
        x, y = event.x, event.y
        line = self.get_nearest_line(x, y)

        if line:
            orientation, i, j = line
            if self.game_state["turn"] == self.player_id:
                move = {"x": i, "y": j, "orientation": orientation}
                self.client_socket.send(pickle.dumps(move))
            else:
                messagebox.showinfo("Aguarde", "Não é seu turno!")

    def get_nearest_line(self, x, y):
        tolerance = self.cell_size // 4
        selected_line = None

        # Verifica linhas horizontais
        for i in range(self.grid_size + 1):
            for j in range(self.grid_size):
                x1, y1 = j * self.cell_size + 15, i * self.cell_size + 15
                x2, y2 = (j + 1) * self.cell_size + 5, i * self.cell_size + 15
                if abs(y - y1) < tolerance and x1 <= x <= x2:
                    selected_line = ("horizontal", j, i)  # x = coluna, y = linha

        # Verifica linhas verticais
        for i in range(self.grid_size):
            for j in range(self.grid_size + 1):
                x1, y1 = i * self.cell_size + 15, j * self.cell_size + 15
                x2, y2 = i * self.cell_size + 15, (j + 1) * self.cell_size + 5
                if abs(x - x1) < tolerance and y1 <= y <= y2:
                    selected_line = ("vertical", i, j)  # x = coluna, y = linha

        return selected_line

    def receive_updates(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                update = pickle.loads(data)

                if "error" in update:
                    messagebox.showerror("Erro", update["error"])
                else:
                    self.game_state = update

                    self.player_id = self.game_state["turn"]
                    self.draw_board()
            except:
                break
        self.client_socket.close()


root = tk.Tk()
client = DotsAndBoxesClient(root)
root.mainloop()
