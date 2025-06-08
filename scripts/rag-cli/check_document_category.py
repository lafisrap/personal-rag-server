#!/usr/bin/env python3
"""
Skript zur Überprüfung der Kategorie-Metadaten des gesuchten Dokuments
"""
import os
import sys
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add the project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from app.services.rag_service import rag_service
from app.db.vector_db import vector_db
from app.core.config import settings

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_document_category(
    expected_doc_id: str = "Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]",
    expected_category: str = "Realismus",
    output_dir: str = "results"
):
    """Überprüfe, ob das gesuchte Dokument die erwartete Kategorie hat."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "kategorie_pruefung.txt")
    
    # Zeitstempel für die Ausgabe
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info("=== Starte Kategorie-Überprüfung ===")
    
    try:
        # Connect to vector store
        if not vector_db.initialized:
            vector_db.init_pinecone()
        
        logger.info(f"Suche nach Dokument: '{expected_doc_id}'")
        logger.info(f"Erwartete Kategorie: '{expected_category}'")
        
        # Handle .txt extension - try both with and without .txt
        document_id_with_txt = expected_doc_id
        if not expected_doc_id.endswith('.txt'):
            document_id_with_txt = expected_doc_id + '.txt'
        document_id_without_txt = expected_doc_id
        if expected_doc_id.endswith('.txt'):
            document_id_without_txt = expected_doc_id[:-4]
        
        # METHODE 1: Semantische Suche nach dem Dokument
        search_query = expected_doc_id.replace("#", " ")  # Convert ID to search terms
        results_unfiltered = rag_service.query(
            query_text=search_query,
            filter=None,
            top_k=20
        )
        
        # Extract documents that match our target
        matching_docs = []
        for item in results_unfiltered:
            metadata = item.get('metadata', {})
            filename = metadata.get('filename', '')
            if expected_doc_id in filename or document_id_with_txt in filename or document_id_without_txt in filename:
                matching_docs.append(item)
                
        # METHODE 2: Umfassende Suche über alle Dokumente
        if not matching_docs:
            try:
                # Get the total number of vectors
                stats = vector_db.index.describe_index_stats()
                total_vectors = stats.get('total_vector_count', 0)
                
                if total_vectors > 0:
                    # Sample query vector (since we need one for the query)
                    sample_vector = rag_service.embedding_service.get_embeddings("sample query for comprehensive search").tolist()
                    
                    # Fetch vectors in batches
                    batch_size = 1000
                    for i in range(0, min(10000, total_vectors), batch_size):
                        query_result = vector_db.index.query(
                            vector=sample_vector,
                            top_k=batch_size,
                            include_values=False,
                            include_metadata=True,
                            offset=i
                        )
                        
                        # Check each result for our document ID
                        for match in query_result.matches:
                            metadata = match.metadata
                            filename = metadata.get('filename', '')
                            if expected_doc_id in filename or document_id_with_txt in filename or document_id_without_txt in filename:
                                matching_docs.append({
                                    "id": match.id,
                                    "score": 0,  # Placeholder
                                    "text": metadata.get("text", ""),
                                    "metadata": {k: v for k, v in metadata.items() if k != "text"}
                                })
            except Exception as e:
                logger.error(f"Umfassende Suche fehlgeschlagen: {str(e)}")
        
        # Ergebnisse in Datei schreiben
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"# Kategorie-Überprüfung - {timestamp}\n\n")
            f.write("## Gesuchtes Dokument\n")
            f.write(f"'{expected_doc_id}'\n\n")
            f.write("## Erwartete Kategorie\n")
            f.write(f"'{expected_category}'\n\n")
            
            if matching_docs:
                kategorien = {}
                for doc in matching_docs:
                    metadata = doc.get('metadata', {})
                    category = metadata.get('category', 'Unbekannt')
                    
                    # Handle multiple categories (comma-separated)
                    if isinstance(category, str) and ',' in category:
                        for cat in category.split(','):
                            cat = cat.strip()
                            kategorien[cat] = kategorien.get(cat, 0) + 1
                    else:
                        kategorien[category] = kategorien.get(category, 0) + 1
                
                # Dokumentinformationen
                f.write("## Dokumentinformationen\n")
                f.write(f"- **Gefundene Chunks:** {len(matching_docs)}\n")
                f.write(f"- **Kategorien:** {', '.join(kategorien.keys())}\n\n")
                
                # Kategorie-Check
                if expected_category in kategorien:
                    f.write(f"✅ **Das Dokument hat die erwartete Kategorie '{expected_category}'**\n\n")
                else:
                    f.write(f"❌ **Das Dokument hat NICHT die erwartete Kategorie '{expected_category}'**\n\n")
                    f.write(f"Stattdessen hat es folgende Kategorie(n): {', '.join(kategorien.keys())}\n\n")
                
                # Metadaten des ersten Chunks
                first_doc = matching_docs[0]
                f.write("## Metadaten (erster Chunk)\n")
                for key, value in first_doc.get('metadata', {}).items():
                    f.write(f"- **{key}:** {value}\n")
                
                # Handlungsempfehlungen
                f.write("\n## Empfehlungen\n")
                if expected_category not in kategorien:
                    f.write(f"1. Entweder den Filter ändern, um die tatsächlichen Kategorien einzuschließen: {', '.join(kategorien.keys())}\n")
                    f.write(f"2. Oder die Metadaten des Dokuments aktualisieren, um die Kategorie '{expected_category}' hinzuzufügen\n")
                elif len(kategorien) > 1:
                    f.write(f"1. Sicherstellen, dass alle Chunks des Dokuments konsistent kategorisiert sind\n")
                    f.write(f"2. Eventuell den Filter erweitern, um alle vorhandenen Kategorien einzuschließen\n")
            else:
                f.write("❌ **Dokument wurde NICHT im Index gefunden!**\n")
                f.write("\n## Mögliche Gründe\n")
                f.write("1. Das Dokument wurde nie hochgeladen\n")
                f.write("2. Das Dokument wurde gelöscht\n")
                f.write("3. Der Dokument-ID ist nicht korrekt\n")
                f.write("\n## Suchparameter\n")
                f.write(f"- Gesuchte ID: '{expected_doc_id}'\n")
                f.write(f"- Mit .txt: '{document_id_with_txt}'\n")
                f.write(f"- Ohne .txt: '{document_id_without_txt}'\n")
                f.write(f"- Suchbegriff: '{search_query}'\n")
        
        # Zusammenfassung im Log
        if matching_docs:
            kategorien = set()
            for doc in matching_docs:
                metadata = doc.get('metadata', {})
                cat = metadata.get('category', 'Nicht angegeben')
                if isinstance(cat, str) and ',' in cat:
                    for c in cat.split(','):
                        kategorien.add(c.strip())
                else:
                    kategorien.add(cat)
            
            logger.info(f"Dokument gefunden mit {len(matching_docs)} Chunks")
            logger.info(f"Gefundene Kategorien: {', '.join(kategorien)}")
            
            if expected_category in kategorien:
                logger.info(f"Die erwartete Kategorie '{expected_category}' ist vorhanden")
            else:
                logger.info(f"Die erwartete Kategorie '{expected_category}' ist NICHT vorhanden")
        else:
            logger.info("Dokument wurde nicht im Index gefunden")
        
        logger.info(f"Ergebnisse wurden in '{log_file}' gespeichert.")
        return len(matching_docs) > 0
        
    except Exception as e:
        logger.error(f"Überprüfung fehlgeschlagen: {str(e)}")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"# Fehler bei der Kategorie-Überprüfung - {timestamp}\n\n")
            f.write(f"Fehler: {str(e)}\n")
        return False

if __name__ == "__main__":
    erfolg = check_document_category()
    exit(0 if erfolg else 1) 