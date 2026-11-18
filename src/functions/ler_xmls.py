import re
from pathlib import Path

def extrair_tag(xml: str, tag: str) -> str | None:
    match = re.search(rf'<{tag}[^>]*>([^<]+)</{tag}>', xml)
    return match.group(1).strip() if match else None


def extrair_tag_no_contexto(xml: str, contexto: str, tag: str) -> str | None:
    match_ctx = re.search(rf'<{contexto}[^>]*>([\s\S]*?)</{contexto}>', xml)
    
    if not match_ctx:
        return None
    
    return extrair_tag(match_ctx.group(1), tag)


def formatar_data(data_iso: str | None) -> str | None:
    if not data_iso:
        return None
    
    data = data_iso.split('T')[0]
    ano, mes, dia = data.split('-')
    return f'{dia}/{mes}/{ano}'


def formatar_cnpj(cnpj: str | None) -> str | None:
    if not cnpj:
        return None
    
    return re.sub(r'^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$', r'\1.\2.\3/\4-\5', cnpj)


def extrair_reidi(descricao: str | None) -> str:
    if not descricao:
        return 'Não'
    
    return 'Sim' if re.search(r'\bREIDI\b', descricao) else 'Não'


def extrair_campo_da_descricao(descricao: str | None, chaves: list[str]) -> str | None:
    if not descricao:
        return None

    alternancia = '|'.join(re.escape(c) for c in chaves)
    pattern     = rf'(?:^|\|)\s*(?:{alternancia})\s*:?\s*([^|]+)'
    match       = re.search(pattern, descricao, re.IGNORECASE)

    if not match:
        return None

    return match.group(1).strip() or None


def ler_xmls(pasta_xmls: str) -> list[dict]:
    print(f'- Lendo XMLs da pasta\n')

    arquivos = sorted(Path(pasta_xmls).glob('*.xml'))

    print('>>> INICIO DA COLETA <<<')
    print(f'   → {len(arquivos)} arquivos encontrados')
    print('>>> FIM DA COLETA <<<\n')

    notas = []

    for arquivo in arquivos:
        xml              = arquivo.read_text(encoding='utf-8')
        descricao        = (
            extrair_tag_no_contexto(xml, 'serv', 'xDescServ')
            or extrair_tag(xml, 'xDescServ')
        )

        #Cancelada = arquivo começa com "CANCELADA_" (prefixo definido pelo bot.py)
        cancelada        = arquivo.name.startswith('CANCELADA_')

        valor_servico    = extrair_tag_no_contexto(xml, 'valores', 'vBC') or '0'
        
        valor_iss_raw    = extrair_tag_no_contexto(xml, 'valores', 'vISSQN') or ''
        valor_iss        = float(valor_iss_raw) if valor_iss_raw else None
        
        #valor_ret_raw    = extrair_tag_no_contexto(xml, 'valores', 'vTotalRet') or ''
        #valor_iss_retido = float(valor_ret_raw) if valor_ret_raw else None
        
        valor_liquido    = extrair_tag_no_contexto(xml, 'valores', 'vLiq') or '0'

        cod_trib_nac     = extrair_tag_no_contexto(xml, 'cServ', 'cTribNac') or ''
        cod_trib_mun     = extrair_tag_no_contexto(xml, 'cServ', 'cTribMun') or ''
        
        #Regra ISS Retido: só preenche se cTribNac == '071901'
        iss_retido = valor_iss if cod_trib_nac == '071901' else None

        nota = {
            #PLANILHA 1
            'numeroNota':   extrair_tag(xml, 'nNFSe'),
            'dataEmissao':  formatar_data(extrair_tag_no_contexto(xml, 'infDPS', 'dhEmi')),
            'cnpj':         formatar_cnpj(extrair_tag_no_contexto(xml, 'toma', 'CNPJ')),
            'razaoSocial':  extrair_tag_no_contexto(xml, 'toma', 'xNome'),
            'valorServico': float(valor_servico),

            'valorDoISS':   iss_retido, # coluna F — mesmo valor da coluna G
            'ISSRetido':    iss_retido, # coluna G — vISSQN se cTribNac == 071901, senão vazio

            'reidi':        extrair_reidi(descricao),
            'contrato':     extrair_campo_da_descricao(descricao, ['Contrato', 'contrato', 'CONTRATO', 'CT']),
            'pedido':       extrair_campo_da_descricao(descricao, ['Pedido', 'pedido', 'PEDIDO']),

            'valorLiquido': float(valor_liquido),

            #PLANILHA 2
            'serie':         extrair_tag(xml, 'serie'),
            'codigoServico': cod_trib_nac + cod_trib_mun,

            #NOTAS FISCAIS CANCELADAS
            'cancelada': cancelada,
            
            #DETALHES
            'xDescServ': descricao, 
            'codTribNac': cod_trib_nac, 
            'codTribMun': cod_trib_mun, 
        }

        notas.append(nota)

    return notas