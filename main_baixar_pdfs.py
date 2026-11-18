import os
import sys
from pathlib import Path
from src.baixar_pdfs import baixar_pdfs

#Quando rodando como .exe (PyInstaller), usa sys._MEIPASS
#Quando rodando como script normal, usa o diretório do arquivo
if getattr(sys, 'frozen', False):
  base_path = Path(sys.executable).parent
  
else:
  base_path = Path(__file__).parent

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(base_path / '.playwright-browsers')

if __name__ == '__main__':
  baixar_pdfs()