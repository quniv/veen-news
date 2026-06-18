<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchLatest } from '$lib/api';
  import { CATEGORIES } from '$lib/types';
  import type { Digest, Category } from '$lib/types';
  import TopicTabs from '$lib/components/TopicTabs.svelte';
  import ArticleCard from '$lib/components/ArticleCard.svelte';
  import DailyRecap from '$lib/components/DailyRecap.svelte';

  let digest = $state<Digest | null>(null);
  let activeCategory = $state<Category>('technology');
  let loading = $state(true);
  let error = $state<string | null>(null);

  const articles = $derived(digest?.categories[activeCategory] ?? []);

  const categoryCounts = $derived.by(() => {
    if (!digest) return Object.fromEntries(CATEGORIES.map(c => [c, 0])) as Record<Category, number>;
    return Object.fromEntries(
      CATEGORIES.map(c => [c, digest!.categories[c]?.length ?? 0])
    ) as Record<Category, number>;
  });

  const dateLabel = $derived.by(() => {
    if (!digest?.date) return null;
    const d = new Date(digest.date);
    if (isNaN(d.getTime())) return digest.date;
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  });

  onMount(async () => {
    try {
      digest = await fetchLatest();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load digest';
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Veen — Daily Digest</title>
</svelte:head>

<div class="container">
  {#if loading}
    <div class="state-center">
      <div class="spinner" aria-label="Loading"></div>
      <p class="state-text">Loading digest...</p>
    </div>
  {:else if error}
    <div class="state-center">
      <p class="state-error">{error}</p>
    </div>
  {:else if !digest?.date}
    <div class="state-center">
      <p class="state-waiting">Waiting for first crawl...</p>
      <p class="state-sub">Check back later — Veen will populate once the pipeline runs.</p>
    </div>
  {:else}
    <div class="page-header">
      <div class="page-title-row">
        <h1 class="page-date">{dateLabel}</h1>
        <div class="stats">
          <span class="stat">{digest.stats.published} articles</span>
          <span class="stat-sep">·</span>
          <span class="stat">{digest.stats.fetched} fetched</span>
          {#if digest.stats.clusters_formed > 0}
            <span class="stat-sep">·</span>
            <span class="stat">{digest.stats.clusters_formed} clusters</span>
          {/if}
        </div>
      </div>
    </div>

    <TopicTabs
      categories={CATEGORIES}
      active={activeCategory}
      counts={categoryCounts}
      onselect={(cat) => { activeCategory = cat; }}
    />

    {#if articles.length === 0}
      <div class="state-center">
        <p class="state-empty">No articles in this category yet.</p>
      </div>
    {:else}
      <div class="article-list">
        {#each articles as article (article.id)}
          <ArticleCard {article} />
        {/each}
      </div>
    {/if}

    {#if digest.daily_recap}
      <DailyRecap recap={digest.daily_recap} />
    {/if}
  {/if}
</div>

<style>
  .page-header {
    margin-bottom: 1.5rem;
  }

  .page-title-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .page-date {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.01em;
  }

  .stats {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.8rem;
    color: var(--text-dim);
  }

  .stat-sep {
    color: var(--border);
  }

  .article-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
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

  .state-empty {
    color: var(--text-muted);
    font-size: 0.9rem;
  }
</style>
