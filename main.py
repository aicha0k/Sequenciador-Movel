from collections import deque
from dataclasses import dataclass
from typing import Optional
from time import sleep


@dataclass
class Message:
    sender: str
    content: str
    msg_id: str
    sequence_number: Optional[int] = None
    sequencer_id: Optional[str] = None

    def __str__(self):
        return (
            f"{self.msg_id} | seq={self.sequence_number} | "
            f"emissor={self.sender} | sequenciador={self.sequencer_id} | "
            f"conteúdo='{self.content}'"
        )


class Sender:
    def __init__(self, sender_id):
        self.sender_id = sender_id
        self.local_counter = 0

    def create_message(self, content):
        self.local_counter += 1
        msg_id = f"{self.sender_id}.{self.local_counter}"

        return Message(
            sender=self.sender_id,
            content=content,
            msg_id=msg_id
        )


class Sequencer:
    def __init__(self, sequencer_id):
        self.sequencer_id = sequencer_id
        self.buffer = deque()

    def receive_from_sender(self, message):
        self.buffer.append(message)
        print(f"  {self.sequencer_id} recebeu {message.msg_id} no buffer.")

    def get_next_undelivered_message(self, delivered_ids):
        """
        Retorna a próxima mensagem ainda não repassada ao grupo receptor.
        Mensagens já entregues são removidas do buffer para evitar duplicação.
        """
        while self.buffer:
            message = self.buffer.popleft()

            if message.msg_id not in delivered_ids:
                return message

        return None

    def show_buffer(self, delivered_ids):
        pending = [
            message.msg_id
            for message in self.buffer
            if message.msg_id not in delivered_ids
        ]

        return pending


class Receiver:
    def __init__(self, receiver_id, sequencer_ring_order):
        self.receiver_id = receiver_id
        self.sequencer_ring_order = sequencer_ring_order
        self.delivered_messages = []

    def deliver(self, message):
        self.delivered_messages.append(message)
        print(f"    {self.receiver_id} entregou: {message}")


class MobileSequencerSystem:
    def __init__(self):
        # Grupo emissor
        self.senders = {
            "E1": Sender("E1"),
            "E2": Sender("E2"),
            "E3": Sender("E3"),
        }

        # Grupo sequenciador: pequeno, como no material
        self.sequencers = [
            Sequencer("S1"),
            Sequencer("S2"),
            Sequencer("S3"),
        ]

        # Anel lógico dos sequenciadores
        self.token_position = 0

        # Grupo receptor
        sequencer_ring_order = [sequencer.sequencer_id for sequencer in self.sequencers]
        self.receivers = [
            Receiver("R1", sequencer_ring_order),
            Receiver("R2", sequencer_ring_order),
            Receiver("R3", sequencer_ring_order),
        ]

        # Controle da ordem global
        self.global_sequence_number = 0

        # Mensagens que já foram repassadas ao grupo receptor
        self.delivered_ids = set()

    def current_sequencer(self):
        return self.sequencers[self.token_position]

    def send_message(self, sender_id, content):
        """
        O emissor difunde a mensagem para todo o grupo sequenciador.
        """
        sender = self.senders[sender_id]
        message = sender.create_message(content)

        print("\n==================================================")
        print(f"{sender_id} criou a mensagem {message.msg_id}: '{content}'")
        print(f"{sender_id} difunde {message.msg_id} para o grupo sequenciador.")

        for sequencer in self.sequencers:
            sequencer.receive_from_sender(message)

        print("==================================================")

    def process_current_token(self):
        """
        Apenas o sequenciador que possui o token pode repassar uma mensagem
        ao grupo receptor.
        """
        sequencer = self.current_sequencer()

        print("\n==================================================")
        print(f"Token atual: {sequencer.sequencer_id}")

        message = sequencer.get_next_undelivered_message(self.delivered_ids)

        if message is None:
            print(f"{sequencer.sequencer_id} não possui mensagens novas para repassar.")
            self.pass_token()
            print("==================================================")
            return

        self.global_sequence_number += 1

        ordered_message = Message(
            sender=message.sender,
            content=message.content,
            msg_id=message.msg_id,
            sequence_number=self.global_sequence_number,
            sequencer_id=sequencer.sequencer_id
        )

        print(
            f"{sequencer.sequencer_id} possui o bastão/token e repassa "
            f"{ordered_message.msg_id} ao grupo receptor com seq={ordered_message.sequence_number}."
        )

        self.multicast_to_receiver_group(ordered_message)

        self.delivered_ids.add(ordered_message.msg_id)

        self.pass_token()
        print("==================================================")

    def multicast_to_receiver_group(self, message):
        """
        Entrega a mensagem ordenada para todos os receptores.
        """
        print("  Difundindo mensagem ordenada para o grupo receptor:")

        for receiver in self.receivers:
            receiver.deliver(message)

    def pass_token(self):
        old = self.current_sequencer().sequencer_id
        self.token_position = (self.token_position + 1) % len(self.sequencers)
        new = self.current_sequencer().sequencer_id

        print(f"Token passou de {old} para {new}.")

    def show_status(self):
        print("\n================ ESTADO DO SISTEMA ================")

        print("\nGrupo emissor:")
        for sender_id in self.senders:
            print(f"  {sender_id}")

        print("\nGrupo sequenciador, em anel lógico:")
        ring = " -> ".join(sequencer.sequencer_id for sequencer in self.sequencers)
        ring += f" -> {self.sequencers[0].sequencer_id}"
        print(f"  {ring}")

        print(f"\nSequenciador com token: {self.current_sequencer().sequencer_id}")

        print("\nBuffers dos sequenciadores:")
        for sequencer in self.sequencers:
            pending = sequencer.show_buffer(self.delivered_ids)

            if pending:
                print(f"  {sequencer.sequencer_id}: {pending}")
            else:
                print(f"  {sequencer.sequencer_id}: vazio")

        print("\nMensagens já entregues ao grupo receptor:")
        if self.delivered_ids:
            print(f"  {sorted(self.delivered_ids)}")
        else:
            print("  Nenhuma mensagem entregue ainda.")

        print("===================================================")

    def show_receiver_logs(self):
        print("\n================ LOG DOS RECEPTORES ================")

        for receiver in self.receivers:
            print(f"\n{receiver.receiver_id} entregou as mensagens nesta ordem:")

            if not receiver.delivered_messages:
                print("  Nenhuma mensagem entregue ainda.")
            else:
                for message in receiver.delivered_messages:
                    print(f"  {message}")

        print("====================================================")

    def validate_total_order(self):
        """
        Verifica se todos os receptores entregaram as mensagens na mesma ordem.
        """
        print("\n================ VERIFICAÇÃO DE ORDEM TOTAL ================")

        if not self.receivers:
            print("Não há receptores.")
            return

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

            print(f"{receiver.receiver_id}: {current_order}")

            if current_order != reference_order:
                all_same_order = False

        if all_same_order:
            print("\nResultado: todos os receptores entregaram as mensagens na mesma ordem.")
        else:
            print("\nResultado: houve divergência na ordem de entrega.")

        print("=============================================================")


def print_menu():
    print("\n================ MENU ================")
    print("1 - Enviar mensagem")
    print("2 - Processar sequenciador com token")
    print("3 - Processar várias rodadas do token")
    print("4 - Mostrar estado do sistema")
    print("5 - Mostrar mensagens entregues nos receptores")
    print("6 - Verificar ordem total")
    print("0 - Sair")
    print("======================================")


def choose_sender(system):
    print("\nEmissores disponíveis:")

    for sender_id in system.senders:
        print(f"  {sender_id}")

    sender_id = input("Escolha o emissor: ").strip().upper()

    if sender_id not in system.senders:
        print("Emissor inválido.")
        return None

    return sender_id


def main():
    system = MobileSequencerSystem()

    print("\nSimulador de Sequenciador Móvel")
    print("Estrutura: Grupo Emissor -> Grupo Sequenciador -> Grupo Receptor")
    print("Apenas o sequenciador com token pode repassar mensagens aos receptores.")

    while True:
        print_menu()
        option = input("Escolha uma opção: ").strip()

        if option == "1":
            sender_id = choose_sender(system)

            if sender_id is not None:
                content = input("Digite o conteúdo da mensagem: ").strip()

                if content:
                    system.send_message(sender_id, content)
                else:
                    print("Conteúdo vazio. Mensagem não enviada.")

        elif option == "2":
            system.process_current_token()

        elif option == "3":
            try:
                rounds = int(input("Quantas rodadas do token deseja processar? "))

                if rounds <= 0:
                    print("Digite um número positivo.")
                else:
                    for _ in range(rounds):
                        system.process_current_token()

            except ValueError:
                print("Valor inválido. Digite um número inteiro.")

        elif option == "4":
            system.show_status()

        elif option == "5":
            system.show_receiver_logs()

        elif option == "6":
            system.validate_total_order()

        elif option == "0":
            print("Encerrando simulação.")
            break

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()