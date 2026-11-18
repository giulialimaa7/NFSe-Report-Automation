import re
import time
import pyautogui
from playwright.sync_api import sync_playwright

def iniciar_sessao(playwright, data_inicio: str, data_fim: str):
  browser = playwright.chromium.launch(headless=False, slow_mo=100)
  context = browser.new_context(ignore_https_errors=True)
  page    = context.new_page()

  page.goto('https://www.nfse.gov.br/EmissorNacional/Login?ReturnUrl=%2fEmissorNacional')
  print('- Abriu o portal')

  page.wait_for_timeout(1000)
  try:
    page.locator('a.img-certificado').click(timeout=3000)
    
  except Exception:
    pass
  
  print('- Clicou no certificado digital')

  time.sleep(5)
  pyautogui.moveTo(760, 400)
  pyautogui.click()
  time.sleep(0.5)
  pyautogui.press('down')
  time.sleep(0.5)
  pyautogui.press('enter')
  print('- Certificado selecionado')

  page.wait_for_load_state('networkidle')
  print('- Login realizado:', page.url, '\n')

  page.wait_for_selector('a[href="/EmissorNacional/Notas/Emitidas"]')
  page.locator('a[href="/EmissorNacional/Notas/Emitidas"]').click()
  print('- Clicou em NFS-e Emitidas')

  page.wait_for_timeout(2000)
  page.fill('#datainicio', data_inicio)
  page.wait_for_timeout(1000)
  page.fill('#datafim', data_fim)
  print("- Período preenchido")
  #print(f'- Período preenchido: {data_inicio} - {data_fim}')

  page.wait_for_timeout(2000)
  page.wait_for_selector('button:has-text("Filtrar")')
  page.locator('button:has-text("Filtrar")').click()
  print('- Clicou em Filtrar\n')

  page.wait_for_timeout(5000)
    
  return browser, context, page