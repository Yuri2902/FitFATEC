# Traduções do catálogo de exercícios — FitFATEC

Fonte dos metadados: `hasaneyldrm/exercises-dataset` (ExerciseDB, 1.324 exercícios).
Licença aplicável aos **dados e textos**: MIT; mantenha os avisos de autoria
originais em `ia_academia/dados/EXERCISES_DATASET_LICENSE.txt` e
`ia_academia/dados/EXERCISES_DATASET_NOTICE.md`.

O FitFATEC gera `dados/nomes_exercicios_pt.json`, uma **cópia derivada** com
`ID → nome_original → nome_pt`. Essa camada é exclusiva do FitFATEC e não copia
as traduções AGPL do openGym. Não utiliza imagens ou animações do Gym visual.

## Revisão de traduções

A tradução automática pelo Gemini usa nome, categoria, equipamento e músculo
alvo. A IA pode confundir movimentos próximos (por exemplo, agachamento com
passada cruzada versus agachamento búlgaro). O CSV gerado documenta a tradução
e marca casos ambíguos. Antes de divulgar o FitFATEC, revisar especialmente
exercícios menos comuns com um profissional qualificado.

Quando o modelo gerar uma tradução incorreta, edite `nome_pt` do ID correto em
`dados/nomes_exercicios_pt.json` sem alterar `nome_original` ou o ID. Se a
tradução estiver validada por vocês, marque `"origem": "revisao_humana"` e
`"revisar": false`. Ao rodar novamente, os registros válidos são preservados.

Licença e fonte: https://github.com/hasaneyldrm/exercises-dataset
