"""
Baixa XMLs de notas emitidas via API oficial do ADN (NFS-e Nacional)
Autenticação: mTLS com certificado A1 (.pfx)

Uso:
    python baixar_xmls_api.py 01/06/2026 09/06/2026

Dependências:
    pip install requests cryptography
    
"""

import sys
import re
import os
import time
import tempfile
from pathlib import Path
from datetime import datetime

import requests
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

#CONFIGURAÇÕES
CAMINHO_PFX = r"C:\Users\Giulia\Downloads\A1_Satel 2025.pfx"
SENHA_PFX   = b"1234"
CNPJ        = "16857533000124"  # só números

BASE_URL_ADN        = "https://adn.nfse.gov.br/contribuintes"
BASE_URL_SEFIN      = "https://sefin.nfse.gov.br/SefinNacional"


def extrair_pem_do_pfx(caminho_pfx: str, senha: bytes) -> tuple[str, str]:
    """Extrai chave privada e certificado do .pfx em formato PEM (arquivos temporários)."""
    with open(caminho_pfx, "rb") as f:
        pfx_data = f.read()

    chave_privada, certificado, _ = pkcs12.load_key_and_certificates(pfx_data, senha)

    cert_pem  = certificado.public_bytes(Encoding.PEM)
    chave_pem = chave_privada.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())

    #Salva em arquivos temporários (requests precisa de caminhos de arquivo)
    tmp_cert  = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    tmp_chave = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")

    tmp_cert.write(cert_pem)
    tmp_chave.write(chave_pem)
    tmp_cert.close()
    tmp_chave.close()

    return tmp_cert.name, tmp_chave.name


def validar_data(data: str) -> bool:
    return bool(re.match(r"^\d{2}/\d{2}/\d{4}$", data))


def formatar_data_iso(data_br: str) -> str:
    #Converte dd/mm/aaaa → aaaa-mm-dd
    dia, mes, ano = data_br.split("/")
    return f"{ano}-{mes}-{dia}"


def listar_notas(session: requests.Session, cnpj: str, data_inicio: str, data_fim: str) -> list[dict]:
    
    #Consulta notas emitidas pelo CNPJ no período via ADN Contribuintes.
    #Endpoint: GET /dfe/prestador/{cnpj}
    url = f"{BASE_URL_ADN}/dfe/prestador/{cnpj}"
    params = {
        "dataInicio": data_inicio,  #aaaa-mm-dd
        "dataFim":    data_fim,
    }

    print(f"- Consultando notas: {url}")
    print(f"  → Período: {data_inicio} a {data_fim}\n")

    notas     = []
    pagina    = 0
    tam_pagina = 50

    while True:
        params["pagina"]    = pagina
        params["tamPagina"] = tam_pagina

        resp = session.get(url, params=params, timeout=30)

        print(f"  → Página {pagina}: status {resp.status_code}")

        if resp.status_code == 200:
            dados = resp.json()

            #A API retorna lista de chaves de acesso ou objetos com chaveAcesso
            if isinstance(dados, list):
                if not dados:
                    break
                notas.extend(dados)
                if len(dados) < tam_pagina:
                    break
                pagina += 1

            elif isinstance(dados, dict):
                #Pode ser paginado com campo "nfse" ou "documentos"
                itens = dados.get("nfse") or dados.get("documentos") or dados.get("data") or []
                if not itens:
                    break
                notas.extend(itens)
                if len(itens) < tam_pagina:
                    break
                pagina += 1

            else:
                print(f"  ⚠ Formato inesperado: {type(dados)}")
                print(f"  Resposta: {str(dados)[:500]}")
                break

        elif resp.status_code == 404:
            print("  → Nenhuma nota encontrada para o período.")
            break

        else:
            print(f"  ❌ Erro {resp.status_code}: {resp.text[:500]}")
            break

        time.sleep(0.5)

    return notas


def baixar_xml(session: requests.Session, chave_acesso: str, pasta_xmls: Path, cancelada: bool = False) -> bool:
    
    #Baixa o XML de uma nota pela chave de acesso.
    #Endpoint: GET /nfse/{chaveAcesso} na Sefin Nacional
    url = f"{BASE_URL_SEFIN}/nfse/{chave_acesso}"

    resp = session.get(url, timeout=30)

    if resp.status_code == 200:
        prefixo      = "CANCELADA_" if cancelada else ""
        nome_arquivo = f"{prefixo}{chave_acesso}.xml"
        (pasta_xmls / nome_arquivo).write_bytes(resp.content)
        
        print(f"  ✅ {nome_arquivo}")
        return True

    else:
        print(f"  ❌ Erro {resp.status_code} para chave {chave_acesso[:20]}...: {resp.text[:200]}")
        return False


def main():
    #Valida argumentos
    args = sys.argv[1:]
    
    if len(args) < 2:
        print("Uso: python baixar_xmls_api.py dd/mm/aaaa dd/mm/aaaa")
        sys.exit(1)

    data_inicio_br, data_fim_br = args[0], args[1]

    if not validar_data(data_inicio_br) or not validar_data(data_fim_br):
        print("⚠ Datas inválidas. Use dd/mm/aaaa.")
        sys.exit(1)

    data_inicio_iso = formatar_data_iso(data_inicio_br)
    data_fim_iso    = formatar_data_iso(data_fim_br)

    print(f"\n- Período: {data_inicio_br} - {data_fim_br}\n")

    #Extrai certificado
    print("- Extraindo certificado...\n")
    try:
        caminho_cert, caminho_chave = extrair_pem_do_pfx(CAMINHO_PFX, SENHA_PFX)
        
    except Exception as e:
        print(f"❌ Erro ao ler o certificado: {e}")
        sys.exit(1)

    #Cria pasta de saída
    nome_pasta     = f"{data_inicio_br.replace('/', '.')} - {data_fim_br.replace('/', '.')}"
    pasta_execucao = Path("./downloads") / nome_pasta
    pasta_xmls     = pasta_execucao / "xmls"
    pasta_xmls.mkdir(parents=True, exist_ok=True)

    #Cria sessão com mTLS
    session      = requests.Session()
    session.cert = (caminho_cert, caminho_chave)
    session.verify = True  # valida certificado do servidor

    try:
        #Lista notas do período
        print(">>> INICIO DA COLETA <<<")
        notas = listar_notas(session, CNPJ, data_inicio_iso, data_fim_iso)
        print(f"\n>>> FIM DA COLETA: {len(notas)} notas encontradas <<<\n")

        if not notas:
            print("- Nenhuma nota para baixar.")
            return

        #Mostra amostra do retorno para entender o formato
        print("- Amostra do retorno da API:")
        print(str(notas[0])[:300])
        print()

        #Baixa os XMLs
        print("Baixando XMLs...")
        sucesso = 0
        erro    = 0

        for nota in notas[:10]:  #TESTE: baixa só as 10 primeiras
            #A chave pode vir como string direta ou dentro de um dict
            if isinstance(nota, str):
                chave_acesso = nota
                cancelada    = False
                
            elif isinstance(nota, dict):
                chave_acesso = (
                    nota.get("chaveAcesso")
                    or nota.get("chNFSe")
                    or nota.get("chave")
                    or str(nota)
                )
                situacao  = nota.get("situacao") or nota.get("status") or ""
                cancelada = "CANCEL" in str(situacao).upper()
                
            else:
                print(f"  ⚠ Formato desconhecido: {nota}")
                continue

            ok = baixar_xml(session, chave_acesso, pasta_xmls, cancelada)
            
            if ok:
                sucesso += 1
                
            else:
                erro += 1

            time.sleep(0.3)

        print(f"\n- Download concluído: {sucesso} ✅  {erro} ❌")
        print(f"- XMLs salvos em: {pasta_xmls.resolve()}")

    finally:
        #Remove arquivos temporários do certificado
        os.unlink(caminho_cert)
        os.unlink(caminho_chave)


if __name__ == "__main__":
    main()
