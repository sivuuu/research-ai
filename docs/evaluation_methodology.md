# ResearchGraph AI — Evaluation Methodology & Metric Formulations

## 1. Overview & Evaluation Philosophy

The **ResearchGraph AI** evaluation framework provides scientific, reproducible validation across 7 distinct dimensions. Rather than relying on qualitative impressions or fabricated benchmark numbers, this platform enforces explicit ground-truth benchmarking against human-annotated academic questions, labeled claims, and empirical contradiction pairs.

Evaluation examples are strictly isolated from the live retrieval corpus to prevent data contamination and target leakage.

---

## 2. Metric Formulations

### 2.1 Retrieval Recall@K ($K \in \{1, 3, 5\}$)
Measures the proportion of human-annotated relevant document passages retrieved within the top-$K$ candidate positions:

$$\text{Recall@K} = \frac{|\mathcal{R}_{1..K} \cap \mathcal{E}|}{|\mathcal{E}|}$$

where:
- $\mathcal{R}_{1..K}$ is the set of retrieved documents/chunks in ranks $1$ through $K$.
- $\mathcal{E}$ is the ground-truth set of relevant documents/chunks for the question.

### 2.2 Mean Reciprocal Rank (MRR)
Measures ranking quality by evaluating how high the first relevant ground-truth source appears in the ranking:

$$\text{MRR} = \frac{1}{|\mathcal{Q}|} \sum_{q \in \mathcal{Q}} \frac{1}{\text{rank}_q}$$

where $\text{rank}_q$ is the rank position of the first relevant document retrieved for query $q$ (or $\infty$ with reciprocal score $0$ if none is retrieved).

### 2.3 Citation Precision & Citation Coverage
- **Citation Precision**: The percentage of citations in the synthesized report that resolve to actual, verified source chunks containing the claimed fact:
  $$\text{Citation Precision} = \frac{N_{\text{valid}}}{N_{\text{total citations}}}$$
- **Citation Coverage**: The fraction of key retrieved candidate sources that were actively incorporated into the generated synthesis:
  $$\text{Citation Coverage} = \frac{|\mathcal{S}_{\text{cited}} \cap \mathcal{S}_{\text{expected}}|}{|\mathcal{S}_{\text{expected}}|}$$

### 2.4 Claim Extraction Precision & Recall
Evaluates the accuracy of structured claims extracted by comparing token-level Jaccard overlap between extracted claims $\mathcal{C}_{\text{ext}}$ and human-labeled ground truth claims $\mathcal{C}_{\text{gold}}$ (match threshold $\theta = 0.35$):

$$\text{Precision}_{\text{claims}} = \frac{|\mathcal{C}_{\text{ext}} \cap_{\theta} \mathcal{C}_{\text{gold}}|}{|\mathcal{C}_{\text{ext}}|}, \quad \text{Recall}_{\text{claims}} = \frac{|\mathcal{C}_{\text{ext}} \cap_{\theta} \mathcal{C}_{\text{gold}}|}{|\mathcal{C}_{\text{gold}}|}$$

$$F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

### 2.5 Contradiction Detection Precision & Recall
Evaluates whether pairs of opposing assertions are correctly flagged as `CONTRADICTS`:

$$\text{Precision}_{\text{contra}} = \frac{|\mathcal{P}_{\text{detected}} \cap \mathcal{P}_{\text{gold}}|}{|\mathcal{P}_{\text{detected}}|}, \quad \text{Recall}_{\text{contra}} = \frac{|\mathcal{P}_{\text{detected}} \cap \mathcal{P}_{\text{gold}}|}{|\mathcal{P}_{\text{gold}}|}$$

### 2.6 Answer Faithfulness
Evaluates the proportion of sentences in the generated synthesis that are directly supported by text in the cited passages, penalizing model hallucination and ungrounded extrapolation:

$$\text{Faithfulness} = \frac{N_{\text{supported sentences}}}{N_{\text{total synthesized sentences}}}$$

### 2.7 End-to-End Latency
Measures the wall-clock execution time in milliseconds ($t_{\text{end}} - t_{\text{start}}$) across the entire 7-agent pipeline.

---

## 3. Dataset Creation & Ground Truth Annotation

The benchmark dataset in `sample_evaluation/ground_truth.json` was created via dual-annotator consensus:
1. **Query Formulation**: Representative research questions spanning broad sensemaking ("How does GraphRAG improve over baseline RAG?") to technical trade-offs ("Computational costs of graph traversal vs vector search") and unanswerable out-of-corpus queries ("Superconducting qubit coherence times").
2. **Ground Truth Identification**: Human annotators read source papers and marked the exact gold-standard passages that answer the questions.
3. **Contradiction Labeling**: Specific empirical tensions between papers (e.g. dense vector superiority vs. BM25 superiority on technical identifiers; GraphRAG high indexing token consumption vs. vector search minimal overhead) were explicitly cataloged as target contradiction pairs.
4. **Refusal Validation**: Out-of-corpus test cases verify that the system issues an explicit evidence gap notification rather than fabricating an answer.
