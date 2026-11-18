import re

def extrair_numero_nota(chave: str) -> str:
  #Extrai 4 dígitos após os zeros no meio da chave de acesso
  #Exemplo: 33045572216857533000124000000000 >> 3033 << 26049110047414
  match = re.search(r'0{6,}(\d{4})\d+$', chave)
  return match.group(1) if match else chave