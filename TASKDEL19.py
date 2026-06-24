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

# --- TASK 3: CONTROLLO INTEGRITÀ CSV ---
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
                if not riga:  # Salta righe vuote
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
            
            for riga in LETTORE:
                if not riga or all(v == '' for v in riga.values()):
                    continue
                
                TOTALIRIGHE += 1
                valore_pop = riga.get('popularity') or riga.get('popularity ')
                
                if valore_pop is None or str(valore_pop).strip() == "":
                    VUOTE += 1
                else:
                    risultato = converti_popolarita(valore_pop)
                    if risultato is not None:
                        BUONE += 1    
                        riga['popularity'] = risultato
                        BRANI.append(riga)
                    else:
                        SBAGLIATE += 1
                        
    except FileNotFoundError:
        print(f"Errore critico: Il file '{percorso}' non è stato trovato.")
        sys.exit(1)

    return BRANI, TOTALIRIGHE, BUONE, VUOTE, SBAGLIATE

def conta_per_genere(brani):
    conteggi = {}
    for brano in brani:
        genere_greggio = brano.get("track_genre") or "Sconosciuto"
        genere = genere_greggio.strip(";").replace('"', '').strip()
        
        if not genere:
            genere = "Sconosciuto"
            
        conteggi[genere] = conteggi.get(genere, 0) + 1
    return conteggi

def analizza_artisti_e_generi(brani):
    conteggio_brani_artista = {}
    generi_per_artista = {}
    righe_artisti_multipli = 0

    for brano in brani:
        artisti_greggi = brano.get("artists") or brano.get("artist") or ""
        artisti_greggi = artisti_greggi.replace('"', '').strip()
        genere = brano.get("track_genre") or "Sconosciuto"
        
        if ";" in artisti_greggi:
            righe_artisti_multipli += 1
            lista_artisti = [a.strip() for a in artisti_greggi.split(";") if a.strip()]
        else:
            lista_artisti = [artisti_greggi.strip()] if artisti_greggi.strip() else ["Sconosciuto"]

        for artista in lista_artisti:
            conteggio_brani_artista[artista] = conteggio_brani_artista.get(artista, 0) + 1
            
            if artista not in generi_per_artista:
                generi_per_artista[artista] = {}
            generi_per_artista[artista][genere] = generi_per_artista[artista].get(genere, 0) + 1

    return conteggio_brani_artista, generi_per_artista, righe_artisti_multipli

def main():
    parser = argparse.ArgumentParser(description="Strumento di analisi dataset musicali CSV.")
    parser.add_argument("file_input", help="Percorso del file CSV da analizzare")
    parser.add_argument("--top", type=int, default=10, help="Numero di artisti da mostrare (default: 10)")
    
    args = parser.parse_args()
    percorso_file = args.file_input
    limite_top = args.top

    print(f"Avvio analisi del dataset: '{percorso_file}'...")
    
    if not controlla_integrita_csv(percorso_file):
        scelta = input("Il file potrebbe essere corrotto. Vuoi procedere comunque? (s/n): ").strip().lower()
        if scelta != 's':
            print("Analisi interrotta dall'utente.")
            sys.exit(1)
    
    elenco_brani, tot, val, vuo, sbag = leggi_brani(percorso_file)
    
    if not elenco_brani:
        print("Nessun brano valido estratto. Verificare la struttura del file.")
        return

    report_qualita(tot, val, vuo, sbag)
    
    conteggi_genere = conta_per_genere(elenco_brani)
    generi_ordinati = sorted(conteggi_genere.items(), key=lambda x: x[1], reverse=True)
    print(f"\n[TASK 3] Primi 5 generi per numero di brani:")
    for gen, num in generi_ordinati[:5]:
        print(f"  - {gen}: {num} brani")

    contatore_artisti, mappa_generi, righe_multiple = analizza_artisti_e_generi(elenco_brani)
    
    print(f"\n[TASK 4] Righe totali con artisti multipli (;): {righe_multiple}")
    
    top_artisti = sorted(contatore_artisti.items(), key=lambda x: x[1], reverse=True)[:limite_top]
    print(f"\n[TASK 4] Top {limite_top} Artisti con più brani (considerando i singoli componenti):")
    for i, (artista, num_brani) in enumerate(top_artisti, 1):
        print(f"  {i}. {artista} ({num_brani} brani)")

    print("\n[TASK 5] Genere prevalente per i primi artisti in classifica:")
    limite_generi = min(5, limite_top)
    top_per_genere = top_artisti[:limite_generi]
    for artista, _ in top_per_genere:
        diz_generi = mappa_generi.get(artista)
        if diz_generi:
            genere_top = max(diz_generi, key=diz_generi.get)
            print(f"  - {artista} -> Genere Prevalente: '{genere_top}' ({diz_generi[genere_top]} brani)")
        else:
            print(f"  - {artista} -> Errore: Dati dell'artista non trovati.")

if __name__ == "__main__":
    main()



#RISPOSTA
#la differenza è che se uno volesse analizzare la top 25 con un numero fisso di cantanti cioè 10 in questo caso dovrebbe modificare il coice mentre se all'utente venisse chiesto quanto vuoi lunga la lista di cantanti e scegliesse lui il numero sarebbe più veloce e pratico per l'esaminazione dei dati.