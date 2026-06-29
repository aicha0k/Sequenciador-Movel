import json
import socketserver
import threading
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    sender: str
    content: str
    msg_id: str
    sequence_number: Optional[int] = None
    sequencer_id: Optional[str] = None

    def describe(self):
        return (
            f"{self.msg_id} | seq={self.sequence_number} | "
            f"emissor={self.sender} | sequenciador={self.sequencer_id} | "
            f"conteúdo='{self.content}'"
        )


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
        return [
            message.msg_id
            for message in self.buffer
            if message.msg_id not in delivered_ids
        ]


class Receiver:
    def __init__(self, receiver_id, sequencer_ring_order):
        self.receiver_id = receiver_id
        self.sequencer_ring_order = sequencer_ring_order
        self.delivered_messages = []

    def deliver(self, message):
        self.delivered_messages.append(message)


class MobileSequencerSystem:
    def __init__(self):
        # Grupo emissor: representado logicamente.
        # Quem interage com ele é o client.py.
        self.sender_counters = {
            "E1": 0,
            "E2": 0,
            "E3": 0,
        }

        # Grupo sequenciador, pequeno, como nos slides.
        self.sequencers = [
            Sequencer("S1"),
            Sequencer("S2"),
            Sequencer("S3"),
        ]

        # Anel lógico dos sequenciadores.
        self.token_position = 0

        # Grupo receptor.
        sequencer_ring_order = [sequencer.sequencer_id for sequencer in self.sequencers]
        self.receivers = [
            Receiver("R1", sequencer_ring_order),
            Receiver("R2", sequencer_ring_order),
            Receiver("R3", sequencer_ring_order),
        ]

        # Controle da ordenação total.
        self.global_sequence_number = 0
        self.delivered_ids = set()

        # Lock para evitar problemas se mais de um cliente acessar ao mesmo tempo.
        self.lock = threading.Lock()

    def current_sequencer(self):
        return self.sequencers[self.token_position]

    def pass_token(self):
        old = self.current_sequencer().sequencer_id
        self.token_position = (self.token_position + 1) % len(self.sequencers)
        new = self.current_sequencer().sequencer_id

        return old, new

    def send_message_to_sequencer_group(self, sender_id, content):
        """
        Simula:
        Grupo Emissor -> Grupo Sequenciador

        O emissor difunde a mensagem para todos os processos
        do grupo sequenciador.
        """
        logs = []

        with self.lock:
            if sender_id not in self.sender_counters:
                return [f"Erro: emissor inválido: {sender_id}"]

            self.sender_counters[sender_id] += 1
            msg_id = f"{sender_id}.{self.sender_counters[sender_id]}"

            message = Message(
                sender=sender_id,
                content=content,
                msg_id=msg_id
            )

            logs.append(f"{sender_id} criou a mensagem {msg_id}: '{content}'")
            logs.append(f"{sender_id} difundiu {msg_id} para o grupo sequenciador.")

            for sequencer in self.sequencers:
                sequencer.receive_message(message)
                logs.append(f"  {sequencer.sequencer_id} recebeu {msg_id} no buffer.")

        return logs

    def process_current_token(self):
        """
        Simula:
        Grupo Sequenciador -> Grupo Receptor

        Apenas o sequenciador que possui o token pode repassar
        uma mensagem ao grupo receptor.
        """
        logs = []

        with self.lock:
            sequencer = self.current_sequencer()
            logs.append(f"Token atual: {sequencer.sequencer_id}")

            message = sequencer.get_next_undelivered_message(self.delivered_ids)

            if message is None:
                logs.append(f"{sequencer.sequencer_id} não possui mensagens novas para repassar.")
                old, new = self.pass_token()
                logs.append(f"Token passou de {old} para {new}.")
                return logs

            self.global_sequence_number += 1

            ordered_message = Message(
                sender=message.sender,
                content=message.content,
                msg_id=message.msg_id,
                sequence_number=self.global_sequence_number,
                sequencer_id=sequencer.sequencer_id
            )

            logs.append(
                f"{sequencer.sequencer_id} possui o bastão/token e repassa "
                f"{ordered_message.msg_id} ao grupo receptor com seq={ordered_message.sequence_number}."
            )

            logs.append("Difundindo mensagem ordenada para o grupo receptor:")

            for receiver in self.receivers:
                receiver.deliver(ordered_message)
                logs.append(f"  {receiver.receiver_id} entregou: {ordered_message.describe()}")

            self.delivered_ids.add(ordered_message.msg_id)

            old, new = self.pass_token()
            logs.append(f"Token passou de {old} para {new}.")

        return logs

    def process_n_rounds(self, n):
        logs = []

        for i in range(n):
            logs.append(f"\n--- Rodada {i + 1} ---")
            logs.extend(self.process_current_token())

        return logs

    def status(self):
        logs = []

        with self.lock:
            logs.append("=== ESTADO DO SISTEMA ===")

            logs.append("\nGrupo emissor:")
            for sender_id in self.sender_counters:
                logs.append(f"  {sender_id}")

            logs.append("\nGrupo sequenciador em anel lógico:")
            ring = " -> ".join(sequencer.sequencer_id for sequencer in self.sequencers)
            ring += f" -> {self.sequencers[0].sequencer_id}"
            logs.append(f"  {ring}")

            logs.append(f"\nSequenciador com token: {self.current_sequencer().sequencer_id}")

            logs.append("\nBuffers dos sequenciadores:")
            for sequencer in self.sequencers:
                pending = sequencer.pending_messages(self.delivered_ids)

                if pending:
                    logs.append(f"  {sequencer.sequencer_id}: {pending}")
                else:
                    logs.append(f"  {sequencer.sequencer_id}: vazio")

            logs.append("\nMensagens já entregues ao grupo receptor:")
            if self.delivered_ids:
                logs.append(f"  {sorted(self.delivered_ids)}")
            else:
                logs.append("  Nenhuma mensagem entregue ainda.")

        return logs

    def receiver_logs(self):
        logs = []

        with self.lock:
            logs.append("=== LOG DOS RECEPTORES ===")

            for receiver in self.receivers:
                logs.append(f"\n{receiver.receiver_id} entregou as mensagens nesta ordem:")

                if not receiver.delivered_messages:
                    logs.append("  Nenhuma mensagem entregue ainda.")
                else:
                    for message in receiver.delivered_messages:
                        logs.append(f"  {message.describe()}")

        return logs

    def validate_total_order(self):
        logs = []

        with self.lock:
            logs.append("=== VERIFICAÇÃO DE ORDEM TOTAL ===")

            if not self.receivers:
                logs.append("Não há receptores.")
                return logs

            reference_order = [
                message.msg_id
                for message in self.receivers[0].delivered_messages
            ]

            all_same_order = True

            for receiver in self.receivers:
                current_order = [
                    message.msg_id
                    for message in receiver.delivered_messages
                ]

                logs.append(f"{receiver.receiver_id}: {current_order}")

                if current_order != reference_order:
                    all_same_order = False

            if all_same_order:
                logs.append("\nResultado: todos os receptores entregaram as mensagens na mesma ordem.")
            else:
                logs.append("\nResultado: houve divergência na ordem de entrega.")

        return logs


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
                response = {
                    "ok": False,
                    "output": f"Erro ao processar requisição: {error}"
                }

            self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))

        print(f"Cliente desconectado: {client_address}")

    def process_request(self, request):
        command = request.get("command")

        if command == "SEND":
            sender_id = request.get("sender_id")
            content = request.get("content")

            if not sender_id or not content:
                return {
                    "ok": False,
                    "output": "Erro: SEND precisa de sender_id e content."
                }

            logs = system.send_message_to_sequencer_group(sender_id, content)
            return {
                "ok": True,
                "output": "\n".join(logs)
            }

        if command == "PROCESS_ONE":
            logs = system.process_current_token()
            return {
                "ok": True,
                "output": "\n".join(logs)
            }

        if command == "PROCESS_N":
            n = int(request.get("n", 1))
            logs = system.process_n_rounds(n)
            return {
                "ok": True,
                "output": "\n".join(logs)
            }

        if command == "STATUS":
            logs = system.status()
            return {
                "ok": True,
                "output": "\n".join(logs)
            }

        if command == "RECEIVER_LOGS":
            logs = system.receiver_logs()
            return {
                "ok": True,
                "output": "\n".join(logs)
            }

        if command == "VALIDATE_TOTAL_ORDER":
            logs = system.validate_total_order()
            return {
                "ok": True,
                "output": "\n".join(logs)
            }

        return {
            "ok": False,
            "output": f"Comando desconhecido: {command}"
        }


def main():
    host = "127.0.0.1"
    port = 5000

    print("Servidor do Sequenciador Móvel iniciado.")
    print(f"Endereço: {host}:{port}")
    print("Aguardando clientes...")

    with socketserver.ThreadingTCPServer((host, port), RequestHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()