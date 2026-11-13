# Checklist da avaliação — Engenharia de Software II

Verificado contra `documentacao/requisitos_ia.pdf` (11 páginas, fornecido com o projeto). Status em 13/11/2026.

| Requisito do enunciado | Evidência na versão atual | Situação |
|---|---|---|
| IA generativa | `assistente.py`, integração `google-genai`, testes mockados e uso relatado nas capturas | Implementado; exige chave/conectividade |
| Nome e tom/persona digital | `assistente.py` (`PERSONA`) e `DOCUMENTO_PROJETO.md` | Descrito |
| Traços antropomórficos completos | Persona atual é onça-mascote; não há documentação de pele/cabelo humanos | Alinhar interpretação com professor |
| Imagem gerada por IA da persona | `public/img/kiara.svg` existe, mas sua procedência não está comprovada | Pendente comprovação/arte final |
| Interface conversacional | `public/index.html`, CSS e JS | Implementado (prototipado) |
| Agendar aula | `servidor.py` e formulário da página | Implementado; validar com MySQL real nesta versão |
| Série de exercícios | Catálogo, `plano_kiara.py` e Kiara | Implementado (não persiste série) |
| Aquecimentos | `catalogo.py` e conversa | Implementado como catálogo/explicação |
| Treino principal e secundário | `catalogo.py` | Implementado em série demonstrativa |
| Nível iniciante/intermediário/avançado | Interface e `catalogo.py` | Implementado, dados ainda manuais |
| Cinco fluxos completos | `FLUXOS_CONVERSA.md` traz 6 fluxos demonstrativos | Documentados; validar em execução |
| Protótipo navegável | Flask serve `/`, `/conta`, agendas e APIs | Implementado |
| Documento de projeto | `DOCUMENTO_PROJETO.md` | Criado nesta revisão |
| Demonstração por vídeo ou apresentação | Não consta artefato no ZIP | Pendente |
| Precificação | `PRECIFICACAO.md` contém categorias e método de cálculo | Rascunho; falta estimativa numérica aprovada |

**Observações:** o PDF usa exemplo de solicitar matrícula no fluxo. O FitFATEC identifica matrícula automaticamente pela sessão — adaptação de UX e segurança a explicar na apresentação. O risco de desistência é recurso adicional do grupo, não requisito mínimo do enunciado.
