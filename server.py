import json
import socketserver
import threading
from collections import deque
from dataclasses import dataclass


@dataclass
class Message:
    sender: str
    content: str
    msg_id: str
    sequence_number: int = None
    sequencer_id: str = None


class Sequencer:
    def __init__(self, sequencer_id):
        self.sequencer_id = sequencer_id
        self.buffer = deque()

    def receive_message(self, message):
        self.buffer.append(message)

    def get_next_undelivered_message(self, delivered_ids):
        while self.buffer:
            message = self.buffer.popleft()
            if message.msg_id not in delivered_ids:
                return message
        return None

    def pending_messages(self, delivered_ids):
        return [msg.msg_id for msg in self.buffer if msg.msg_id not in delivered_ids]


class Receiver:
    def __init__(self, receiver_id):
        self.receiver_id = receiver_id
        self.delivered_messages = []

    def deliver(self, message):
        self.delivered_messages.append(message)


class MobileSequencerSystem:
    def __init__(self):
        self.sender_counters = {"E1": 0, "E2": 0, "E3": 0}
        
        self.sequencers = [Sequencer("S1"), Sequencer("S2"), Sequencer("S3")]
        self.token_position = 0
        
        self.receivers = [Receiver("R1"), Receiver("R2"), Receiver("R3")]

        self.global_sequence_number = 0
        self.delivered_ids = set()
        self.lock = threading.Lock()

    def current_sequencer(self):
        return self.sequencers[self.token_position]

    def pass_token(self):
        self.token_position = (self.token_position + 1) % len(self.sequencers)

    def send_message_to_sequencer_group(self, sender_id, content):
        with self.lock:
            if sender_id not in self.sender_counters:
                return False
            
            self.sender_counters[sender_id] += 1
            msg_id = f"{sender_id}.{self.sender_counters[sender_id]}"
            
            message = Message(sender=sender_id, content=content, msg_id=msg_id)

            # Difusão da mensagem para todos os sequenciadores
            for sequencer in self.sequencers:
                sequencer.receive_message(message)
                
        return True

    def process_current_token(self):
        with self.lock:
            sequencer = self.current_sequencer()
            message = sequencer.get_next_undelivered_message(self.delivered_ids)

            # Se não há mensagens novas, apenas passa o token
            if message is None:
                self.pass_token()
                return

            # Se há mensagem, define a ordem e entrega aos receptores
            self.global_sequence_number += 1
            ordered_message = Message(
                sender=message.sender,
                content=message.content,
                msg_id=message.msg_id,
                sequence_number=self.global_sequence_number,
                sequencer_id=sequencer.sequencer_id
            )

            for receiver in self.receivers:
                receiver.deliver(ordered_message)

            self.delivered_ids.add(ordered_message.msg_id)
            self.pass_token()


# Instância global do sistema
system = MobileSequencerSystem()


class RequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        client_address = self.client_address[0]
        print(f"Cliente conectado: {client_address}")

        while True:
            line = self.rfile.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.decode("utf-8"))
                response = self.process_request(request)
            except Exception as error:
                response = {"ok": False, "output": f"Erro interno: {error}"}

            self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))

        print(f"Cliente desconectado: {client_address}")

    def process_request(self, request):
        command = request.get("command")

        if command == "SEND":
            system.send_message_to_sequencer_group(request.get("sender_id"), request.get("content"))
            return {"ok": True}

        if command == "PROCESS_ONE":
            system.process_current_token()
            return {"ok": True}

        if command == "GET_GUI_STATE":
            with system.lock:
                return {
                    "ok": True,
                    "output": {
                        "token": system.current_sequencer().sequencer_id,
                        "buffers": {
                            s.sequencer_id: s.pending_messages(system.delivered_ids) 
                            for s in system.sequencers
                        },
                        "receivers": {
                            r.receiver_id: [f"{m.msg_id}: {m.content}" for m in r.delivered_messages]
                            for r in system.receivers
                        }
                    }
                }

        return {"ok": False, "output": "Comando desconhecido."}


def main():
    host, port = "127.0.0.1", 5000
    print(f"Servidor iniciado em {host}:{port}")
    
    with socketserver.ThreadingTCPServer((host, port), RequestHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()