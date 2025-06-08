#!/usr/bin/env python3
"""
Diagnoseskript für RAG-Retrieval Probleme
"""
import os
import sys
import logging
import json
from typing import Dict, Any, List, Optional

# Füge das übergeordnete Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(".."))

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_rag_retrieval(
    query_text: str = "Welches sind die 12 Weltanschauungen?",
    expected_doc_id: str = "Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]",
    top_k: int = 20,
    with_filter: bool = False,
    category_filter: Dict[str, str] = {"category": "Realismus"},
    output_dir: str = "results"
):
    """Diagnose-Funktion für RAG-Retrieval Probleme."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    
    # Erstelle den Ausgabeordner, falls er nicht existiert
    os.makedirs(output_dir, exist_ok=True)
    
    # Diagnose-Datei
    diagnose_file = os.path.join(output_dir, "rag_diagnose_ergebnisse.txt")
    
    # Initialisiere Vector-Datenbank
    logger.info("=== Starte RAG-Diagnose ===")
    vector_db.init_pinecone()
    
    try:
        logger.info(f"Abfrage: '{query_text}'")
        logger.info(f"Erwartetes Dokument: '{expected_doc_id}'")
        
        # 1. Test ohne Filter
        logger.info("Test 1: Suche ohne Filter")
        ergebnisse_ohne_filter = rag_service.query(
            query_text=query_text,
            filter=None,
            top_k=top_k
        )
        
        # 2. Test mit Filter
        logger.info("Test 2: Suche mit Kategoriefilter")
        ergebnisse_mit_filter = rag_service.query(
            query_text=query_text,
            filter=category_filter,
            top_k=top_k
        )
        
        # 3. Direkte Suche nach dem erwarteten Dokument (falls möglich)
        logger.info("Test 3: Direkte Suche nach dem erwarteten Dokument")
        try:
            # Diese Implementierung hängt von der konkreten API ab
            # Hier wird angenommen, dass es eine Möglichkeit gibt, direkt nach ID zu suchen
            expected_doc = vector_db.get_document_by_partial_id(expected_doc_id)
            expected_doc_exists = expected_doc is not None
        except Exception as e:
            logger.warning(f"Konnte nicht direkt nach Dokument-ID suchen: {str(e)}")
            expected_doc = None
            expected_doc_exists = "Unbekannt"
        
        # Ergebnisse in Datei schreiben
        with open(diagnose_file, "w", encoding="utf-8") as f:
            f.write(f"# RAG-Diagnose-Ergebnisse\n\n")
            f.write(f"## Abfrage\n'{query_text}'\n\n")
            f.write(f"## Erwartetes Dokument\n'{expected_doc_id}'\n\n")
            
            # Existenz des erwarteten Dokuments
            f.write(f"## Existenz des erwarteten Dokuments\n")
            f.write(f"- Dokument existiert im Index: {expected_doc_exists}\n\n")
            
            if expected_doc:
                f.write("### Metadaten des erwarteten Dokuments\n")
                for key, value in expected_doc.get('metadata', {}).items():
                    f.write(f"- **{key}:** {value}\n")
                f.write("\n")
            
            # Test 1: Ergebnisse ohne Filter
            f.write(f"## Test 1: Suche ohne Filter (Top-{top_k})\n\n")
            
            # Prüfen, ob das erwartete Dokument in den Ergebnissen ist
            found_at_position = None
            for i, ergebnis in enumerate(ergebnisse_ohne_filter):
                metadata = ergebnis.get('metadata', {})
                filename = metadata.get('filename', '')
                if expected_doc_id in filename:
                    found_at_position = i + 1
                    break
            
            if found_at_position:
                f.write(f"✅ Erwartetes Dokument gefunden an Position {found_at_position} von {len(ergebnisse_ohne_filter)}\n\n")
            else:
                f.write(f"❌ Erwartetes Dokument NICHT gefunden in den Top-{top_k} Ergebnissen\n\n")
            
            # Top-5 Ergebnisse ohne Filter
            f.write("### Top-5 Ergebnisse ohne Filter\n\n")
            for i, ergebnis in enumerate(ergebnisse_ohne_filter[:5]):
                f.write(f"#### Ergebnis {i+1}\n\n")
                f.write(f"- **Relevanz:** {ergebnis['score']:.4f}\n")
                
                metadata = ergebnis.get('metadata', {})
                filename = metadata.get('filename', 'Kein Dateiname verfügbar')
                title = metadata.get('title', 'Kein Titel verfügbar')
                category = metadata.get('category', 'Keine Kategorie verfügbar')
                
                f.write(f"- **Dateiname:** {filename}\n")
                f.write(f"- **Titel:** {title}\n")
                f.write(f"- **Kategorie:** {category}\n")
                
                # Hervorheben, wenn es das erwartete Dokument ist
                if expected_doc_id in filename:
                    f.write(f"- **⭐ GESUCHTES DOKUMENT ⭐**\n")
                
                # Textauszug
                textauszug = ergebnis.get('text', '')[:150]
                f.write(f"- **Textauszug:** {textauszug}...\n\n")
            
            # Test 2: Ergebnisse mit Filter
            f.write(f"## Test 2: Suche mit Filter {category_filter} (Top-{top_k})\n\n")
            
            # Prüfen, ob das erwartete Dokument in den Ergebnissen ist
            found_at_position = None
            for i, ergebnis in enumerate(ergebnisse_mit_filter):
                metadata = ergebnis.get('metadata', {})
                filename = metadata.get('filename', '')
                if expected_doc_id in filename:
                    found_at_position = i + 1
                    break
            
            if found_at_position:
                f.write(f"✅ Erwartetes Dokument gefunden an Position {found_at_position} von {len(ergebnisse_mit_filter)}\n\n")
            else:
                f.write(f"❌ Erwartetes Dokument NICHT gefunden in den Top-{top_k} Ergebnissen\n\n")
            
            # Top-5 Ergebnisse mit Filter
            f.write("### Top-5 Ergebnisse mit Filter\n\n")
            for i, ergebnis in enumerate(ergebnisse_mit_filter[:5]):
                f.write(f"#### Ergebnis {i+1}\n\n")
                f.write(f"- **Relevanz:** {ergebnis['score']:.4f}\n")
                
                metadata = ergebnis.get('metadata', {})
                filename = metadata.get('filename', 'Kein Dateiname verfügbar')
                title = metadata.get('title', 'Kein Titel verfügbar')
                category = metadata.get('category', 'Keine Kategorie verfügbar')
                
                f.write(f"- **Dateiname:** {filename}\n")
                f.write(f"- **Titel:** {title}\n")
                f.write(f"- **Kategorie:** {category}\n")
                
                # Hervorheben, wenn es das erwartete Dokument ist
                if expected_doc_id in filename:
                    f.write(f"- **⭐ GESUCHTES DOKUMENT ⭐**\n")
                
                # Textauszug
                textauszug = ergebnis.get('text', '')[:150]
                f.write(f"- **Textauszug:** {textauszug}...\n\n")
            
            # Schlussfolgerungen
            f.write("## Diagnose-Schlussfolgerungen\n\n")
            
            if not expected_doc_exists or expected_doc_exists == "Unbekannt":
                f.write("- Es konnte nicht festgestellt werden, ob das erwartete Dokument im Index existiert.\n")
            
            if expected_doc:
                category = expected_doc.get('metadata', {}).get('category', None)
                if category != "Realismus":
                    f.write(f"- Das erwartete Dokument hat die Kategorie '{category}', nicht 'Realismus', was den Filter-Effekt erklärt.\n")
            
            if found_at_position and found_at_position > 5:
                f.write(f"- Das erwartete Dokument wurde gefunden, aber erst an Position {found_at_position}. Der Top-K Wert im Produktionscode ist möglicherweise zu niedrig.\n")
            
            if not found_at_position:
                f.write("- Das erwartete Dokument wurde in keiner der Suchen gefunden. Mögliche Gründe:\n")
                f.write("  - Dokument ist nicht im Index\n")
                f.write("  - Die Embedding-Qualität ist suboptimal\n")
                f.write("  - Die Chunks könnten ungünstig geschnitten sein\n")
                f.write("  - Die Abfrage müsste anders formuliert werden\n")
        
        logger.info(f"Diagnose-Ergebnisse wurden in '{diagnose_file}' gespeichert.")
        return True
        
    except Exception as e:
        logger.error(f"Diagnose fehlgeschlagen: {str(e)}")
        return False

def diagnose_with_alternative_queries(output_dir: str = "results"):
    """Führt die Diagnose mit alternativen Abfrage-Formulierungen durch."""
    alternative_queries = [
        "Welches sind die 12 Weltanschauungen?",
        "Die zwölf Weltanschauungen nach Rudolf Steiner",
        "12 Weltanschauungen Materialismus Idealismus Spiritualismus",
        "Grundlegende Weltanschauungen in der Anthroposophie",
        "Was sind die verschiedenen Weltanschauungen?"
    ]
    
    for i, query in enumerate(alternative_queries):
        logger.info(f"Teste alternative Abfrage {i+1}: '{query}'")
        diagnose_rag_retrieval(query_text=query, output_dir=output_dir)

if __name__ == "__main__":
    erfolg = diagnose_rag_retrieval()
    
    # Wenn gewünscht, alternative Abfragen testen
    # diagnose_with_alternative_queries()
    
    exit(0 if erfolg else 1) 