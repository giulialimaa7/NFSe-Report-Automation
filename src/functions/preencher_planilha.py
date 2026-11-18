from openpyxl import load_workbook

#Mapeia número do mês para a coluna na aba "Notas Fiscais Canceladas"
#Cabeçalhos na linha 2: B=Fevereiro, C=Março ... L=Dezembro
MES_PARA_COLUNA = {
    1:  'B',  #Janeiro
    2:  'C',  #Fevereiro
    3:  'D',  #Março
    4:  'E',  #Abril
    5:  'F',  #Maio
    6:  'G',  #Junho
    7:  'H',  #Julho
    8:  'I',  #Agosto
    9:  'J',  #Setembro
    10: 'K',  #Outubro
    11: 'L',  #Novembro
    12: 'M',  #Dezembro
}


def extrair_mes(data_formatada: str | None) -> int | None:
    if not data_formatada:
        return None
    
    partes = data_formatada.split('/')
    
    if len(partes) < 2:
        return None
    
    return int(partes[1])

def preencher_planilha(notas: list[dict], caminho_relatorio: str) -> None:
    print('- Preenchendo planilha')

    wb = load_workbook(caminho_relatorio)

    notas_normais    = [n for n in notas if not n['cancelada']]
    notas_canceladas = [n for n in notas if n['cancelada']]

    print('- Notas separadas')
    print(f'   → {len(notas_normais)} notas normais')
    print(f'   → {len(notas_canceladas)} notas canceladas\n')

    #PLANILHA 1 
    ws1 = wb['Planilha1']

    proxima_linha = 3
    
    while ws1[f'A{proxima_linha}'].value is not None:
        proxima_linha += 1

    for nota in notas_normais:
        ws1[f'A{proxima_linha}'] = nota['numeroNota']
        ws1[f'B{proxima_linha}'] = nota['dataEmissao']
        ws1[f'C{proxima_linha}'] = nota['cnpj']
        ws1[f'D{proxima_linha}'] = nota['razaoSocial']
        ws1[f'E{proxima_linha}'] = nota['valorServico']
        ws1[f'F{proxima_linha}'] = nota['valorDoISS']
        ws1[f'G{proxima_linha}'] = nota['ISSRetido']
        ws1[f'H{proxima_linha}'] = nota['reidi']
        ws1[f'J{proxima_linha}'] = nota['contrato']
        ws1[f'M{proxima_linha}'] = nota['pedido']
        ws1[f'R{proxima_linha}'] = nota['valorLiquido']

        proxima_linha += 1

    print('- PLANILHA 1 preenchida!')
    

    #PLANILHA 2 
    ws2 = wb['Planilha2']

    proxima_linha2 = 3
    
    while ws2[f'A{proxima_linha2}'].value is not None:
        proxima_linha2 += 1

    primeira_linha_dados = proxima_linha2

    for nota in notas_normais:
        ws2[f'A{proxima_linha2}'] = nota['dataEmissao']
        ws2[f'B{proxima_linha2}'] = nota['serie']
        ws2[f'C{proxima_linha2}'] = nota['numeroNota']
        ws2[f'D{proxima_linha2}'] = nota['codigoServico']
        ws2[f'E{proxima_linha2}'] = nota['razaoSocial']
        ws2[f'F{proxima_linha2}'] = nota['cnpj']
        ws2[f'G{proxima_linha2}'] = nota['valorServico']
        ws2[f'H{proxima_linha2}'] = nota['valorLiquido']
        ws2[f'I{proxima_linha2}'] = nota['contrato']

        proxima_linha2 += 1

    ultima_linha_dados = proxima_linha2 - 1

    #H1 e I1 — soma das colunas de todas as notas inseridas
    if primeira_linha_dados <= ultima_linha_dados:
        ws2['G1'] = f'=SUM(G{primeira_linha_dados}:G{ultima_linha_dados})'
        ws2['H1'] = f'=SUM(H{primeira_linha_dados}:H{ultima_linha_dados})'

    print('- PLANILHA 2 preenchida!')

    #NOTAS FISCAIS CANCELADAS ─────────────────────────────────────────────
    if notas_canceladas:
        ws_canc = wb['Notas Fiscais Canceladas']

        proxima_linha_por_coluna = {}

        for nota in notas_canceladas:
            mes    = extrair_mes(nota['dataEmissao'])
            coluna = MES_PARA_COLUNA.get(mes)

            if not coluna:
                print(f"⚠ NOTA {nota['numeroNota']}: MÊS INVÁLIDO OU NÃO MAPEADO ({nota['dataEmissao']})")
                continue

            if coluna not in proxima_linha_por_coluna:
                linha = 3
                
                while ws_canc[f'{coluna}{linha}'].value is not None:
                    linha += 1
                    
                proxima_linha_por_coluna[coluna] = linha

            linha_alvo = proxima_linha_por_coluna[coluna]
            ws_canc[f'{coluna}{linha_alvo}'] = nota['numeroNota']
            proxima_linha_por_coluna[coluna] += 1

        print("- ABA 'Notas Fiscais Canceladas' PREENCHIDA!")
        
    else:
        print('\n- Nenhuma nota cancelada encontrada.\n')
        
    #DETALHES
    ws_det = wb['Detalhes']
 
    proxima_linha_det = 2
    
    while ws_det[f'B{proxima_linha_det}'].value is not None:
        proxima_linha_det += 1
 
    for nota in notas_normais:
        ws_det[f'B{proxima_linha_det}'] = nota['numeroNota']
        ws_det[f'C{proxima_linha_det}'] = nota['xDescServ']
        ws_det[f'D{proxima_linha_det}'] = nota['codTribNac']
        ws_det[f'E{proxima_linha_det}'] = nota['codTribMun']
        
        proxima_linha_det += 1
 
    print("- ABA 'Detalhes' PREENCHIDA!") 

    wb.save(caminho_relatorio)