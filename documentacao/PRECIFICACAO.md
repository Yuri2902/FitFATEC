# FitFATEC — Precificação (rascunho para avaliação)

**Estado:** proposta de premissas, **não** orçamento comercial aprovado. O projeto atual é acadêmico e não possui clientes pagantes. Preços de API, nuvem e banco dependem de provedor, região, volume e data da contratação; conferir as tabelas oficiais antes da entrega.

## 1. Escopo coberto pelo protótipo

- Chat da Kiara e geração/ajuste de treino com catálogo.
- Cadastro/login e agendamento de horários.
- Modelo demonstrativo de risco de desistência com dados fictícios.
- Não cobre suporte 24h contratado, hospedagem robusta, integração com academia real nem revisão clínica dos exercícios.

## 2. Estrutura de custos

| Componente | No protótipo local | Para operação real |
|---|---|---|
| Desenvolvimento | Trabalho acadêmico da equipe, não precificado | Definir horas e custo/hora |
| Hospedagem | Computador local da demonstração | Servidor web, domínio, HTTPS e backup |
| MySQL | Instalação local | Instância ou servidor gerenciado |
| Gemini | Pode usar cota gratuita se disponível | Custo por volume de tokens conforme modelo e contrato |
| Dados de exercícios | Metadados MIT com atribuição | Revisão técnica e manutenção das traduções |
| Segurança e operação | Testes locais | Monitoramento, controle de acesso, suporte e auditoria |

## 3. Como estimar o custo mensal

**Estimativa = infraestrutura + banco + uso de IA + manutenção**.

Para o uso do modelo: `custo_API = (tokens_entrada / 1.000.000 × tarifa_entrada) + (tokens_saida / 1.000.000 × tarifa_saida)`, respeitando a modalidade de cobrança contratada. Use valores atualizados do Google e volume mensal estimado com o grupo. A cota gratuita (quando existir) não é garantia de disponibilidade permanente.

## 4. Itens para completar com o grupo antes de apresentar

1. Quantidade estimada de alunos ativos e conversas por mês.
2. Modelo contratado e preço atualizado por tokens.
3. Se a solução será apenas demonstração ou produto comercial; se comercial, estimar preço por academia e margem.
4. Custos de hospedagem e backup, revisão profissional dos treinos e manutenção.
5. Valor/hora e esforço de suporte. 

**Conclusão:** há uma estrutura de precificação documentada, mas os **valores numéricos finais ainda estão pendentes de validação**. Não reportar como proposta comercial fechada.
