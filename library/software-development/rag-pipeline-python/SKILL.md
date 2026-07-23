---
name: rag-pipeline-python
description: "Use when user asks to build or explain a Python Retrieval-Augmented Generation pipeline with embeddings, document loading, vector search, hybrid BM25 plus vector retrieval, reranking, JSON extraction, and source verification. NOT for a generic chatbot without retrieval or a paper-writing task. Provides a practical architecture and code-oriented patterns based on the referenced tutorial."
version: 1.1.0
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - rag
    - retrieval-augmented-generation
    - ollama
    - deepseek
    - python
    - lokale-ki
    - hybrid-search
    category: software-development
author: Hermes Agent
license: MIT
lane: worker-heavy
reasoning_effort: xhigh
agent: Analyst
routing_hint: '**Agent-Scope:** Data, ML, modeling, statistics, training, evaluation.
  Off-scope: visual design, code writing, copy — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['vector', 'retrieval', 'and', 'rag-pipeline-python', 'build']
keywords: ['retrieval', 'vector', 'user', 'asks', 'build']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

---
# RAG-Pipeline in Python

> Basierend auf TheMorpheus Tutorials: "KI: Richtige UND aktuelle Antworten"
> Quelle: https://www.youtube.com/watch?v=qgEkG70p4Y0
>
> **Referenzen:**
> - `references/hybrid-search.md` — Hybrid Search (BM25 + Vector + Reranking)
> - `references/morpheus-rag-details.md` — Vollständiger Code aus dem Video

## Das Problem

KI-Modelle (LLMs) antworten "aus dem Kopf":
- **Ungenau** — Fakten werden halluziniert
- **Nicht aktuell** — Trainingsdaten haben einen Cutoff
- **Keine Quelle** — Antworten können nicht verifiziert werden

Beispiel aus dem Video:
> Frage: "Was ist am 15.11.2024 mit Musk und OpenAI passiert?"
> KI-Antwort (ohne RAG): Halluziniert oder "Ich habe keine Informationen..."

## Die Lösung: RAG (Retrieval Augmented Generation)

```
┌─────────────────────────────────────────────────────────────┐
│  BENUTZER-FRAGE                                            │
│  "Was ist aktuell mit OpenAI?"                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  RETRIEVAL (Wissensabfrage)                                │
│  • Suche in Dokumenten/DB/News/API                          │
│  • Finde relevante Artikel/Dokumente                        │
│  • Extrahiere Text-Chunks                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  AUGMENTATION (Kontext aufbauen)                           │
│  • Baue Prompt mit Kontext + Frage                          │
│  • "Basierend auf diesen Quellen: [Chunks]"                 │
│  • "Beantworte die Frage: [Frage]"                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  GENERATION (LLM antwortet mit Kontext)                    │
│  • Lokales Modell (Ollama + DeepSeek R1)                    │
│  • Antwort basiert auf den gelieferten Quellen              │
│  • JSON-Output für strukturierte Verarbeitung               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ANTWORT + QUELLEN                                         │
│  • Faktische Antwort                                        │
│  • Mit Quellenangaben                                       │
│  • Verifizierbar                                            │
└─────────────────────────────────────────────────────────────┘
```

## Architektur aus dem Video (UPGRADED: Hybrid Search)

### Komponenten

1. **Ollama** — Lokales LLM-Hosting
   - Modell: `deepseek-r1:8b` (Reasoning)
   - Embedding: `nomic-embed-text` (Dediziert, entlastet VRAM)
   - Läuft lokal, keine API-Kosten

2. **Hybrid Search** — BM25 + Vector + Reranking
   - **BM25:** Keyword-basiert (funktioniert für exakte Begriffe, Funktionsnamen, Fehlercodes)
   - **Vector:** Semantisch (versteht Bedeutung, Synonyme)
   - **Ensemble:** Kombiniert beides mit Gewichtung
   - **Cross-Encoder Reranker:** BAAI/bge-reranker-v2-m3 (präzisiert Top-Ergebnisse)

3. **Python-Client** — Ollama API ansprechen
   ```python
   from ollama import chat, ChatResponse
   from langchain_ollama import OllamaEmbeddings

   # Dediziertes Embedding-Modell (trennt von Reasoning)
   embeddings = OllamaEmbeddings(model="nomic-embed-text")

   response = chat(
       model='deepseek-r1:8b',
       messages=[{'role': 'user', 'content': question}]
   )
   ```

4. **JSON-Extraktion** — Strukturierte Ausgabe aus Reasoning-Modellen
   - DeepSeek R1 gibt `` tags aus (internes Reasoning)
   - Extraktion via Regex in mehreren Fallback-Schritten
   - Siehe `references/morpheus-rag-details.md` für vollständigen Code

4. **Artikel-Relevanz-Prüfung** — Nur relevante Dokumente verwenden
   - Filterung vor dem RAG-Step
   - Reduziert Halluzinationen
   - Beispiel aus Video: `is_article_relevant(article, query)`

### Code-Struktur (aus Screenshots rekonstruiert)

```python
#!/usr/bin/env python3
"""news_rag.py — RAG-Pipeline für Nachrichten"""

import json
import re
from ollama import chat, ChatResponse

def extract_json_from_response(text: str) -> dict | None:
    """
    Extrahiert JSON aus LLM-Antworten.
    DeepSeek R1 gibt oft ``...`` + JSON aus.
    """
    # Step 1: Entferne  tags
    text = re.sub(r'.*?', '', text, flags=re.DOTALL)

    # Step 2: Suche nach JSON-Code-Block
    match = re.search(r'```json\s*(.+?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Step 3: Suche nach JSON-Strukturen
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start != -1:
            end = text.rfind(end_char)
            if end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    pass

    # Step 4: Versuche gesamten Text als JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def is_article_relevant(article: dict, query: str) -> bool:
    """Prüft ob ein Artikel zur Query relevant ist."""
    # Implementierung: Keyword-Matching, Embedding-Similarity, etc.
    pass


def main():
    question = "Was ist am 15.11.2024 passiert mit Musk und OpenAI?"

    # 1. RETRIEVAL: Suche relevante Artikel
    articles = search_articles(question)  # z.B. via News-API
    relevant = [a for a in articles if is_article_relevant(a, question)]

    # 2. AUGMENTATION: Baue Kontext-Prompt
    context = "\n\n".join([
        f"Artikel {i+1}:\n{a['title']}\n{a['content'][:500]}"
        for i, a in enumerate(relevant[:3])
    ])

    prompt = f"""Basierend auf diesen Artikeln:
{context}

Beantworte die Frage: {question}
Gib die Antwort als JSON aus mit Feldern: answer, sources, confidence."""

    # 3. GENERATION: LLM mit Kontext
    response = chat(
        model='deepseek-r1:8b',
        messages=[{'role': 'user', 'content': prompt}]
    )

    # 4. EXTRACTION: JSON aus Antwort parsen
    result = extract_json_from_response(response.message.content)

    if result:
        print(f"Antwort: {result.get('answer')}")
        print(f"Quellen: {result.get('sources')}")
        print(f"Konfidenz: {result.get('confidence')}")
    else:
        print("Konnte keine strukturierte Antwort extrahieren.")
        print(f"Roh-Antwort: {response.message.content}")


if __name__ == "__main__":
    main()
```

### Code-Struktur (aus Screenshots rekonstruiert)

```python
#!/usr/bin/env python3
"""news_rag.py — RAG-Pipeline für Nachrichten"""

import json
import re
from ollama import chat, ChatResponse

def extract_json_from_response(text: str) -> dict | None:
    """
    Extrahiert JSON aus LLM-Antworten.
    DeepSeek R1 gibt oft <think>...</think> + JSON aus.
    """
    # Step 1: Entferne <think> Tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # Step 2: Suche nach JSON-Code-Block
    match = re.search(r'```json\s*(.+?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Step 3: Suche nach JSON-Strukturen
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start != -1:
            end = text.rfind(end_char)
            if end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    pass

    # Step 4: Versuche gesamten Text als JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def is_article_relevant(article: dict, query: str) -> bool:
    """Prüft ob ein Artikel zur Query relevant ist."""
    # Implementierung: Keyword-Matching, Embedding-Similarity, etc.
    pass


def main():
    question = "Was ist am 15.11.2024 passiert mit Musk und OpenAI?"

    # 1. RETRIEVAL: Suche relevante Artikel
    articles = search_articles(question)  # z.B. via News-API
    relevant = [a for a in articles if is_article_relevant(a, question)]

    # 2. AUGMENTATION: Baue Kontext-Prompt
    context = "\n\n".join([
        f"Artikel {i+1}:\n{a['title']}\n{a['content'][:500]}"
        for i, a in enumerate(relevant[:3])
    ])

    prompt = f"""Basierend auf diesen Artikeln:
{context}

Beantworte die Frage: {question}
Gib die Antwort als JSON aus mit Feldern: answer, sources, confidence."""

    # 3. GENERATION: LLM mit Kontext
    response = chat(
        model='deepseek-r1:8b',
        messages=[{'role': 'user', 'content': prompt}]
    )

    # 4. EXTRACTION: JSON aus Antwort parsen
    result = extract_json_from_response(response.message.content)

    if result:
        print(f"Antwort: {result.get('answer')}")
        print(f"Quellen: {result.get('sources')}")
        print(f"Konfidenz: {result.get('confidence')}")
    else:
        print("Konnte keine strukturierte Antwort extrahieren.")
        print(f"Roh-Antwort: {response.message.content}")


if __name__ == "__main__":
    main()
```

### Hybrid Search Beispiel (UPGRADED)

```python
#!/usr/bin/env python3
"""hybrid_rag.py — RAG-Pipeline mit Hybrid Search"""

import json
import re
from ollama import chat, ChatResponse
from langchain_ollama import OllamaEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

# ========== KONFIGURATION ==========
EMBEDDING_MODEL = "nomic-embed-text"  # Dediziertes Embedding
LLM_MODEL = "deepseek-r1:8b"          # Reasoning-Modell
BM25_WEIGHT = 0.4                     # Keyword-Gewichtung
VECTOR_WEIGHT = 0.6                   # Semantische Gewichtung
TOP_K = 10                            # Vor-Reranking
TOP_N = 4                             # Nach Reranking

# ========== EMBEDDINGS ==========
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

def create_hybrid_retriever(documents):
    """
    Erstellt einen Hybrid Retriever (BM25 + Vector).

    Args:
        documents: Liste von Document-Objekten mit .page_content

    Returns:
        EnsembleRetriever
    """
    # BM25 Retriever (Keyword-basiert)
    bm25 = BM25Retriever.from_documents(documents)
    bm25.k = TOP_K

    # Vector Retriever (semantisch)
    from langchain_community.vectorstores import FAISS
    vectorstore = FAISS.from_documents(documents, embeddings)
    vector = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    # Ensemble: Kombiniert beides
    hybrid = EnsembleRetriever(
        retrievers=[bm25, vector],
        weights=[BM25_WEIGHT, VECTOR_WEIGHT]
    )

    return hybrid


def rerank_results(query, results):
    """
    Optional: Cross-Encoder Reranking für präzisere Ergebnisse.
    Erfordert: pip install sentence-transformers
    """
    try:
        from sentence_transformers import CrossEncoder
        reranker = CrossEncoder('BAAI/bge-reranker-v2-m3')

        pairs = [[query, doc.page_content] for doc in results]
        scores = reranker.predict(pairs)

        # Sortiere nach Score
        scored = list(zip(results, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, score in scored[:TOP_N]]
    except ImportError:
        # Fallback: Ohne Reranking
        return results[:TOP_N]


def extract_json_from_response(text: str) -> dict | None:
    """Extrahiert JSON aus LLM-Antworten (DeepSeek R1)."""
    # Step 1: Entferne  tags
    text = re.sub(r'.*?', '', text, flags=re.DOTALL)

    # Step 2: Suche nach JSON-Code-Block
    match = re.search(r'```json\s*(.+?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Step 3: Suche nach JSON-Strukturen
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start != -1:
            end = text.rfind(end_char)
            if end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    pass

    # Step 4: Versuche gesamten Text als JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def main():
    question = "Was ist aktuell mit OpenAI?"

    # 1. RETRIEVAL: Hybrid Search
    # documents = load_documents()  # Deine Dokumente laden
    # retriever = create_hybrid_retriever(documents)
    # raw_results = retriever.get_relevant_documents(question)
    # relevant = rerank_results(question, raw_results)

    # 2. AUGMENTATION: Baue Kontext-Prompt
    # context = "\n\n".join([doc.page_content for doc in relevant[:3]])

    prompt = f"""Basierend auf diesen Quellen:
{context}

Beantworte die Frage: {question}
Gib die Antwort als JSON aus mit Feldern: answer, sources, confidence."""

    # 3. GENERATION: LLM mit Kontext
    response = chat(
        model=LLM_MODEL,
        messages=[{'role': 'user', 'content': prompt}]
    )

    # 4. EXTRACTION: JSON aus Antwort parsen
    result = extract_json_from_response(response.message.content)

    if result:
        print(f"Antwort: {result.get('answer')}")
        print(f"Quellen: {result.get('sources')}")
        print(f"Konfidenz: {result.get('confidence')}")
    else:
        print("Konnte keine strukturierte Antwort extrahieren.")


if __name__ == "__main__":
    main()
```

### Dependencies

```bash
pip install ollama langchain langchain-community langchain-ollama faiss-cpu sentence-transformers
```

### Warum Hybrid Search besser ist

| Ansatz | Stärke | Schwäche |
|--------|--------|----------|
| Nur BM25 | Exakte Begriffe, Funktionsnamen | Keine Semantik |
| Nur Vector | Bedeutung, Synonyme | Verliert spezifische Terme |
| **Hybrid** | **Beides kombiniert** | **Mehr Komplexität** |

**Beispiel:**
- Query: "Wie fixe ich den CUDA Out of Memory Fehler?"
- BM25 findet: "CUDA", "Out of Memory", "Fehler" (exakt)
- Vector findet: "GPU Speicher voll", "VRAM Limit" (semantisch)
- **Hybrid findet beides** → Bessere Abdeckung

### Dediziertes Embedding-Modell

**Warum nomic-embed-text statt deepseek-r1 für Embeddings?**

| | deepseek-r1:8b | nomic-embed-text |
|---|---|---|
| Größe | 5.2 GB | 274 MB |
| VRAM-Nutzung | ~5 GB | ~300 MB |
| Geschwindigkeit | Langsam (Reasoning) | Schnell (nur Embedding) |
| Zweck | Reasoning + Generation | Nur Embedding |
| Trennung | Blockiert R1 während Embedding | Parallel möglich |

**Empfehlung:** Immer dediziertes Embedding-Modell nutzen. R1 für Reasoning, nomic für Retrieval.

## Key Learnings

### 1. Lokale KI ist ausreichend für RAG
- DeepSeek R1 8B auf Consumer-Hardware (RTX 5060)
- Keine API-Kosten, keine Rate-Limits
- Daten bleiben lokal

### 2. JSON-Extraktion ist kritisch
- Reasoning-Modelle (DeepSeek R1) geben  tags aus
- Regex-basierte Extraktion notwendig
- Mehrere Fallback-Strategien

### 3. Quellenverifizierung
- Jede Antwort muss Quellen haben
- Nutzer kann nachprüfen
- Reduziert Halluzinationen drastisch

### 4. Relevanz-Filterung
- Nicht alle Dokumente in den Kontext
- Vorfilterung spart Tokens und reduziert Noise

## Anwendung für Hermes

### Wie ich RAG nutzen kann

**Aktuell:** Ich suche im Web (web_search, web_extract) und gebe die Ergebnisse als Kontext an das LLM.

**Mit RAG-Pipeline (verbessert):**
1. Suche gezielt nach aktuellen Informationen
2. Extrahiere und speichere relevante Dokumente
3. Baue Kontext-Prompt mit Quellen
4. Generiere Antwort basierend auf den Quellen
5. Zitiere die Quellen in der Antwort

### Beispiel: Aktuelle Esports-Frage

```
User: "Wer hat IEM Cologne 2026 gewonnen?"

Ohne RAG:
  Ich: "Ich habe keine Informationen über IEM Cologne 2026..."

Mit RAG:
  Ich: Suche nach "IEM Cologne 2026 winner"
  Ich: Extrahiere Artikel von HLTV, ESL
  Ich: Baue Prompt mit Artikel-Inhalten
  Ich: "Team X hat IEM Cologne 2026 gewonnen.
        Quelle: HLTV.org, Artikel vom 20.07.2026"
```

## Verwandte Skills

- `ki-murks-verhindern` — Quality Gates für KI-Agenten
- `ollama-local-hosting` — Lokale LLM-Einrichtung
- `multi-agent-research` — Parallele Recherche für RAG

## Pitfalls

- **JSON-Extraktion ist fragil** — DeepSeek's Output-Format kann variieren
- **Kontext-Window-Limit** — Zu viele Dokumente überladen das Modell
- **Relevanz-Prüfung ist entscheidend** — Irrelevante Dokumente führen zu schlechten Antworten
- **Quellen können veraltet sein** — RAG ist nur so aktuell wie die Datenquelle

## Ressourcen

- Video: https://www.youtube.com/watch?v=qgEkG70p4Y0
- Ollama: https://ollama.com
- DeepSeek R1: https://github.com/deepseek-ai/DeepSeek-R1
