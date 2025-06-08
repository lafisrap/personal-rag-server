#!/usr/bin/env python3
"""
Test-Script, das die RAG-Abfrage ohne Filter durchführt und nach dem erwarteten Dokument sucht
"""
import os
import sys
import logging
from typing import Dict, Any, List
from datetime import datetime

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_without_filter(
    query_text: str = "Welches sind die 12 Weltanschauungen?", 
    expected_doc: str = "Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]",
    top_k: int = 30,
    output_dir: str = "results"  # relativer Pfad
):
    """Test ausführen ohne Filter und nach dem erwarteten Dokument suchen."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    
    # Erstelle den Ausgabeordner, falls er nicht existiert
    os.makedirs(output_dir, exist_ok=True)
    
    # Speicherpfad für die Logs
    log_file = os.path.join(output_dir, "ergebnisse_ohne_filter.txt")
    
    # Initialisiere Vector-Datenbank
    logger.info("=== Starte RAG-Test ohne Filter ===")
    vector_db.init_pinecone()
    
    try:
        logger.info(f"Abfrage: '{query_text}'")
        logger.info(f"Suche nach Dokument: '{expected_doc}'")
        logger.info(f"Top-K: {top_k}")
        
        # Führe die Abfrage ohne Filter aus
        ergebnisse = rag_service.query(
            query_text=query_text,
            filter=None,  # Kein Filter
            top_k=top_k
        )
        
        # Output-Datei vorbereiten und Ergebnisse speichern
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"# RAG-Ergebnisse ohne Filter - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Abfrage: '{query_text}'\n")
            f.write(f"## Top-K: {top_k}\n")
            f.write(f"## Erwartetes Dokument: '{expected_doc}'\n\n")
            
            # Prüfen, ob das erwartete Dokument in den Ergebnissen ist
            expected_doc_found = False
            expected_doc_position = None
            expected_doc_score = None
            
            for i, ergebnis in enumerate(ergebnisse):
                metadata = ergebnis.get('metadata', {})
                filename = metadata.get('filename', '')
                if expected_doc in filename:
                    expected_doc_found = True
                    expected_doc_position = i + 1
                    expected_doc_score = ergebnis['score']
                    break
            
            # Status des erwarteten Dokuments
            f.write("## Status des erwarteten Dokuments\n\n")
            if expected_doc_found:
                f.write(f"✅ **Das erwartete Dokument wurde gefunden!**\n")
                f.write(f"- Position: {expected_doc_position} von {len(ergebnisse)}\n")
                f.write(f"- Relevanz-Score: {expected_doc_score:.4f}\n\n")
            else:
                f.write(f"❌ **Das erwartete Dokument wurde NICHT gefunden in den Top-{top_k} Ergebnissen.**\n\n")
            
            # Alle Ergebnisse auflisten
            f.write("## Alle gefundenen Dokumente\n\n")
            
            for i, ergebnis in enumerate(ergebnisse):
                # Markierung, wenn es das erwartete Dokument ist
                if expected_doc_found and i == expected_doc_position - 1:
                    f.write(f"### ⭐ Dokument {i+1} (GESUCHTES DOKUMENT) ⭐\n\n")
                else:
                    f.write(f"### Dokument {i+1}\n\n")
                
                f.write(f"- **Relevanz:** {ergebnis['score']:.4f}\n")
                
                # Metadaten extrahieren
                metadaten = ergebnis.get('metadata', {})
                
                # Titel
                titel = metadaten.get('title', 'Kein Titel verfügbar')
                f.write(f"- **Titel:** {titel}\n")
                
                # Autor
                autor = metadaten.get('author', 'Kein Autor verfügbar')
                f.write(f"- **Autor:** {autor}\n")
                
                # Dateiname
                dateiname = metadaten.get('filename', 'Kein Dateiname verfügbar')
                f.write(f"- **Dateiname:** {dateiname}\n")
                
                # Dokument-ID
                dokument_id = metadaten.get('document_id', 'Keine ID verfügbar')
                f.write(f"- **Dokument-ID:** {dokument_id}\n")
                
                # Kategorie
                kategorie = metadaten.get('category', 'Keine Kategorie verfügbar')
                f.write(f"- **Kategorie:** {kategorie}\n")
                
                # Chunk-Index
                chunk_index = metadaten.get('chunk_index', 'Kein Chunk-Index verfügbar')
                f.write(f"- **Chunk-Index:** {chunk_index}\n")
                
                # Textauszug
                textauszug = ergebnis.get('text', '')[:300]  # Längerer Ausschnitt
                f.write(f"- **Textauszug:** {textauszug}...\n\n")
                
                # Trennlinie
                if i < len(ergebnisse) - 1:
                    f.write("---\n\n")
        
        logger.info(f"Ergebnisse wurden in '{log_file}' gespeichert.")
        
        if expected_doc_found:
            logger.info(f"Das gesuchte Dokument wurde an Position {expected_doc_position} von {len(ergebnisse)} gefunden.")
            logger.info(f"Relevanz-Score: {expected_doc_score:.4f}")
        else:
            logger.info(f"Das gesuchte Dokument wurde NICHT in den Top-{top_k} Ergebnissen gefunden.")
        
        return expected_doc_found
        
    except Exception as e:
        logger.error(f"Test fehlgeschlagen: {str(e)}")
        return False

if __name__ == "__main__":
    # Verarbeite Kommandozeilenargumente, wenn vorhanden
    if len(sys.argv) > 1:
        query = sys.argv[1]
        erfolg = run_test_without_filter(query_text=query)
    else:
        # Standardabfrage
        erfolg = run_test_without_filter()
    
    exit(0 if erfolg else 1) 