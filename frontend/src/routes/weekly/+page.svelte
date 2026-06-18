<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchIndex, fetchWeekly } from '$lib/api';
  import { CATEGORIES, CATEGORY_LABELS } from '$lib/types';
  import type { Cluster, Category } from '$lib/types';
  import ArticleCard from '$lib/components/ArticleCard.svelte';

  interface WeeklyData {
    week: string;
    label?: string;
    date_range?: { start: string; end: string };
    total_articles?: number;
    clusters?: Cluster[];
    categories?: Record<Category, { articles: import('$lib/types').Article[]; count: number }>;
    stats?: { fetched: number; published: number };
  }

  let data = $state<WeeklyData | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  const weekLabel = $derived.by(() => {
    if (!data) return '';
    if (data.label) return data.label;
    if (data.week) {
      const [year, week] = data.week.split('-W');
      if (week) return `Week ${week} · ${year}`;
    }
    return data.week ?? '';
  });

  const topClusters = $derived(data?.clusters?.slice(0, 5) ?? []);

  onMount(async () => {
    try {
      const index = await fetchIndex();
      const latest = index.weekly?.at(-1);
      if (!latest) {
        data = null;
        return;
      }
      data = await fetchWeekly(latest.week) as WeeklyData;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load weekly recap';
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Veen — Weekly Recap</title>
</svelte:head>

<div class="container">
  {#if loading}
    <div class="state-center">
      <div class="spinner" aria-label="Loading"></div>
      <p class="state-text">Loading weekly recap...</p>
    </div>
  {:else if error}
    <div class="state-center">
      <p class="state-error">{error}</p>
    </div>
  {:else if !data}
    <div class="state-center">
      <p class="state-waiting">No weekly recap available yet.</p>
      <p class="state-sub">Weeklies are generated after at least one full week of crawls.</p>
    </div>
  {:else}
    <div class="page-header">
      <div class="section-label">Weekly Recap</div>
      <h1 class="page-title">{weekLabel}</h1>
      {#if data.total_articles}
        <p class="page-sub">{data.total_articles} articles this week</p>
      {/if}
    </div>

    {#if topClusters.length > 0}
      <section class="section">
        <h2 class="section-title">Top Topics</h2>
        <div class="cluster-list">
          {#each topClusters as cluster (cluster.id)}
            <div class="cluster-card">
              <div class="cluster-header">
                <span class="cluster-topic">{cluster.topic}</span>
                <span class="cluster-count">{cluster.article_count} articles</span>
              </div>
              {#if cluster.summary}
                <p class="cluster-summary">{cluster.summary}</p>
              {/if}
            </div>
          {/each}
        </div>
      </section>
    {/if}

    {#if data.categories}
      <section class="section">
        <h2 class="section-title">By Category</h2>
        {#each CATEGORIES as cat (cat)}
          {@const catData = data.categories?.[cat]}
          {#if catData && catData.articles?.length > 0}
            <div class="cat-section">
              <h3 class="cat-title">
                {CATEGORY_LABELS[cat]}
                <span class="cat-count">{catData.count ?? catData.articles.length}</span>
              </h3>
              <div class="article-list">
                {#each catData.articles.slice(0, 5) as article (article.id)}
                  <ArticleCard {article} />
                {/each}
              </div>
            </div>
          {/if}
        {/each}
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
  }

  .page-sub {
    margin-top: 0.35rem;
    font-size: 0.85rem;
    color: var(--text-muted);
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

  .cluster-list {
    display: flex;
    flex-direction: column;
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
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 0.35rem;
  }

  .cluster-topic {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text);
  }

  .cluster-count {
    font-size: 0.72rem;
    color: var(--text-dim);
    white-space: nowrap;
  }

  .cluster-summary {
    font-size: 0.82rem;
    color: var(--text-muted);
    line-height: 1.5;
    margin: 0;
  }

  .cat-section {
    margin-bottom: 1.75rem;
  }

  .cat-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.65rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .cat-count {
    font-size: 0.72rem;
    background: var(--border);
    color: var(--text-dim);
    padding: 0.05em 0.45em;
    border-radius: 999px;
    font-variant-numeric: tabular-nums;
  }

  .article-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
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
