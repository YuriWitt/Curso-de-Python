Lottery Analyzer
MVP em Python para importar resultados da Mega-Sena e da Lotofácil, manter o histórico em SQLite e gerar uma análise reproduzível.

O sistema calcula frequência e atraso de cada dezena e usa esses indicadores apenas para ordenar uma sugestão de jogo. Isso é uma heurística descritiva: sorteios independentes não ficam mais previsíveis com o histórico, portanto a probabilidade matemática de uma combinação continua a mesma.
Preparar
cd Curso-de-Python
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install --no-deps --no-build-isolation -e .
python -m unittest discover -s tests -v
Importar um arquivo local
JSON pode ser um objeto ou uma lista. Os campos aceitos são numero/`contest`, listaDezenas/`numbers` e dataApuracao/`draw_date`. CSV usa as colunas equivalentes.
lottery-analyzer --db data/lottery.db import --game mega-sena --file dados/megasena.json
lottery-analyzer --db data/lottery.db import --game lotofacil --file dados/lotofacil.csv
lottery-analyzer --db data/lottery.db analyze --game todos
Sincronizar a API da Caixa
O comando consulta servicebus2.caixa.gov.br. Sem --end, --start 0 baixa o último concurso; para reconstruir o histórico, informe o intervalo e execute novamente se a rede interromper a operação:
lottery-analyzer --db data/lottery.db sync --game mega-sena --start 0 --end 1
lottery-analyzer --db data/lottery.db sync --game lotofacil --start 0 --end 1
O ambiente precisa permitir o domínio da API. Se a rede estiver bloqueada, use import com um arquivo exportado e continue a análise offline.
Probabilidade
Para uma aposta simples, acertar todos os números equivale a 1 em 50.063.860 na Mega-Sena e 1 em 3.268.760 na Lotofácil. O relatório também exibe a probabilidade exata de cada quantidade de acertos que gera prêmio na modalidade.
