import re
import sys

#Valida formato dd/mm/aaaa
def validar_data(data: str) -> bool:
  return bool(re.match(r'^\d{2}/\d{2}/\d{4}$', data))

def validar_argumentos() -> tuple[str, str]:
  args = sys.argv[1:]

  if len(args) < 2:
    print('⚠ Informe as datas: python main.py dd/mm/aaaa dd/mm/aaaa')
    sys.exit(1)

  arg_inicio, arg_fim = args[0], args[1]

  if not validar_data(arg_inicio):
    print(f'⚠ Data inicial inválida: "{arg_inicio}". Use dd/mm/aaaa.')
    sys.exit(1)

  if not validar_data(arg_fim):
    print(f'⚠ Data final inválida: "{arg_fim}". Use dd/mm/aaaa.')
    sys.exit(1)

  return arg_inicio, arg_fim