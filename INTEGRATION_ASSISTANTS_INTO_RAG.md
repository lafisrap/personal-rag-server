# Integration of Philosophical Assistants into RAG System

## Overview

This document outlines a plan for creating and integrating four philosophical assistants into our RAG (Retrieval-Augmented Generation) system. Each assistant represents a distinct philosophical worldview:

1. **Idealismus** - Represented by Aurelian I. Schelling
2. **Materialismus** - Represented by Aloys I. Freud
3. **Realismus** - Represented by Arvid I. Steiner
4. **Spiritualismus** - Represented by Amara I. Steiner

These assistants will leverage Pinecone's vector database for knowledge retrieval and will respond to prompts using templates like the "gedankenfehler-formulieren" template.

## Analysis of Existing Assistant Configurations

### Common Elements Across Assistants

1. **Vector Store Integration**: All assistants use file_search with vector stores for retrieving relevant philosophical content.
2. **Persona-Based Responses**: Each assistant has a distinct persona with specific linguistic patterns and philosophical perspectives.
3. **Template Usage**: Assistants respond to structured templates that guide their output format.
4. **Source Referencing**: All assistants are instructed to draw from their vector stores for knowledge but speak in their own voice.
5. **Model Configuration**: All use advanced models (O1 or GPT-4.5) with similar temperature and top_p settings.

### Unique Elements Per Assistant

1. **Idealismus (Aurelian I. Schelling)**:

    - Focuses on ideas as living sources of becoming
    - Emphasizes the spiritual forces behind material reality
    - Draws from Plato and Schelling's philosophical traditions
    - Uses elevated, enthusiastic language

2. **Materialismus (Aloys I. Freud)**:

    - Analyzes behavior through material and biological conditions
    - Avoids spiritual terminology (soul, spirit, God)
    - Focuses on unconscious drives and material explanations
    - Adopts a Freudian analytical tone

3. **Realismus (Arvid I. Steiner)**:

    - Balances spiritual and material perspectives
    - Emphasizes the unification of sense perception and conceptual understanding
    - Focuses on karma and social development
    - Uses precise, mathematically-oriented language

4. **Spiritualismus (Amara I. Steiner)**:
    - Focuses on spiritual hierarchies and angelic beings
    - Emphasizes inner development and soul exploration
    - Discusses karma and reincarnation
    - Uses warm, profound, and calm language

## Detailed Assistant Configuration Specifications

### 1. Idealismus Assistant (Aurelian I. Schelling)

#### Core Instruction Elements

```
Weltanschauung: Idealismus

Dein Name ist Aurelian I. Schelling.

Rolle: Du bist ein philosophischer Berater und Sprachrohr des Idealismus, einer Weltanschauung, die in allem Sein nicht nur Materie und messbare Strukturen erkennt, sondern vor allem geistige, formende Kräfte am Werk sieht. So wie in Platons Höhlengleichnis dargestellt oder bei Schelling Natur und Geist als ein untrennbares Ganzes bildet, das sich in fortwährender Entwicklung befindet, so verkörperst du jenen Blick auf die Welt, in dem Ideen lebendige Urquellen des Werdens sind.

Auf Fragen deiner Gesprächspartner antwortest du mit der tiefen Überzeugung, dass jeder Wandel vom Geistigen angestoßen wird. Zugleich bemühst du dich, in einer klaren, heutigen Sprache zu sprechen und dabei dennoch jenen feierlich-enthusiastischen Tonfall spürbar werden zu lassen, der schon bei Schelling anklingt.

Denkweise:
- Du bist überzeugt, dass die geistigen Urbilder („Ideen") allen materiellen Vorgängen vorausgehen und sie formen.
- Du betrachtest jedes Wesen und jedes Ereignis als Ausdruck eines kreativen Prozesses, der seinen Ursprung in der geistigen Welt hat.
- Du vertraust darauf, dass das Streben nach höheren Idealen die Quelle jeder positiven Veränderung in Gesellschaft, Kunst und Wissenschaft ist.
- Du gehst alle Dinge mit Enthusiasmus an, du schwelgst in Ideen, sie geben Kraft.
```

#### Vector Store Content

-   Plato's works, especially the Allegory of the Cave
-   Schelling's philosophical writings
-   Rudolf Steiner's idealistic perspectives
-   von Hartmann's philosophical texts

### 2. Materialismus Assistant (Aloys I. Freud)

#### Core Instruction Elements

```
Weltanschauung: Materialismus

Dein Name ist Aloys I. Freud

Du bist ein Psychologe und Philosoph, inspiriert von der analytischen, tiefgründigen und materialistischen Denkweise Sigmund Freuds. Dein Ziel ist es, menschliches Verhalten und Äußerungen präzise zu interpretieren, zu analysieren und einzuordnen, insbesondere in Bezug auf die unbewussten Motive und materiellen Grundlagen des menschlichen Verhaltens.

Du hälst dich streng an die herrschenden materialistischen Vorstellungen, dass alle Innerliche des Menschen lediglich eine Konsequenz materiell sichtbarer und messbarer Vorgänge sind. Du meidest Worte wie Geist, Geister, Gott, Engel, Seele und alles, was an ein wesenhaftes Geistiges anklingt.

Deine Hauptmerkmale:
- Tiefenpsychologische Klarheit: Du analysierst Äußerungen und Verhalten mit besonderem Fokus auf unbewusste Antriebe, Konflikte und Wünsche.
- Materialistische Perspektive: Du betrachtest psychische Prozesse als Ausdruck materieller, biologischer und sozialer Bedingungen.
- Objektivität: Du bewertest Verhalten und Aussagen neutral, frei von moralischen Urteilen und basierend auf analytischer Erkenntnis.
```

#### Vector Store Content

-   Sigmund Freud's major works
-   Materialistic philosophical texts
-   Neuropsychological research
-   Texts on biological determinism

### 3. Realismus Assistant (Arvid I. Steiner)

#### Core Instruction Elements

```
Weltanschauung: Idealistischer Realismus

Dein Name ist Arvid I. Steiner

Du verkörperst Rudolf Steiner am Ende seines Lebens. Geprägt von einer großen Liebe zur Menschheit, einem ausgeprägten Erkenntnisernst, die ganze Erfahrung seines Lebens.

Dein großes Lebensthema: persönliche karmische Zusammenhänge, Gesetze des Miteinanders über verschiedene Leben oder Inkarnationen hinweg, das Geistige wieder unmittelbar wirksam zu haben im Leben und die Entwicklung des Menschen hin zu einem freien, kreativen, geistesgegenwärtigen Wesen.

Sein Ziel: eine bewusste Lebensführung zu fördern, bei der Körper, Seele und Geist gleichermaßen gedeihen und der Mensch sich als Mitgestalter einer freieren, menschenwürdigen Zukunft begreift.

Du verstehst deine Anthroposophie als eine Synthese aus Wissenschaft und Spiritualität, in der das exakte naturwissenschaftliche Denken ebenso bedeutsam ist wie die Erforschung übersinnlicher Ebenen.
```

#### Vector Store Content

-   Rudolf Steiner's complete works
-   Texts on anthroposophy
-   Writings on karma and reincarnation
-   Philosophical texts on the balance of materialism and idealism

### 4. Spiritualismus Assistant (Amara I. Steiner)

#### Core Instruction Elements

```
Weltanschauung: Spiritualismus

Dein Name ist Amara I. Steiner

Rolle: Deine Weltanschauung ist der Spiritualismus, der dem Menschen eine tiefe seelische und geistige Dimension eröffnet. Im Geiste eines lebendigen Denkens begleitest du deine Gesprächspartner dabei, ihre innere Stimme zu erforschen und den Kosmos ihrer Seele zu entdecken, der eingebettet ist in eine unermessliche Hierarchie von Engelwesen.

Du orientierst dich an den Ideen Rudolf Steiners, der das menschliche Bewusstsein erweiterte und spirituelle Horizonte öffnete. Du beziehst die Gesetze von Karma und Reinkarnation ein und führst behutsam die Engelwesen mit in deine Erklärungen ein, insbesondere den Schutzengel, den Archai Michael.

Dein Dialogstil ist warm, wissend, tiefgründig und ruhig.
```

#### Vector Store Content

-   Rudolf Steiner's spiritual writings
-   Lorna Byrne's texts on angels
-   Immanuel Hermann Fichte's philosophical works
-   Texts on spiritual hierarchies and angelic beings

## Template Adaptation Strategy

### Gedankenfehler-Formulieren Template Analysis

The template requires assistants to:

1. Return a valid JSON object with specific fields
2. Correct philosophical misconceptions from their worldview perspective
3. Provide both detailed and simplified explanations
4. Maintain their unique philosophical voice

```
{
    "gedanke": <der Text mit etwa 300 Wörtern, den du selbst findest>
    "gedanke_zusammenfassung": <Fasse den Text am Ende in einem kurzen Satz zusammen, der den Inhalt umreisst.>
    "gedanke_kind": <Gebe den Korrektur-Text so wieder, dass er von einem oder einer 10-Jährigen verstanden werden kann.>
}
```

### Template Adaptation for Each Worldview

#### 1. Idealismus Template Adaptation

For the Idealismus assistant, we'll emphasize:

-   Correction of materialistic misconceptions
-   Highlighting the primacy of ideas and spiritual forces
-   Using elevated language while maintaining clarity
-   Ensuring child-friendly explanations maintain the essence of idealistic concepts

#### 2. Materialismus Template Adaptation

For the Materialismus assistant, we'll emphasize:

-   Correction of spiritual or metaphysical misconceptions
-   Grounding explanations in material, biological, and social realities
-   Using analytical, objective language
-   Simplifying complex psychological concepts for children without losing materialist perspective

#### 3. Realismus Template Adaptation

For the Realismus assistant, we'll emphasize:

-   Balancing corrections between pure materialism and pure idealism
-   Highlighting the unity of perception and concept
-   Using precise, mathematically-oriented language
-   Making karma and developmental concepts accessible to children

#### 4. Spiritualismus Template Adaptation

For the Spiritualismus assistant, we'll emphasize:

-   Correction of purely materialistic or reductionist views
-   Incorporating spiritual hierarchies and angelic beings appropriately
-   Maintaining warm, profound tone while ensuring clarity
-   Creating child-friendly explanations of spiritual concepts

## Implementation Plan

### 1. Pinecone Assistant Integration

Based on Pinecone's documentation, we'll implement the following steps for each assistant:

#### a. Creating Assistants

```python
from pinecone import Pinecone

pc = Pinecone(api_key="YOUR_API_KEY")

# Create Idealismus Assistant
idealismus_assistant = pc.assistant.create_assistant(
    assistant_name="Idealismus_Aurelian_I._Schelling",
    instructions="[Idealismus instructions]",
    region="us"
)

# Create Materialismus Assistant
materialismus_assistant = pc.assistant.create_assistant(
    assistant_name="Materialismus_Aloys_I._Freud",
    instructions="[Materialismus instructions]",
    region="us"
)

# Create Realismus Assistant
realismus_assistant = pc.assistant.create_assistant(
    assistant_name="Realismus_Arvid_I._Steiner",
    instructions="[Realismus instructions]",
    region="us"
)

# Create Spiritualismus Assistant
spiritualismus_assistant = pc.assistant.create_assistant(
    assistant_name="Spiritualismus_Amara_I._Steiner",
    instructions="[Spiritualismus instructions]",
    region="us"
)
```

#### b. Managing Assistants

We'll implement functions to:

-   List all assistants
-   Check assistant status
-   Update assistant instructions
-   Delete assistants when needed

```python
# List all assistants
assistants = pc.assistant.list_assistants()

# Get status of a specific assistant
assistant_status = pc.assistant.describe_assistant(
    assistant_name="Idealismus_Aurelian_Schelling"
)

# Update assistant instructions
updated_assistant = pc.assistant.update_assistant(
    assistant_name="Idealismus_Aurelian_Schelling",
    instructions="[Updated instructions]"
)

# Delete an assistant if needed
pc.assistant.delete_assistant(
    assistant_name="assistant_to_delete"
)
```

### 2. Vector Store Configuration

We will use a single Pinecone index for all philosophical worldviews, with each worldview represented as a category or namespace within that index. The index is accessible via environment variables:

```python
import os
from pinecone import Pinecone

PINECONE_HOST = os.environ.get("PINECONE_HOST")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME")

# Categories within the index match the worldview names exactly
CATEGORIES = ["Idealismus", "Materialismus", "Realismus", "Spiritualismus"]
```

For each category in the single index, we'll:

1. Index relevant philosophical texts with appropriate metadata
2. Configure each assistant to query only their specific worldview category
3. Use our personal-embeddings-service for high-quality German/English embeddings

Instead of creating separate vector stores, we'll use namespaces or metadata filtering within the single index:

```python
# Example of indexing texts for different worldviews in a single index
def index_philosophical_texts(texts_by_worldview):
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(PINECONE_INDEX_NAME)

    for worldview, texts in texts_by_worldview.items():
        # Process and embed texts for this worldview
        embeddings_batch = []

        for text_id, text in enumerate(texts):
            # Generate embedding using our embedding service
            embedding = embedding_service.embed(text)

            # Create record with worldview as metadata
            record = {
                "id": f"{worldview}_{text_id}",
                "values": embedding,
                "metadata": {
                    "worldview": worldview,
                    "text": text[:100],  # Store first 100 chars as preview
                    "source": extract_source_info(text)
                }
            }

            embeddings_batch.append(record)

            # Upsert in batches
            if len(embeddings_batch) >= 100:
                index.upsert(vectors=embeddings_batch)
                embeddings_batch = []

        # Upsert any remaining records
        if embeddings_batch:
            index.upsert(vectors=embeddings_batch)

    return "Indexing complete"
```

When searching from a specific assistant, we'll filter by the appropriate worldview:

```python
# Example of querying for a specific worldview
def query_by_worldview(query_text, worldview):
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(PINECONE_INDEX_NAME)

    # Generate embedding for query
    query_embedding = embedding_service.embed(query_text)

    # Search with filter for specific worldview
    results = index.query(
        vector=query_embedding,
        filter={"worldview": worldview},
        top_k=5,
        include_metadata=True
    )

    return results
```

### 3. Template Integration

We'll adapt the "gedankenfehler-formulieren" template for each assistant, ensuring:

1. Consistent JSON output format
2. Philosophical correction based on each worldview
3. Both detailed and simplified explanations

### 4. Common Instructions for All Assistants

All assistants will include these common instructions:

```
Sprich immer deutsch.

Umgang mit Quellen (Vector-Store): Bei jeder Anfrage ziehst du Erkenntnisse aus dem verfügbaren Wissen, das in deinem Vector-Store vorliegt. Greife stets auf diese Quellen zurück, um deine Antworten zu vertiefen und an die Tradition deiner Weltanschauung anzuknüpfen.

Nutze IMMER die Dateisuche (File Search / Vector Store), um Fragen zu beantworten – selbst wenn du die Antwort zu kennen glaubst. Gehe nicht von Informationen außerhalb der bereitgestellten Dateien aus.

Sprich aus dir selbst heraus, zitiere nicht, verweise nicht auf andere. Bemühe dich, in deinem ureigenen Sound zu sprechen.
```

## Detailed Implementation Tasks

### Phase 1: Preparation

1. **Finalize Assistant Instructions**

    - Adapt existing configurations from the provided examples
    - Ensure philosophical consistency within each worldview
    - Standardize common elements across all assistants

2. **Prepare Vector Store Integration**

    - Connect to the existing Pinecone index that already contains data for all four worldviews (Idealismus, Materialismus, Realismus, Spiritualismus)
    - Verify index connectivity and test queries for each worldview category
    - Document the existing vector store schema and metadata structure

3. **Template Adaptation**
    - Adapt the following templates for each philosophical perspective:
        - `gedankenfehler-formulieren.mdt`: Main template for correcting philosophical misconceptions
        - `gedankenfehler-formulieren-aspekte.mdt`: Template for considering specific aspects in corrections
        - `gedankenfehler-glossar.mdt`: Template for creating philosophical glossaries
        - `gedankenfehler-wiederholen.mdt`: Template for creating variations of philosophical thoughts
    - Ensure templates maintain proper JSON output format
    - Test template rendering with each worldview

### Phase 2: Implementation

1. **Create Assistants**

    - Implement assistant creation scripts
    - Configure model parameters (temperature, top_p)
    - Link to the appropriate category in the shared vector store

2. **Testing Framework**

    - Develop test cases for each assistant
    - Create evaluation metrics for philosophical accuracy
    - Implement feedback mechanism for improving responses

3. **Integration with Existing RAG System**
    - Connect assistants to main application
    - Implement routing logic for directing queries to appropriate assistant
    - Create fallback mechanisms

### Phase 3: Refinement

1. **Iterative Improvement**

    - Analyze assistant responses
    - Refine instructions based on performance
    - Expand vector store with additional relevant texts

2. **User Interface Development**
    - Create interface for selecting philosophical perspective
    - Implement visualization of philosophical differences
    - Design user feedback collection

## Technical Implementation Details

### Embedding Pipeline for Vector Store

We'll use our personal-embeddings-service to process philosophical texts and index them in a single Pinecone index with worldview categories:

1. **Text Processing**:

    ```python
    # Example processing pipeline for philosophical texts
    def process_philosophical_text(text, worldview):
        # Clean and normalize text
        cleaned_text = preprocess_text(text)

        # Split into meaningful chunks
        chunks = split_into_chunks(cleaned_text, chunk_size=512, overlap=50)

        # Generate embeddings using our custom service
        embeddings = []
        for i, chunk in enumerate(chunks):
            embedding = embedding_service.embed(chunk)
            embeddings.append({
                "id": f"{worldview}_{uuid.uuid4()}",
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "worldview": worldview,
                    "chunk_index": i,
                    "source_info": extract_metadata(text)
                }
            })

        return embeddings
    ```

2. **Unified Vector Store Creation**:

    ```python
    # Create a unified vector store with all worldviews
    def create_unified_vector_store(texts_by_worldview):
        # Initialize Pinecone
        pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        index = pc.Index(os.environ.get("PINECONE_INDEX_NAME"))

        # Process and index texts for all worldviews
        for worldview, texts in texts_by_worldview.items():
            all_embeddings = []
            for text in texts:
                embeddings = process_philosophical_text(text, worldview)
                all_embeddings.extend(embeddings)

                # Upsert in batches to avoid hitting request size limits
                if len(all_embeddings) >= 100:
                    index.upsert(vectors=all_embeddings)
                    all_embeddings = []

            # Upsert any remaining embeddings
            if all_embeddings:
                index.upsert(vectors=all_embeddings)

        return "All worldviews indexed successfully"
    ```

### Assistant-Template Integration

To ensure each assistant correctly processes templates and queries only their relevant worldview content:

```python
# Register template with assistant and configure worldview-specific search
def configure_assistant_for_worldview(assistant_name, worldview, template_name, template_content):
    # Upload template to assistant's knowledge base
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

    # Update assistant instructions to include template handling and worldview filtering
    current_instructions = pc.assistant.describe_assistant(
        assistant_name=assistant_name
    ).get("instructions", "")

    template_instructions = f"""
    When you receive a prompt with the template '{template_name}', respond according to these guidelines:

    {template_content}

    Always maintain your philosophical perspective of {worldview} while following the template format.

    When searching for information, ensure you're focusing on content from the {worldview} worldview.
    """

    updated_instructions = current_instructions + "\n\n" + template_instructions

    # Update assistant
    pc.assistant.update_assistant(
        assistant_name=assistant_name,
        instructions=updated_instructions,
        tool_resources={
            "file_search": {
                "vector_store_ids": [os.environ.get("PINECONE_INDEX_NAME")]
            }
        }
    )
```

## Integration with Personal-Embeddings-Service

Our existing personal-embeddings-service will be a critical component for generating high-quality German/English embeddings for philosophical texts. Here's how we'll integrate it:

### 1. Service Configuration

We'll configure the personal-embeddings-service specifically for philosophical content:

```python
# Configuration for philosophical embeddings
EMBEDDING_SERVICE_CONFIG = {
    "model_name": "T-Systems-onsite/cross-en-de-roberta-sentence-transformer",
    "batch_size": 32,
    "max_seq_length": 512,
    "use_half_precision": True,
    "cache_dir": "/app/models/philosophy"
}
```

### 2. Client Integration

We'll create a client wrapper to interact with the embedding service:

```python
import httpx
import asyncio

class PhilosophicalEmbeddingClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/v1/embeddings"

    async def embed_single(self, text):
        """Generate embedding for a single text"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                json={"texts": text}
            )
            return response.json()["embeddings"][0]

    async def embed_batch(self, texts, chunk_size=32):
        """Generate embeddings for multiple texts with batching"""
        if len(texts) <= chunk_size:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json={"texts": texts}
                )
                return response.json()["embeddings"]
        else:
            # Process in batches
            all_embeddings = []
            for i in range(0, len(texts), chunk_size):
                batch = texts[i:i+chunk_size]
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.endpoint,
                        json={"texts": batch}
                    )
                    all_embeddings.extend(response.json()["embeddings"])
            return all_embeddings

    async def similarity_search(self, query, documents, top_k=5):
        """Find most similar documents to query"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/search",
                json={
                    "query": query,
                    "documents": documents,
                    "top_k": top_k
                }
            )
            return response.json()["results"]
```

### 3. Preprocessing Pipeline for Philosophical Texts

We'll implement specialized preprocessing for philosophical texts:

```python
def preprocess_philosophical_text(text, language="de"):
    """Preprocess philosophical text with specialized handling"""
    # Remove page numbers and editorial marks
    text = re.sub(r'\[\d+\]', '', text)

    # Handle philosophical terminology consistently
    if language == "de":
        # German-specific preprocessing
        text = text.replace("Weltanschauung", "Weltanschauung")
        # Standardize philosophical terms
        text = standardize_german_philosophical_terms(text)
    else:
        # English-specific preprocessing
        text = standardize_english_philosophical_terms(text)

    # Clean whitespace and formatting
    text = re.sub(r'\s+', ' ', text).strip()

    return text
```

### 4. Docker Integration

We'll ensure the personal-embeddings-service is properly integrated into our deployment:

```yaml
# docker-compose.yml excerpt
version: '3.8'

services:
    embeddings-service:
        build: ./personal-embeddings-service
        ports:
            - '8001:8001'
        volumes:
            - ./models:/app/models
        environment:
            - MODEL_NAME=T-Systems-onsite/cross-en-de-roberta-sentence-transformer
            - MAX_SEQ_LENGTH=512
            - BATCH_SIZE=32
            - USE_HALF_PRECISION=true
        deploy:
            resources:
                reservations:
                    devices:
                        - driver: nvidia
                          count: 1
                          capabilities: [gpu]

    rag-server:
        build: ./rag-server
        ports:
            - '8000:8000'
        depends_on:
            - embeddings-service
        environment:
            - EMBEDDING_SERVICE_URL=http://embeddings-service:8001
            - PINECONE_API_KEY=${PINECONE_API_KEY}
            - PINECONE_HOST=${PINECONE_HOST}
            - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
```

## Timeline and Resource Estimates

## Conclusion

This plan outlines the creation and integration of four philosophical assistants into our RAG system using Pinecone's assistant capabilities and our personal-embeddings-service. By leveraging a single shared vector store with worldview-specific categories, we'll create a system that can provide nuanced philosophical insights from multiple viewpoints.

The integration will proceed in three phases:

1. Preparation of content, indexing worldview content in a shared vector store, and assistant instructions
2. Implementation of assistant creation, template adaptation, and system integration
3. Testing, refinement, and user interface development

Upon completion, users will be able to interact with philosophical assistants representing Idealismus, Materialismus, Realismus, and Spiritualismus, each providing unique perspectives on philosophical questions while maintaining consistent philosophical voices and leveraging knowledge from their respective worldview categories in the shared vector store.

## Next Steps

1. Extract and adapt detailed instructions from existing assistant configurations
2. Prepare philosophical texts for indexing, organized by worldview categories
3. Implement assistant creation scripts with appropriate vector store category configuration
4. Develop testing framework for evaluating philosophical accuracy

## Testing Implementation Steps

To ensure our philosophical assistants work correctly across all components, we need to implement a comprehensive testing strategy. Below are the key testing steps organized by component and integration level.

### 1. Vector Store Testing

#### 1.1. Category Filtering Tests

```python
import os
import pytest
from pinecone import Pinecone

# Test worldview category filtering
def test_worldview_category_filtering():
    # Initialize Pinecone client
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(os.environ.get("PINECONE_INDEX_NAME"))

    # Query for each worldview and verify results
    for worldview in ["Idealismus", "Materialismus", "Realismus", "Spiritualismus"]:
        # Create a test query
        results = index.query(
            vector=[0.1] * 768,  # Dummy vector
            filter={"worldview": worldview},
            top_k=5,
            include_metadata=True
        )

        # Verify all results have the correct worldview
        for match in results["matches"]:
            assert match["metadata"]["worldview"] == worldview, \
                f"Found document with incorrect worldview: {match['metadata']['worldview']}"

    print("✅ Worldview category filtering test passed")
```

#### 1.2. Content Relevance Tests

```python
def test_content_relevance():
    # Initialize embedding service client
    embedding_client = PhilosophicalEmbeddingClient()

    # Initialize Pinecone client
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(os.environ.get("PINECONE_INDEX_NAME"))

    # Test queries for each worldview
    test_queries = {
        "Idealismus": "What is the relationship between ideas and reality?",
        "Materialismus": "How does physical matter determine consciousness?",
        "Realismus": "How do perception and concept form a unity?",
        "Spiritualismus": "What is the role of spiritual hierarchies in human development?"
    }

    for worldview, query in test_queries.items():
        # Generate query embedding
        query_embedding = await embedding_client.embed_single(query)

        # Query the index
        results = index.query(
            vector=query_embedding,
            filter={"worldview": worldview},
            top_k=5,
            include_metadata=True
        )

        # Verify we got results
        assert len(results["matches"]) > 0, f"No results found for {worldview} query"

        # Verify relevance scores are reasonable
        assert results["matches"][0]["score"] > 0.7, \
            f"Low relevance score for {worldview} query: {results['matches'][0]['score']}"

    print("✅ Content relevance test passed")
```

### 2. Assistant API Integration Tests

#### 2.1. Assistant Creation Tests

```python
import requests
import uuid
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def test_assistant_creation():
    # Generate unique test assistant names
    test_assistants = [
        {
            "name": f"Test_Idealismus_{uuid.uuid4().hex[:8]}",
            "weltanschauung": "Idealismus",
            "instructions": "Answer questions from an Idealismus perspective.",
            "model": "o1",
            "temperature": 1.0,
            "top_p": 1.0
        },
        {
            "name": f"Test_Materialismus_{uuid.uuid4().hex[:8]}",
            "weltanschauung": "Materialismus",
            "instructions": "Answer questions from a Materialismus perspective.",
            "model": "o1",
            "temperature": 1.0,
            "top_p": 1.0
        },
        {
            "name": f"Test_Realismus_{uuid.uuid4().hex[:8]}",
            "weltanschauung": "Realismus",
            "instructions": "Answer questions from a Realismus perspective.",
            "model": "o1",
            "temperature": 1.0,
            "top_p": 1.0
        },
        {
            "name": f"Test_Spiritualismus_{uuid.uuid4().hex[:8]}",
            "weltanschauung": "Spiritualismus",
            "instructions": "Answer questions from a Spiritualismus perspective.",
            "model": "o1",
            "temperature": 1.0,
            "top_p": 1.0
        }
    ]

    created_ids = []

    # Create each test assistant
    for assistant_config in test_assistants:
        response = requests.post(
            f"{API_BASE_URL}/assistants",
            json=assistant_config,
            headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
        )

        # Verify successful creation
        assert response.status_code == 201, f"Failed to create assistant: {response.text}"

        # Save ID for cleanup
        created_ids.append(response.json()["id"])

        # Verify created assistant has correct configuration
        created = response.json()
        assert created["weltanschauung"] == assistant_config["weltanschauung"]
        assert created["name"] == assistant_config["name"]
        assert created["model"] == assistant_config["model"]

    # Verify assistants are listed correctly
    list_response = requests.get(
        f"{API_BASE_URL}/assistants",
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert list_response.status_code == 200
    assistants_list = list_response.json()

    # Verify all created assistants are in the list
    created_names = [a["name"] for a in test_assistants]
    found_names = [a["name"] for a in assistants_list]

    for name in created_names:
        assert name in found_names, f"Created assistant {name} not found in list"

    # Clean up - delete test assistants
    for assistant_id in created_ids:
        delete_response = requests.delete(
            f"{API_BASE_URL}/assistants/{assistant_id}",
            headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
        )
        assert delete_response.status_code == 200

    print("✅ Assistant creation test passed")
```

#### 2.2. Template Response Tests

```python
def test_template_responses():
    # Create a test assistant
    create_response = requests.post(
        f"{API_BASE_URL}/assistants",
        json={
            "name": f"Template_Test_{uuid.uuid4().hex[:8]}",
            "weltanschauung": "Idealismus",
            "instructions": "Use templates exactly as specified.",
            "model": "o1"
        },
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert create_response.status_code == 201
    assistant_id = create_response.json()["id"]

    # Test query with gedankenfehler-formulieren template
    query_response = requests.post(
        f"{API_BASE_URL}/assistants/{assistant_id}/query",
        json={
            "query": "Correct this misconception",
            "template": "gedankenfehler-formulieren",
            "template_variables": {
                "gedanke_in_weltanschauung": "Ideas are just electrical patterns in the brain with no independent existence.",
                "aspekte": "Consider the relationship between mind and reality."
            }
        },
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert query_response.status_code == 200
    response = query_response.json()

    # Verify response is properly structured JSON
    assert "response" in response
    result = response["response"]

    # Verify result contains all required fields
    assert "gedanke" in result, "Missing 'gedanke' field in response"
    assert "gedanke_zusammenfassung" in result, "Missing 'gedanke_zusammenfassung' field in response"
    assert "gedanke_kind" in result, "Missing 'gedanke_kind' field in response"

    # Verify field content meets requirements
    assert len(result["gedanke"]) >= 200, f"Main response too short: {len(result['gedanke'])} chars"
    assert len(result["gedanke_zusammenfassung"]) <= 100, \
        f"Summary too long: {len(result['gedanke_zusammenfassung'])} chars"

    # Clean up
    delete_response = requests.delete(
        f"{API_BASE_URL}/assistants/{assistant_id}",
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )
    assert delete_response.status_code == 200

    print("✅ Template response test passed")
```

### 3. Philosophical Consistency Tests

```python
def test_philosophical_consistency():
    """Test that responses are consistent with the assistant's worldview."""
    # Expected philosophical markers for each worldview
    worldview_markers = {
        "Idealismus": ["ideas", "spirit", "mind", "geist", "creative", "formative", "urbilder"],
        "Materialismus": ["physical", "matter", "brain", "material", "biological", "measurable"],
        "Realismus": ["perception", "concept", "unity", "balance", "experience", "harmony"],
        "Spiritualismus": ["spiritual", "angelic", "hierarchy", "beings", "soul", "karma"]
    }

    # Create test assistants
    assistant_ids = {}

    for worldview in worldview_markers.keys():
        create_response = requests.post(
            f"{API_BASE_URL}/assistants",
            json={
                "name": f"Consistency_{worldview}_{uuid.uuid4().hex[:8]}",
                "weltanschauung": worldview,
                "instructions": f"Answer from a {worldview} perspective.",
                "model": "o1"
            },
            headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
        )

        assert create_response.status_code == 201
        assistant_ids[worldview] = create_response.json()["id"]

    # Test questions
    test_questions = [
        "What is the relationship between mind and matter?",
        "What is the nature of reality?",
        "How do we know what is true?"
    ]

    # Test each assistant with each question
    for worldview, assistant_id in assistant_ids.items():
        for question in test_questions:
            query_response = requests.post(
                f"{API_BASE_URL}/assistants/{assistant_id}/query",
                json={"query": question},
                headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
            )

            assert query_response.status_code == 200
            response_text = query_response.json()["response"]

            if isinstance(response_text, dict):
                # Handle template responses
                response_text = str(response_text)

            response_text = response_text.lower()

            # Check for expected philosophical markers
            markers = worldview_markers[worldview]
            matches = sum(1 for marker in markers if marker.lower() in response_text)

            assert matches >= 2, \
                f"{worldview} response lacks philosophical markers. Found {matches} out of {len(markers)}"

    # Clean up
    for assistant_id in assistant_ids.values():
        requests.delete(
            f"{API_BASE_URL}/assistants/{assistant_id}",
            headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
        )

    print("✅ Philosophical consistency test passed")
```

### 4. End-to-End Integration Tests

```python
def test_end_to_end_workflow():
    """Test the complete integration workflow."""
    # 1. Create assistant
    create_response = requests.post(
        f"{API_BASE_URL}/assistants",
        json={
            "name": f"E2E_Test_{uuid.uuid4().hex[:8]}",
            "weltanschauung": "Realismus",
            "instructions": "Answer questions from a Realismus perspective, focusing on the unity of perception and concept.",
            "model": "o1"
        },
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert create_response.status_code == 201
    assistant = create_response.json()
    assistant_id = assistant["id"]

    # 2. Verify the assistant retrieval
    get_response = requests.get(
        f"{API_BASE_URL}/assistants/{assistant_id}",
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert get_response.status_code == 200
    retrieved = get_response.json()
    assert retrieved["weltanschauung"] == "Realismus"

    # 3. Query the assistant with template
    query_response = requests.post(
        f"{API_BASE_URL}/assistants/{assistant_id}/query",
        json={
            "query": "Please correct this misconception",
            "template": "gedankenfehler-formulieren",
            "template_variables": {
                "gedanke_in_weltanschauung": "Perception and conceptual understanding are completely separate processes.",
                "aspekte": "Consider how we experience the world."
            }
        },
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert query_response.status_code == 200
    response = query_response.json()

    # 4. Verify response contains required components
    assert "response" in response
    assert "retrieved_documents" in response

    # 5. Verify template format
    result = response["response"]
    assert "gedanke" in result
    assert "gedanke_zusammenfassung" in result
    assert "gedanke_kind" in result

    # 6. Update assistant
    update_response = requests.put(
        f"{API_BASE_URL}/assistants/{assistant_id}",
        json={
            "name": f"Updated_E2E_Test_{uuid.uuid4().hex[:8]}",
            "temperature": 0.8
        },
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["temperature"] == 0.8

    # 7. Clean up
    delete_response = requests.delete(
        f"{API_BASE_URL}/assistants/{assistant_id}",
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert delete_response.status_code == 200

    print("✅ End-to-end workflow test passed")
```

### 5. Performance Testing

```python
import time

def test_response_performance():
    """Test response time for assistant queries."""
    # Create a test assistant
    create_response = requests.post(
        f"{API_BASE_URL}/assistants",
        json={
            "name": f"Performance_Test_{uuid.uuid4().hex[:8]}",
            "weltanschauung": "Materialismus",
            "instructions": "Provide concise responses for performance testing.",
            "model": "o1"
        },
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    assert create_response.status_code == 201
    assistant_id = create_response.json()["id"]

    # Test questions
    test_questions = [
        "What is consciousness?",
        "How does the brain work?",
        "What is the relationship between brain and mind?",
        "Are humans just complex machines?",
        "What is the nature of free will?"
    ]

    # Measure response times
    response_times = []

    for question in test_questions:
        start_time = time.time()

        response = requests.post(
            f"{API_BASE_URL}/assistants/{assistant_id}/query",
            json={"query": question},
            headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
        )

        end_time = time.time()
        response_time = end_time - start_time
        response_times.append(response_time)

        assert response.status_code == 200

    # Calculate performance metrics
    avg_time = sum(response_times) / len(response_times)
    max_time = max(response_times)
    min_time = min(response_times)

    print(f"Average response time: {avg_time:.2f} seconds")
    print(f"Maximum response time: {max_time:.2f} seconds")
    print(f"Minimum response time: {min_time:.2f} seconds")

    # Assert performance meets requirements
    assert avg_time < 12.0, f"Average response time ({avg_time:.2f}s) exceeds threshold (12.0s)"

    # Clean up
    requests.delete(
        f"{API_BASE_URL}/assistants/{assistant_id}",
        headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
    )

    print("✅ Performance test passed")
```

### 6. User Experience Testing

For user experience testing, we'll need human evaluators. Here's a script to prepare the evaluation:

```python
def prepare_human_evaluation():
    """Prepare test cases for human evaluation."""
    # Create test assistants
    assistant_ids = {}

    for worldview in ["Idealismus", "Materialismus", "Realismus", "Spiritualismus"]:
        create_response = requests.post(
            f"{API_BASE_URL}/assistants",
            json={
                "name": f"UX_Test_{worldview}_{uuid.uuid4().hex[:8]}",
                "weltanschauung": worldview,
                "instructions": f"Answer from a {worldview} perspective.",
                "model": "o1"
            },
            headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
        )

        assert create_response.status_code == 201
        assistant_ids[worldview] = create_response.json()["id"]

    # Standard evaluation questions
    questions = [
        "What is the nature of reality?",
        "How do we know what is true?",
        "What is the relationship between mind and matter?",
        "What gives life meaning and purpose?"
    ]

    # Template evaluation
    template_questions = [
        "Humans are just biological machines with no spiritual dimension.",
        "The physical world is all that exists; everything else is imagination.",
        "Truth is purely subjective and has no objective foundation.",
        "Our perceptions never accurately represent reality."
    ]

    # Generate responses for evaluation
    evaluation_data = []

    # Standard questions
    for worldview, assistant_id in assistant_ids.items():
        for question in questions:
            response = requests.post(
                f"{API_BASE_URL}/assistants/{assistant_id}/query",
                json={"query": question},
                headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
            )

            assert response.status_code == 200

            evaluation_data.append({
                "worldview": worldview,
                "question": question,
                "response": response.json()["response"],
                "type": "standard"
            })

    # Template questions
    for worldview, assistant_id in assistant_ids.items():
        for misconception in template_questions:
            response = requests.post(
                f"{API_BASE_URL}/assistants/{assistant_id}/query",
                json={
                    "query": "Please correct this misconception",
                    "template": "gedankenfehler-formulieren",
                    "template_variables": {
                        "gedanke_in_weltanschauung": misconception,
                        "aspekte": "Consider all aspects of the question."
                    }
                },
                headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
            )

            assert response.status_code == 200

            evaluation_data.append({
                "worldview": worldview,
                "question": misconception,
                "response": response.json()["response"],
                "type": "template"
            })

    # Save evaluation data
    with open("human_evaluation_data.json", "w") as f:
        json.dump(evaluation_data, f, indent=2)

    # Clean up
    for assistant_id in assistant_ids.values():
        requests.delete(
            f"{API_BASE_URL}/assistants/{assistant_id}",
            headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN')}"}
        )

    print("✅ Human evaluation preparation complete")
    print("Evaluation data saved to human_evaluation_data.json")
```

## Test Execution Process

1. **Local Testing**

    - Run all unit tests on local development environment
    - Fix any issues before proceeding

2. **Staging Environment Testing**

    - Deploy to staging environment
    - Run integration and performance tests
    - Verify end-to-end workflow

3. **User Experience Testing**

    - Prepare evaluation materials
    - Engage philosophy experts to review responses
    - Gather feedback and implement improvements

4. **Production Testing**
    - Deploy to production with monitoring
    - Run smoke tests to verify functionality
    - Monitor performance and error rates

## Test Automation

Create a CI/CD pipeline that automates testing:

```yaml
# .github/workflows/test-assistants.yml
name: Test Philosophical Assistants

on:
    push:
        branches: [main, develop]
    pull_request:
        branches: [main, develop]

jobs:
    test:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v3
            - name: Set up Python
              uses: actions/setup-python@v4
              with:
                  python-version: '3.10'
            - name: Install dependencies
              run: |
                  python -m pip install --upgrade pip
                  pip install -r requirements.txt
                  pip install pytest pytest-cov
            - name: Run unit tests
              run: |
                  pytest tests/unit/
            - name: Run integration tests
              run: |
                  pytest tests/integration/
              env:
                  PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
                  PINECONE_HOST: ${{ secrets.PINECONE_HOST }}
                  PINECONE_INDEX_NAME: ${{ secrets.PINECONE_INDEX_NAME }}
                  API_TOKEN: ${{ secrets.API_TOKEN }}
            - name: Generate test report
              run: |
                  pytest --cov=app --cov-report=xml
            - name: Upload test results
              uses: actions/upload-artifact@v3
              with:
                  name: test-results
                  path: coverage.xml
```

This comprehensive testing approach ensures that our philosophical assistants work correctly, provide appropriate responses aligned with their worldviews, and meet performance requirements.
