import numpy as np


def mrr_at_k_from_ordered_relevance(ordered_relevance: np.ndarray, k: int) -> float:
    """
    Compute MRR@K when columns are already ordered by decreasing relevance.

    Parameters
    ----------
    ordered_relevance : np.ndarray, shape (n_queries, n_documents)
        Binary matrix where each row is sorted by decreasing predicted relevance.
        Value 1 = relevant, 0 = not relevant.
    k : int
        Cutoff rank.

    Returns
    -------
    float
        MRR@K value.
    """
    if k <= 0:
        return 0.0

    # Consider only the first K columns
    top_k = ordered_relevance[:, :k]

    # Find the first relevant position in each row (0‑based)
    # argmax returns the first index where value is 1; if no 1, returns 0
    # But we need to distinguish rows with no relevant document.
    first_idx = np.argmax(top_k, axis=1)  # shape (n_queries,)

    # Create a boolean mask: rows that have at least one relevant document in top K
    has_relevant = np.any(top_k, axis=1)

    # Reciprocal rank: 1/(pos+1) for rows with relevant, 0 otherwise
    rr = np.where(has_relevant, 1.0 / (first_idx + 1), 0.0)

    # Mean over queries
    return float(np.mean(rr))


def ndcg_at_k(ordered_relevance: np.ndarray, k: int, method: str = "exp") -> float:
    """
    Compute Normalized Discounted Cumulative Gain at cutoff K.

    Parameters
    ----------
    ordered_relevance : np.ndarray, shape (n_queries, n_documents)
        Relevance matrix where each row is sorted by decreasing predicted relevance.
        Values can be binary (0/1) or graded (e.g., 0-4).
    k : int
        Cutoff rank (may be larger than n_documents).
    method : str, either 'exp' (default) or 'linear'
        - 'exp' : DCG = sum (2^rel - 1) / log2(i+1)
        - 'linear' : DCG = sum rel / log2(i+1)

    Returns
    -------
    float
        NDCG@K averaged over all queries.
    """
    if k <= 0:
        return 0.0

    n_docs = ordered_relevance.shape[1]
    k_actual = min(k, n_docs)  # effective cutoff

    # Truncate to top k_actual columns
    top_k = ordered_relevance[:, :k_actual]

    # Compute gains
    if method == "exp":
        gains = np.power(2, top_k) - 1
    elif method == "linear":
        gains = top_k
    else:
        raise ValueError("method must be 'exp' or 'linear'")

    # Discounts: 1 / log2(i+1) for i = 1..k_actual
    positions = np.arange(1, k_actual + 1, dtype=float)
    discounts = np.log2(positions + 1)

    # DCG per query (broadcast: gains shape (n_queries, k_actual), discounts shape (k_actual,))
    dcg = np.sum(gains / discounts, axis=1)

    # IDCG: sort each row descending and take top k_actual
    ideal_sorted = np.sort(ordered_relevance, axis=1)[:, ::-1]  # descending
    ideal_top_k = ideal_sorted[:, :k_actual]

    if method == "exp":
        ideal_gains = np.power(2, ideal_top_k) - 1
    else:
        ideal_gains = ideal_top_k

    idcg = np.sum(ideal_gains / discounts, axis=1)

    # Avoid division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        ndcg = np.where(idcg > 0, dcg / idcg, 0.0)

    return float(np.mean(ndcg))
