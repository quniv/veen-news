<script lang="ts">
  import type { Category } from '$lib/types';
  import { CATEGORY_LABELS } from '$lib/types';

  const {
    categories,
    active,
    counts,
    onselect
  }: {
    categories: Category[];
    active: Category;
    counts: Record<Category, number>;
    onselect: (cat: Category) => void;
  } = $props();
</script>

<div class="tabs-wrapper">
  <div class="tabs" role="tablist" aria-label="News categories">
    {#each categories as cat (cat)}
      <button
        role="tab"
        aria-selected={cat === active}
        class="tab"
        class:active={cat === active}
        onclick={() => onselect(cat)}
      >
        {CATEGORY_LABELS[cat]}
        <span class="count">{counts[cat] ?? 0}</span>
      </button>
    {/each}
  </div>
</div>

<style>
  .tabs-wrapper {
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.25rem;
  }

  .tabs-wrapper::-webkit-scrollbar {
    display: none;
  }

  .tabs {
    display: flex;
    gap: 0.15rem;
    padding-bottom: 0;
    white-space: nowrap;
    min-width: max-content;
  }

  .tab {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.55rem 0.9rem;
    font-size: 0.83rem;
    font-weight: 500;
    color: var(--text-muted);
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: color 0.15s ease, border-color 0.15s ease;
    position: relative;
    bottom: -1px;
  }

  .tab:hover {
    color: var(--text);
  }

  .tab.active {
    color: var(--accent-hover);
    border-bottom-color: var(--accent);
    font-weight: 600;
  }

  .count {
    font-size: 0.7rem;
    font-weight: 500;
    background: var(--border);
    color: var(--text-muted);
    padding: 0.05em 0.4em;
    border-radius: 999px;
    min-width: 1.4em;
    text-align: center;
    line-height: 1.5;
  }

  .tab.active .count {
    background: color-mix(in srgb, var(--accent) 25%, transparent);
    color: var(--accent-hover);
  }
</style>
