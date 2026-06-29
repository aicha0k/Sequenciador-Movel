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

