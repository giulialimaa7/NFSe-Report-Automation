# Bot NFS-e

## Estrutura
```
BOT-FINANCEIRO/
├── main.py
├── requirements.txt
├── modelo/
│   └── Planilha_modelo_TI.xlsx   ← copiar aqui
├── downloads/                    ← gerado automaticamente
└── src/
    ├── bot.py
    └── functions/
        ├── coletar_hrefs.py
        ├── ler_xmls.py
        └── preencher_planilha.py
```

## Instalação
```bash
pip install -r requirements.txt
playwright install chromium
```

## Uso
```bash
python main.py 16/04/2026 17/04/2026
```

## Gerar executável (.exe)
```bash
pip install pyinstaller
pyinstaller --onefile --name bot main.py
```

O `.exe` ficará em `dist/bot.exe`.
Copie junto: pasta `modelo/` e browsers do Playwright.
