<script lang="ts">
  const { score }: { score: number } = $props();

  const color = $derived(
    score >= 0.7 ? 'var(--score-high)' :
    score >= 0.4 ? 'var(--score-mid)' :
    'var(--score-low)'
  );
</script>

<span class="badge" style="color: {color}; border-color: {color};">
  {score.toFixed(2)}
</span>

<style>
  .badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.1em 0.45em;
    border-radius: 999px;
    border: 1px solid currentColor;
    letter-spacing: 0.02em;
    line-height: 1.4;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }
</style>
