import re
import shutil
import tempfile
import os
import time
import base64
import gzip
import requests

from pathlib import Path
from playwright.sync_api import sync_playwright
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

from .functions.iniciar_sessao import iniciar_sessao
from .functions.utils import validar_argumentos
from .functions.ler_xmls import ler_xmls
from .functions.coletar_hrefs import coletar_hrefs_da_pagina
from .functions.preencher_planilha import preencher_planilha

#CERTIFICADO DIGITAL 
CAMINHO_PFX = r"C:\Users\Giulia\Downloads\A1_Satel 2025.pfx"
SENHA_PFX   = b"1234"

def _extrair_pem(caminho_pfx: str, senha: bytes) -> tuple[str, str]:
    #Extrai cert + chave do .pfx em arquivos .pem temporários.
    with open(caminho_pfx, "rb") as f:
        pfx_data = f.read()
        
    chave, cert, _ = pkcs12.load_key_and_certificates(pfx_data, senha)
    tmp_cert  = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    tmp_chave = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    tmp_cert.write(cert.public_bytes(Encoding.PEM))
    tmp_chave.write(chave.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
    tmp_cert.close()
    tmp_chave.close()
    return tmp_cert.name, tmp_chave.name


def _baixar_xml_api(session: requests.Session, chave_acesso: str) -> bytes | None:
    
    #Baixa o XML da nota via API Sefin Nacional (mTLS).
    #A API retorna JSON com o XML dentro de 'nfseXmlGZipB64' (GZip + Base64).
    
    url  = f"https://sefin.nfse.gov.br/SefinNacional/nfse/{chave_acesso}"
    resp = session.get(url, timeout=30)

    if resp.status_code == 200:
        dados   = resp.json()
        xml_b64 = dados.get("nfseXmlGZipB64")
        
        if xml_b64:
            xml_gz  = base64.b64decode(xml_b64)
            xml_raw = gzip.decompress(xml_gz)
            return xml_raw
        
        return resp.content  # fallback: resposta já é XML direto

    print(f"    API status {resp.status_code}: {resp.text[:200]}")
    return None


def gerar_relatorio():
    #Uso: python main.py 16/04/2026 17/04/2026
    data_inicio, data_fim = validar_argumentos()
    print(f'\n- Período escolhido: {data_inicio} - {data_fim}\n')

    #Nome da pasta: "16.04.2026 - 17.04.2026"
    nome_pasta     = f"{data_inicio.replace('/', '.')} - {data_fim.replace('/', '.')}"
    pasta_execucao = Path('./downloads') / nome_pasta
    pasta_xmls     = pasta_execucao / 'xmls'

    #BROWSER 
    with sync_playwright() as p:
        browser, context, page = iniciar_sessao(p, data_inicio, data_fim)

        #Descobre total de páginas
        def get_total_paginas():
            
            try:
                texto = page.inner_text('body')
                match = re.search(r'Total de (\d+) registros', texto)

                if match:
                    total_registros = int(match.group(1))
                    return max(1, -(-total_registros // 15))  # ceil division

                #Fallback: maior número na paginação
                links   = page.query_selector_all('ul.pagination li a')
                numeros = [int(a.inner_text().strip()) for a in links if a.inner_text().strip().isdigit()]
                return max(numeros) if numeros else 1

            except Exception:
                return 1

        total_paginas = get_total_paginas()

        print('>>> INICIO DA COLETA <<<')
        todas_notas = []
        for pagina in range(1, total_paginas + 1):
            print(f'Coletando página {pagina}/{total_paginas}')

            notas_da_pagina = coletar_hrefs_da_pagina(page)
            todas_notas.extend(notas_da_pagina)
            print(f'   → {len(notas_da_pagina)} notas encontradas')

            #Clica na próxima página se não for a última
            if pagina < total_paginas:
                proximo = str(pagina + 1)
                botao   = page.locator('ul.pagination li a').filter(has_text=re.compile(f'^{proximo}$'))

                if botao.count() > 0:
                    botao.click()
                else:
                    page.locator('ul.pagination a[data-original-title="Próxima"]').click()

                page.wait_for_timeout(3000)

        print('>>> FIM DA COLETA <<<\n')

        canceladas_count = sum(1 for n in todas_notas if n['cancelada'])
        print(f'- {len(todas_notas)} notas emitidas')
        print(f'- {canceladas_count} cancelada(s)')

        if not todas_notas:
            print('- Nenhuma nota encontrada para o período!')
            browser.close()
            return

        pasta_xmls.mkdir(parents=True, exist_ok=True)
        print('\n- Pasta do período criada')

        browser.close()

    #DOWNLOAD VIA API (mTLS) 
    print('- Extraindo certificado...')
    caminho_cert, caminho_chave = _extrair_pem(CAMINHO_PFX, SENHA_PFX)

    session        = requests.Session()
    session.cert   = (caminho_cert, caminho_chave)
    session.verify = True

    try:
        print('Baixando XMLs via API...\n')
        sucesso = erro = 0

        for nota in todas_notas:
            href         = nota['href']
            cancelada    = nota['cancelada']
            chave_acesso = href.split('/')[-1]
            prefixo      = 'CANCELADA_' if cancelada else ''
            nome_arquivo = f'{prefixo}{chave_acesso}.xml'

            conteudo = _baixar_xml_api(session, chave_acesso)

            if conteudo:
                (pasta_xmls / nome_arquivo).write_bytes(conteudo)
                print(f'  ✅ {nome_arquivo}')
                sucesso += 1
                
            else:
                print(f'  ❌ Erro: {nome_arquivo}')
                erro += 1

            time.sleep(0.3)

        print(f'\n- Download concluído: {sucesso} ✅  {erro} ❌\n')

    finally:
        os.unlink(caminho_cert)
        os.unlink(caminho_chave)

    #Lê XMLs e preenche o relatório
    notas = ler_xmls(str(pasta_xmls))
    print('- Dados processados')

    modelo_origem     = Path('./modelo/Planilha_modelo_TI.xlsx')
    relatorio_destino = pasta_execucao / f'Relatório {nome_pasta}.xlsx'
    shutil.copy(modelo_origem, relatorio_destino)

    preencher_planilha(notas, str(relatorio_destino))
    print('- Relatório gerado\n')
