import csv
import sys
import os
import argparse

def converti_popolarita(valore):
    if valore is None:
        return None
    
    VALORESTRINGA = str(valore).strip()
    if VALORESTRINGA == "":
        return None
    
    try:
        NUMFLO = float(VALORESTRINGA)
        NUMINT = int(NUMFLO)
        
        if NUMINT < 0 or NUMINT > 100:
            return None
            
        return NUMINT
    except ValueError:
        return None

def report_qualita(totali, valide, vuote, sbagliate):
    print("\n=== REPORT QUALITÀ DATI ===")
    print(f"Righe totali analizzate:   {totali}")
    print(f"Righe VALIDE (buone):      {valide}")
    print(f"Righe con dato mancante:   {vuote}")
    print(f"Righe con dato sbagliato:  {sbagliate}")
    
    somma_controllo = valide + vuote + sbagliate
    print(f"Somma di controllo:        {somma_controllo}")
    if somma_controllo == totali:
        print("-> Verification superata: I conti tornano perfettamente.")
    else:
        print("ATTENZIONE: I conti non tornano!")
    print("===========================\n")

def controlla_integrita_csv(percorso, max_righe_controllo=50, tolleranza_errori=0.10):
    try:
        with open(percorso, mode='r', encoding='utf-8') as f:
            prima_linea = f.readline().rstrip('\n\r').rstrip(';')
            header = next(csv.reader([prima_linea], delimiter=','))
            num_colonne_attese = len(header)
            
            righe_controllate = 0
            righe_fallite = 0
            
            linee_pulite = (linea.rstrip('\n\r').rstrip(';') for linea in f)
            lettore = csv.reader(linee_pulite, delimiter=',')
            
            for riga in lettore:
                if not riga:
                    continue
                righe_controllate += 1
                
                if len(riga) != num_colonne_attese:
                     righe_fallite += 1
                
                if righe_controllate >= max_righe_controllo:
                    break
            
            if righe_controllate == 0:
                return True
                
            percentuale_errore = righe_fallite / righe_controllate
            if percentuale_errore > tolleranza_errori:
                print(f"\n[ATTENZIONE CRITICA] Il file sembra malformato!")
                print(f"Su {righe_controllate} righe campionate, {righe_fallite} hanno un numero errato di colonne ({percentuale_errore:.1%}).")
                return False
            return True
    except Exception as e:
        print(f"Errore durante il controllo preliminare di integrità: {e}")
        return False

def leggi_brani(percorso):
    TOTALIRIGHE = 0
    BUONE = 0
    VUOTE = 0
    SBAGLIATE = 0
    BRANI = []

    try:
        with open(percorso, mode='r', encoding='utf-8') as f:
            PULITE = (linea.rstrip('\n\r').rstrip(';') for linea in f)
            LETTORE = csv.DictReader(PULITE, delimiter=',')
            
            if LETTORE.fieldnames:
                LETTORE.fieldnames = [f.strip() for f in LETTORE.fieldnames]
            
            colonne = LETTORE.fieldnames or []
            colonna_genere = None
            for col in colonne:
                if 'genre' in col.lower():
                    colonna_genere = col
                    break

            for riga in LETTORE:
                if not riga or all(v == '' for v in riga.values()):
                    continue
                
                TOTALIRIGHE += 1
                
                genere_grezzo = riga.get(colonna_genere) if colonna_genere else ""
                if genere_grezzo and genere_grezzo.strip():
                    riga['track_genre'] = genere_grezzo.split(';')[0].replace('"', '').strip()
                else:
                    riga['track_genre'] = "Sconosciuto"

                valore_pop = riga.get('popularity') or riga.get('popularity ')
                
                if valore_pop is None or str(valore_pop).strip() == "":
                    VUOTE += 1
                    riga['popularity'] = None
                    BRANI.append(riga)
                else:
                    risultato = converti_popolarita(valore_pop)
                    if risultato is not None:
                        BUONE += 1    
                        riga['popularity'] = risultato
                        BRANI.append(riga)
                    else:
                        SBAGLIATE += 1
                        riga['popularity'] = None
                        BRANI.append(riga)
                        
    except FileNotFoundError:
        print(f"Errore critico: Il file '{percorso}' non è stato trovato.")
        sys.exit(1)

    return BRANI, TOTALIRIGHE, BUONE, VUOTE, SBAGLIATE

def estrai_artisti(artisti_greggi):
    """Spezza la stringa degli artisti se contengono il punto e virgola."""
    artisti_greggi = artists_greggi = artisti_greggi.replace('"', '').strip()
    if ";" in artisti_greggi:
        return [a.strip() for a in artisti_greggi.split(";") if a.strip()]
    elif artisti_greggi:
        return [artisti_greggi]
    else:
        return ["Sconosciuto"]

def ottieni_brani_unici(brani):
    """
    Ritorna una lista di brani unici basata sulla chiave (stringa_completa_artisti, titolo).
    Questo garantisce consistenza, previene i duplicati cross-genere e
    preserva i brani in collaborazione (featuring) ed i duetti.
    """
    unici = {}
    for b in brani:
        titolo = (b.get("track_name") or b.get("track_title") or "").replace('"', '').strip()
        # STRADA ACCURATA: Usiamo l'intera stringa degli artisti normalizzata per differenziare i duetti
        artisti_completi = (b.get("artists") or b.get("artist") or "").replace('"', '').strip()
        
        if not titolo:
            continue
            
        chiave = (artisti_completi.lower(), titolo.lower())
        if chiave not in unici:
            unici[chiave] = b
            
    # CORREZIONE: Rimosso completamente l'operatore walrus 'uniques :=' superfluo
    return list(unici.values())

def esegui_analisi_artisti(brani, limite_top):
    print(f"--- ANALISI 1: CLASSIFICA TOP {limite_top} ARTISTI (BRANI DISTINTI) ---")
    mappa_set_brani = {}
    
    for brano in brani:
        titolo = (brano.get("track_name") or brano.get("track_title") or "").replace('"', '').strip()
        artisti_lista = estrai_artisti(brano.get("artists") or brano.get("artist") or "")
        
        if not titolo:
            continue
            
        for artista in artisti_lista:
            if artista not in mappa_set_brani:
                mappa_set_brani[artista] = set()
            mappa_set_brani[artista].add(titolo.lower()) # case-insensitive

    conteggio_brani = {art: len(titoli) for art, titoli in mappa_set_brani.items()}
    top_artisti = sorted(conteggio_brani.items(), key=lambda x: x[1], reverse=True)[:limite_top]
    
    print(f"Classifica basata su un totale di {len(brani)} brani de-duplicati all'origine:\n")
    for i, (artista, num) in enumerate(top_artisti, 1):
        print(f"  {i}. {artista} -> {num} brani distinti")

def esegui_analisi_generi(brani):
    print("--- ANALISI 2: POPOLARITÀ MEDIA PER GENERE ---")
    
    generi_dati = {}
    esclusi_zero = 0
    
    for brano in brani:
        genere = brano.get("track_genre") or "Sconosciuto"
        pop = brano.get("popularity")
        
        if pop is None:
            continue
        if pop == 0:
            esclusi_zero += 1
            continue
            
        if genere not in generi_dati:
            generi_dati[genere] = []
        generi_dati[genere].append(pop)
        
    print(f"Nota di contesto: Sono stati esclusi dal calcolo {esclusi_zero} brani con popolarità pari a 0.\n")
    
    medie_genere = []
    for genere, lista_pop in generi_dati.items():
        media = sum(lista_pop) / len(lista_pop)
        medie_genere.append((genere, media, len(lista_pop)))
        
    medie_genere = sorted(medie_genere, key=lambda x: x[1], reverse=True)
    
    for gen, media, n_brani in medie_genere:
        print(f"  - {gen}: Media Popolarità {media:.2f} (calcolata su {n_brani} brani reali)")

def esegui_analisi_prevalente(brani, artista_cercato):
    print(f"--- ANALISI 3: GENERE PREVALENTE PER ARTISTA ---")
    if not artista_cercato:
        print("Errore: Per questa analisi devi specificare un artista usando il comando --artista \"Nome Artista\"")
        return

    artista_cercato_l = artista_cercato.strip().lower()
    conteggio_generi = {}
    totale_brani_artista = 0
    artista_reale_case = None

    for brano in brani:
        artisti_lista = estrai_artisti(brano.get("artists") or brano.get("artist") or "")
        genere = brano.get("track_genre") or "Sconosciuto"
        
        # Cerca se l'artista fa parte del brano corrente
        match = False
        for art in artisti_lista:
            if art.lower() == artista_cercato_l:
                match = True
                artista_reale_case = art
                break
                
        if match:
            totale_brani_artista += 1
            conteggio_generi[genere] = conteggio_generi.get(genere, 0) + 1

    if totale_brani_artista == 0:
        print(f"Risultato: Artista '{artista_cercato}' non trovato nel file.")
    else:
        genere_top = max(conteggio_generi, key=conteggio_generi.get)
        brani_genere_top = conteggio_generi[genere_top]
        print(f"Artista trovato: {artista_reale_case}")
        print(f"Genere Prevalente: '{genere_top}'")
        print(f"Contesto: Questo genere appare in {brani_genere_top} brani su un totale di {totale_brani_artista} brani distinti dell'artista.")

def main():
    parser = argparse.ArgumentParser(description="Strumento professionale di analisi dataset musicali CSV.")
    parser.add_argument("file_input", nargs="?", default="dataset.csv", help="Percorso del file CSV da analizzare (default: dataset.csv)")
    parser.add_argument("--top", type=int, default=10, help="Numero di artisti da mostrare (default: 10)")
    parser.add_argument("--analisi", choices=["artisti", "generi", "prevalente"], help="Scegli l'analisi da eseguire: artisti, generi, prevalente")
    parser.add_argument("--artista", type=str, help="Nome dell'artista per l'analisi del genere prevalente")
    
    args = parser.parse_args()
    percorso_file = args.file_input
    limite_top = args.top

    if not os.path.exists(percorso_file):
        print(f"Errore: Il file '{percorso_file}' non esiste nella cartella corrente.")
        sys.exit(1)
        
    if not controlla_integrita_csv(percorso_file):
        scelta = input("Il file potrebbe essere corrotto. Vuoi procedere comunque? (s/n): ").strip().lower()
        if scelta != 's':
            print("Analisi interrotta.")
            sys.exit(1)
    
    # 1. Caricamento dati grezzi
    elenco_brani_grezzi, tot, val, vuo, sbag = leggi_brani(percorso_file)
    if not elenco_brani_grezzi:
        print("Nessun brano estratto.")
        return

    # Mostra sempre il report qualità iniziale per garantire l'onestà del dato
    report_qualita(tot, val, vuo, sbag)

    # 4. TRATTAMENTO DATI: Otteniamo la lista coerente dei brani de-duplicati all'origine
    brani_puliti = ottieni_brani_unici(elenco_brani_grezzi)

    # 2. Controllo flusso basato sul comando scelto dall'utente
    if not args.analisi:
        print("Benvenuto nello strumento di analisi. Specifica un'analisi da eseguire con il comando --analisi.")
        print("Esempi:")
        print("   python \"PROGETTO FINALE1.py\" dataset.csv --analisi artisti")
        print("   python \"PROGETTO FINALE1.py\" dataset.csv --analisi generi")
        print("   python \"PROGETTO FINALE1.py\" dataset.csv --analisi prevalente --artista \"Bad Bunny\"")
        return

    if args.analisi == "artisti":
        esegui_analisi_artisti(brani_puliti, limite_top)
    elif args.analisi == "generi":
        esegui_analisi_generi(brani_puliti)
    elif args.analisi == "prevalente":
        esegui_analisi_prevalente(brani_puliti, args.artista)

if __name__ == "__main__":
    main()