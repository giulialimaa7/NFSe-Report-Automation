def coletar_hrefs_da_pagina(page) -> list[dict]:
    try:
        page.wait_for_selector('table.table-striped tbody tr', timeout=5000)
        
    except Exception:
        pass

    return page.eval_on_selector_all(
        'table.table-striped tbody tr',
        '''rows => rows.reduce((acc, tr) => {
            const linkXML = tr.querySelector('a[href*="/Notas/Download/NFSe/"]');
            const linkPDF = tr.querySelector('a[href*="/Notas/Download/DANFSe/"]');
            
            if (!linkXML) return acc;

            const situacao  = tr.getAttribute('data-situacao') || '';
            const cancelada = situacao.includes('CANCELADA');

            acc.push({
                href:    linkXML.getAttribute('href'),
                hrefPDF: linkPDF ? linkPDF.getAttribute('href') : null,
                cancelada
            });
            
            return acc;
            
        }, [])'''
    )