<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchIndex, fetchMonthly } from '$lib/api';
  import { CATEGORIES, CATEGORY_LABELS } from '$lib/types';
  import type { Cluster, Category } from '$lib/types';

  interface CategorySummary {
    count: number;
    top_sources?: string[];
  }

  interface MonthlyData {
    month: string;
    label?: string;
    total_articles?: number;
    clusters?: Cluster[];
    categories?: Record<Category, CategorySummary>;
    stats?: { fetched: number; published: number; sources_crawled?: number };
  }

  let data = $state<MonthlyData | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  const monthLabel = $derived.by(() => {
    if (!data) return '';
    if (data.label) return data.label;
    if (data.month) {
      // format "2026-06" → "June 2026"
      const [year, month] = data.month.split('-');
      if (year && month) {
        const d = new Date(Number(year), Number(month) - 1, 1);
        if (!isNaN(d.getTime())) {
          return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        }
      }
    }
    return data.month ?? '';
  });

  const topClusters = $derived(data?.clusters?.slice(0, 8) ?? []);

  const categoryBreakdown = $derived.by(() => {
    if (!data?.categories) return [];
    return CATEGORIES
      .filter(cat => (data!.categories![cat]?.count ?? 0) > 0)
      .map(cat => ({ cat, ...data!.categories![cat] }))
      .sort((a, b) => (b.count ?? 0) - (a.count ?? 0));
  });

  onMount(async () => {
    try {
      const index = await fetchIndex();
      const latest = index.monthly?.at(-1);
      if (!latest) {
        data = null;
        return;
      }
      data = await fetchMonthly(latest.month) as MonthlyData;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load monthly recap';
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Veen — Monthly Recap</title>
</svelte:head>

<div class="container">
  {#if loading}
    <div class="state-center">
      <div class="spinner" aria-label="Loading"></div>
      <p class="state-text">Loading monthly recap...</p>
    </div>
  {:else if error}
    <div class="state-center">
      <p class="state-error">{error}</p>
    </div>
  {:else if !data}
    <div class="state-center">
      <p class="state-waiting">No monthly recap available yet.</p>
      <p class="state-sub">Monthly recaps are generated at the end of each calendar month.</p>
    </div>
  {:else}
    <div class="page-header">
      <div class="section-label">Monthly Recap</div>
      <h1 class="page-title">{monthLabel}</h1>
      {#if data.stats || data.total_articles}
        <div class="stats-row">
          {#if data.total_articles}
            <span class="stat-chip">{data.total_articles} articles</span>
          {/if}
          {#if data.stats?.fetched}
            <span class="stat-chip">{data.stats.fetched} fetched</span>
          {/if}
          {#if data.stats?.sources_crawled}
            <span class="stat-chip">{data.stats.sources_crawled} sources</span>
          {/if}
        </div>
      {/if}
    </div>

    {#if topClusters.length > 0}
      <section class="section">
        <h2 class="section-title">Top Topics This Month</h2>
        <div class="cluster-grid">
          {#each topClusters as cluster (cluster.id)}
            <div class="cluster-card">
              <div class="cluster-header">
                <span class="cluster-topic">{cluster.topic}</span>
                <span class="cluster-count">{cluster.article_count}</span>
              </div>
              {#if cluster.summary}
                <p class="cluster-summary">{cluster.summary}</p>
              {/if}
            </div>
          {/each}
        </div>
      </section>
    {/if}

    {#if categoryBreakdown.length > 0}
      <section class="section">
        <h2 class="section-title">Category Breakdown</h2>
        <div class="breakdown-list">
          {#each categoryBreakdown as item (item.cat)}
            <div class="breakdown-row">
              <div class="breakdown-left">
                <span class="breakdown-label">{CATEGORY_LABELS[item.cat]}</span>
                {#if item.top_sources?.length}
                  <span class="breakdown-sources">{item.top_sources.slice(0, 3).join(', ')}</span>
                {/if}
              </div>
              <div class="breakdown-right">
                <span class="breakdown-count">{item.count}</span>
                <div class="breakdown-bar-wrap">
                  <div
                    class="breakdown-bar"
                    style="width: {Math.min(100, (item.count / (data?.total_articles || item.count)) * 100 * 3)}%"
                  ></div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </section>
    {/if}
  {/if}
</div>

<style>
  .page-header {
    margin-bottom: 2rem;
  }

  .section-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent-hover);
    margin-bottom: 0.35rem;
  }

  .page-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
    margin-bottom: 0.6rem;
  }

  .stats-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .stat-chip {
    font-size: 0.75rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 0.2em 0.65em;
    border-radius: 999px;
  }

  .section {
    margin-bottom: 2.5rem;
  }

  .section-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.85rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
  }

  .cluster-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.6rem;
  }

  .cluster-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.85rem 1rem;
  }

  .cluster-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 0.35rem;
  }

  .cluster-topic {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1.35;
  }

  .cluster-count {
    font-size: 0.7rem;
    background: color-mix(in srgb, var(--accent) 20%, transparent);
    color: var(--accent-hover);
    padding: 0.1em 0.45em;
    border-radius: 999px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .cluster-summary {
    font-size: 0.8rem;
    color: var(--text-muted);
    line-height: 1.5;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .breakdown-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .breakdown-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.65rem 0.85rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }

  .breakdown-left {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    flex: 1;
    min-width: 0;
  }

  .breakdown-label {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text);
  }

  .breakdown-sources {
    font-size: 0.72rem;
    color: var(--text-dim);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .breakdown-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
  }

  .breakdown-count {
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--accent-hover);
    font-variant-numeric: tabular-nums;
    min-width: 2.5rem;
    text-align: right;
  }

  .breakdown-bar-wrap {
    width: 80px;
    height: 4px;
    background: var(--border);
    border-radius: 999px;
    overflow: hidden;
  }

  .breakdown-bar {
    height: 100%;
    background: var(--accent);
    border-radius: 999px;
    min-width: 3px;
    max-width: 100%;
  }

  .state-center {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 4rem 1rem;
    text-align: center;
  }

  .spinner {
    width: 2rem;
    height: 2rem;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .state-text {
    color: var(--text-muted);
    font-size: 0.9rem;
  }

  .state-error {
    color: var(--score-low);
    font-size: 0.9rem;
  }

  .state-waiting {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
  }

  .state-sub {
    font-size: 0.85rem;
    color: var(--text-muted);
    max-width: 380px;
  }
</style>
