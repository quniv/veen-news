<script lang="ts">
  import type { Article } from '$lib/types';
  import ScoreBadge from './ScoreBadge.svelte';

  const { article }: { article: Article } = $props();

  function formatDate(published_at: string | null): string {
    if (!published_at) return '';
    const date = new Date(published_at);
    if (isNaN(date.getTime())) return '';

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = diffMs / (1000 * 60 * 60);

    if (diffHours < 1) {
      const mins = Math.floor(diffMs / (1000 * 60));
      return `${mins}m ago`;
    }
    if (diffHours < 24) {
      return `${Math.floor(diffHours)}h ago`;
    }

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  const dateLabel = $derived(formatDate(article.published_at));
</script>

<article class="card">
  <div class="card-header">
    <span class="source">{article.source}</span>
    {#if dateLabel}
      <span class="date">{dateLabel}</span>
    {/if}
    <ScoreBadge score={article.score} />
  </div>
  <h3 class="title">
    <a href={article.url} target="_blank" rel="noopener noreferrer">
      {article.title}
    </a>
  </h3>
  {#if article.summary}
    <p class="summary">{article.summary}</p>
  {/if}
</article>

<style>
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    transition: background 0.15s ease, border-color 0.15s ease;
  }

  .card:hover {
    background: var(--bg-card-hover);
    border-color: var(--accent);
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .source {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--accent-hover);
    background: color-mix(in srgb, var(--accent) 15%, transparent);
    padding: 0.1em 0.5em;
    border-radius: 999px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }

  .date {
    font-size: 0.72rem;
    color: var(--text-dim);
    margin-left: auto;
  }

  .title {
    font-size: 0.975rem;
    font-weight: 600;
    line-height: 1.45;
    margin: 0;
  }

  .title a {
    color: var(--text);
    text-decoration: none;
  }

  .title a:hover {
    color: var(--accent-hover);
    text-decoration: underline;
  }

  .summary {
    font-size: 0.85rem;
    color: var(--text-muted);
    line-height: 1.55;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
