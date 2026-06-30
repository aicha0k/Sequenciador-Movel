# Sequenciador Móvel

## Funcionamento

O sequenciador móvel é uma entidade/processo que fica responsável por definir a ordem das mensagens ou eventos em um sistema distribuído,com a diferença que essa função de sequenciar pode “mudar de lugar” entre os nós do sistema. Essa técnica surgiu como uma solução para os problemas de confiabilidade encontrados no modelo de sequenciador fixo.

>  A difusão atômica garante que todos os processos corretos entregarão todas as mensagens e na mesma ordem total destas mensagens. Desta forma, todos os processos têm a mesma visão do sistema e podem agir de maneira consistente sem comunicações adicionais.

Diferente do sequenciador fixo, onde um único nó decide a ordem de todas as mensagens, o sequenciador móvel distribui essa responsabilidade entre um conjunto de nós.

É definido um grupo pequeno de processos (geralmente entre 2 a 4 membros) que formam um anel lógico, estes são o Grupo de Sequenciadores.

O privilégio de ordenar e repassar as mensagens circula por esse anel por meio de um *token*. Apenas o processo que possui o bastão no momento pode definir a ordem e enviar as mensagens ao grupo receptor.

Quando um emissor quer enviar uma mensagem, ele a difunde para todo o **grupo de sequenciadores**. O sequenciador que detém o bastão recebe essa mensagem, atribui-lhe uma ordem e a repassa para os destinatários finais

Como cada processo receptor conhece a sequência exata dos processos no anel lógico dos sequenciadores, eles conseguem estabelecer uma **ordem total determinística** das mensagens recebidas, garantindo que todos os membros do grupo vejam as informações na mesma sequência.

### Vantagens

- Ao contrário do sequenciador fixo, que é um ponto único de falha (se ele cai, o sistema para), o sequenciador móvel permite que o sistema continue operando mesmo que um dos coordenadores falhe;
- Maior escalabilidade: Permite que o grupo emissor cresça sem sobrecarregar um único ponto central de forma permanente;

### Desvantagens

- Perda do Token: Se o processo que está com o bastão falha no momento da posse, o sistema precisa de mecanismos para regenerar o *token* e manter a circulação;
- Todos os receptores precisam saber a ordem correta do anel lógico dos sequenciadores para que a ordenação funcione corretamente;

Para esse algoritmo, um código demonstrativo de um sequenciador móvel, que envolve um grupo emissor, um grupo sequenciador organizado em anel lógico com token, e um grupo receptor. O emissor difunde a mensagem ao grupo sequenciador, e apenas o sequenciador que possui o token repassa a mensagem ao grupo receptor.

A aplicação foi implementada no modelo cliente-servidor. O cliente representa o grupo emissor, permitindo que o usuário escolha um emissor e envie mensagens ao servidor. O servidor executa o algoritmo de sequenciador móvel, mantendo o grupo sequenciador em anel lógico, o token de privilégio e o grupo receptor. A cada mensagem recebida, o servidor a difunde internamente ao grupo sequenciador. Apenas o sequenciador com token repassa a mensagem ao grupo receptor, atribuindo um número de sequência global.

O arquivo `client.py` é a interface entre o grupo emissor e o restante. O usuário escolhe o emissor e escreve a mensagem a ser enviada, e envia a requisição ao servidor via socket TCP.

O arquivo `server.py` mantém os metadados dos grupos sequenciador, e receptor, além de manter/atualizar os buffers dos sequenciadores, guarda a informação do anél lógico, e do token/bastão, atribui os números de sequência, e entrega as mensagens ao grupo receptor. 

O nosso sistema conta com uma interface gráfica, composto por dois programas, `server.py` e `client.py`. 

O `client.py` cria uma interface gráfica com Tkinter. A interface pode ser vista na imagem abaixo.

![image](./interface-grafica.png)

Na parte superior, o usuário escolhe entre os emissores disponiveis, chamados de E1, E2, e E3. Ao clicar em enviar, o cliente manda uma requisição pro servidor:

```
{"command": "SEND", "sender_id": "E2", "content": "blablabla"}
```
Quando o usuário clicar em _Processar 1 Passo (Token)_, o cliente manda `{"command": "PROCESS_ONE"}`.

No `server.py`, o núcleio da aplicação, possui os grupos emissor, sequenciador, e receptor. Cada sequenciador tem um buffer próprio: `self.buffer = deque()`. O servidor também guarda a posição atual do token, o número global de sequência, e as mensagens já entregues.

Quando uma mensagem chega, o servidor cria um identificador, `E2.1` por exemplo. Isso significa que é primeira mensagem enviada pelo emissor E2. Depois, essa mensagem é colocada no buffer de sequenciadores, como ilustrado abaixo:

```
S1 recebe E2.1
S2 recebe E2.1
S3 recebe E2.1
```
Isso simula a difusão do emissor para o grupo sequenciador.

O token define qual sequenciador tem o direito de repassar uma mensagem ao grupo receptor. Na imagem, token está com S2. Quando o usuário clica em `Processar 1 Passo (Token)`, o servidor executa o seguinte fluxo:

1. Verifica quem está com o token.
2. Esse sequenciador procura uma mensagem pendente em seu buffer.
3. Se encontrar, atribui um número de sequência global.
4. Entrega a mensagem para R1, R2 e R3.
5. Marca a mensagem como entregue.
6. Passa o token para o próximo sequenciador.

## Requisitos Funcionais

## Interação entre `client.py` e `server.py`

## Como Utilizar

