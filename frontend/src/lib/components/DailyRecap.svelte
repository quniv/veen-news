<script lang="ts">
  interface DailyRecap {
    global_analysis: string;
    vietnam_analysis: string;
    watch_list: string;
    full_summary: string;
  }

  let { recap }: { recap: DailyRecap } = $props();
</script>

<section class="daily-recap">
  <header class="recap-header">
    <h2>📈 Xu hướng &amp; Nhận định hôm nay</h2>
  </header>

  <div class="recap-body">
    <div class="recap-section">
      <span class="section-label">🌐 Toàn cầu</span>
      <p class="section-text">{recap.global_analysis}</p>
    </div>

    <div class="recap-section">
      <span class="section-label">🇻🇳 Việt Nam</span>
      <p class="section-text">{recap.vietnam_analysis}</p>
    </div>

    <div class="recap-section">
      <span class="section-label">👁 Đáng theo dõi</span>
      <p class="section-text">{recap.watch_list}</p>
    </div>
  </div>

  <hr class="recap-divider" />

  <div class="full-summary">
    <h3 class="summary-header">🗞️ Tóm tắt Toàn cảnh</h3>
    <p class="summary-text">{recap.full_summary}</p>
  </div>
</section>

<style>
  .daily-recap {
    margin-top: 2.5rem;
    border-top: 2px solid var(--border);
    background-color: var(--surface);
    border-radius: 0.5rem;
    padding: 1.75rem 2rem;
  }

  .recap-header {
    margin-bottom: 1.5rem;
  }

  .recap-header h2 {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text);
    margin: 0;
    line-height: 1.4;
  }

  .recap-body {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .recap-section {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .section-label {
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .section-text {
    margin: 0;
    color: var(--text-dim);
    line-height: 1.75;
    font-size: 0.95rem;
  }

  .recap-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.75rem 0;
  }

  .full-summary {
    border-left: 3px solid var(--accent);
    padding-left: 1.25rem;
  }

  .summary-header {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
    margin: 0 0 0.75rem 0;
    line-height: 1.4;
  }

  .summary-text {
    margin: 0;
    color: var(--text);
    line-height: 1.8;
    font-size: 0.95rem;
  }

  @media (max-width: 640px) {
    .daily-recap {
      padding: 1.25rem 1rem;
      border-radius: 0.25rem;
    }
  }
</style>
