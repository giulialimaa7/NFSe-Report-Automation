import sys
from pathlib import Path

#Adiciona a raiz do projeto ao path para encontrar src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.functions.ler_xmls import ler_xmls
from src.functions.preencher_planilha import preencher_planilha

pasta_xmls       = Path('./downloads/01.03.2026 - 31.03.2026/xmls')
caminho_relatorio = Path('./downloads/01.03.2026 - 31.03.2026/Relatório 01.03.2026 - 31.03.2026.xlsx')

notas = ler_xmls(str(pasta_xmls))
print(f'- {len(notas)} notas lidas')

preencher_planilha(notas, str(caminho_relatorio))
print(f'- Relatório preenchido: {caminho_relatorio}')