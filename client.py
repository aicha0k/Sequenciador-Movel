import json
import socket


HOST = "127.0.0.1"
PORT = 5000


def send_request(sock, request):
    message = json.dumps(request) + "\n"
    sock.sendall(message.encode("utf-8"))

    response_line = b""

    while not response_line.endswith(b"\n"):
        chunk = sock.recv(4096)

        if not chunk:
            raise ConnectionError("Conexão com o servidor foi encerrada.")

        response_line += chunk

    response = json.loads(response_line.decode("utf-8"))
    return response


def print_menu():
    print("\n================ MENU CLIENTE ================")
    print("1 - Enviar mensagem ao servidor")
    print("2 - Processar sequenciador com token")
    print("3 - Processar várias rodadas do token")
    print("4 - Mostrar estado do servidor")
    print("5 - Mostrar mensagens entregues nos receptores")
    print("6 - Verificar ordem total")
    print("0 - Sair")
    print("==============================================")


def choose_sender():
    valid_senders = ["E1", "E2", "E3"]

    print("\nEmissores disponíveis:")
    for sender in valid_senders:
        print(f"  {sender}")

    sender_id = input("Escolha o emissor: ").strip().upper()

    if sender_id not in valid_senders:
        print("Emissor inválido.")
        return None

    return sender_id


def main():
    print("Cliente do Sequenciador Móvel")
    print(f"Conectando ao servidor {HOST}:{PORT}...")

    try:
        with socket.create_connection((HOST, PORT)) as sock:
            print("Conectado ao servidor.")

            while True:
                print_menu()
                option = input("Escolha uma opção: ").strip()

                if option == "1":
                    sender_id = choose_sender()

                    if sender_id is None:
                        continue

                    content = input("Digite o conteúdo da mensagem: ").strip()

                    if not content:
                        print("Conteúdo vazio. Mensagem não enviada.")
                        continue

                    response = send_request(sock, {
                        "command": "SEND",
                        "sender_id": sender_id,
                        "content": content
                    })

                    print("\n--- Resposta do servidor ---")
                    print(response["output"])

                elif option == "2":
                    response = send_request(sock, {
                        "command": "PROCESS_ONE"
                    })

                    print("\n--- Resposta do servidor ---")
                    print(response["output"])

                elif option == "3":
                    try:
                        n = int(input("Quantas rodadas deseja processar? "))

                        if n <= 0:
                            print("Digite um número positivo.")
                            continue

                        response = send_request(sock, {
                            "command": "PROCESS_N",
                            "n": n
                        })

                        print("\n--- Resposta do servidor ---")
                        print(response["output"])

                    except ValueError:
                        print("Valor inválido. Digite um número inteiro.")

                elif option == "4":
                    response = send_request(sock, {
                        "command": "STATUS"
                    })

                    print("\n--- Estado do servidor ---")
                    print(response["output"])

                elif option == "5":
                    response = send_request(sock, {
                        "command": "RECEIVER_LOGS"
                    })

                    print("\n--- Log dos receptores ---")
                    print(response["output"])

                elif option == "6":
                    response = send_request(sock, {
                        "command": "VALIDATE_TOTAL_ORDER"
                    })

                    print("\n--- Verificação ---")
                    print(response["output"])

                elif option == "0":
                    print("Encerrando cliente.")
                    break

                else:
                    print("Opção inválida.")

    except ConnectionRefusedError:
        print("Não foi possível conectar ao servidor.")
        print("Verifique se o server.py está rodando.")
    except ConnectionError as error:
        print(f"Erro de conexão: {error}")


if __name__ == "__main__":
    main()