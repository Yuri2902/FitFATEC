# FitFATEC — fontes e licenças dos exercícios

## Origem permitida

A biblioteca adicional de nomes/músculos/equipamentos provém de:

- **ExerciseDB v1**, AscendAPI (conteúdo de origem).
- **hasaneyldrm/exercises-dataset**, Hasan Emir Yıldırım — metadados e instruções sob licença MIT: https://github.com/hasaneyldrm/exercises-dataset
- O projeto **openGym**, de Duarte Santos, indicou essa fonte original: https://github.com/DuarteSantos8/openGym e https://github.com/DuarteSantos8/openGym/blob/main/NOTICE.md

Usamos apenas os metadados básicos da fonte MIT: `id`, `name`, `category`, `target`, `equipment` e `secondary_muscles`.
O importador descarrega os documentos oficiais `LICENSE` e `NOTICE.md` da fonte original e os salva em `ia_academia/dados/`, junto do arquivo de dados. **Mantenha esses dois arquivos no repositório sempre que publicar ou distribuir os dados importados**, além deste documento.

## Separação de licenças

- **openGym** é AGPL-3.0. Seu código, suas novas descrições e traduções próprias não foram copiados.
- Metadados de exercícios de **hasaneyldrm/exercises-dataset** estão sujeitos à licença MIT e devem manter o aviso de direitos autorais e o texto da licença.
- **Imagens, GIFs, animações, miniaturas e vídeos** do openGym/dataset pertencem a terceiros, principalmente Gym visual. **Não os copiamos, baixamos, exibimos por link ou enviamos a qualquer IA.** O uso por outros aplicativos requer permissão do titular.
- Atribuição de dados não constitui endosso do FitFATEC pelos titulares, e informações do catálogo não são prescrições de treinamento individualizadas.

## Aviso de licença MIT da fonte

Copyright (c) 2026 Hasan Emir Yıldırım.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation and data files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Para evitar dúvidas, mantenha também os arquivos originais `EXERCISES_DATASET_LICENSE.txt` e `EXERCISES_DATASET_NOTICE.md` que o importador gera a partir da fonte.
