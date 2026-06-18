<script lang="ts">
  import '../app.css';
  import type { Snippet } from 'svelte';

  const { children }: { children: Snippet } = $props();
</script>

<header class="header">
  <div class="container header-inner">
    <a href="/" class="logo">Veen</a>
    <nav class="nav" aria-label="Main navigation">
      <a href="/" class="nav-link">Daily</a>
      <a href="/weekly" class="nav-link">Weekly</a>
      <a href="/monthly" class="nav-link">Monthly</a>
    </nav>
  </div>
</header>

<main class="main">
  {@render children()}
</main>

<style>
  .header {
    position: sticky;
    top: 0;
    z-index: 100;
    background: color-mix(in srgb, var(--bg) 85%, transparent);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
  }

  .header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 3.25rem;
  }

  .logo {
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--accent-hover);
    letter-spacing: -0.02em;
    text-decoration: none;
  }

  .logo:hover {
    color: var(--text);
    text-decoration: none;
  }

  .nav {
    display: flex;
    gap: 0.25rem;
  }

  .nav-link {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-muted);
    padding: 0.35rem 0.75rem;
    border-radius: var(--radius);
    text-decoration: none;
    transition: color 0.15s ease, background 0.15s ease;
  }

  .nav-link:hover {
    color: var(--text);
    background: var(--bg-card);
    text-decoration: none;
  }

  .main {
    padding: 2rem 0 4rem;
  }
</style>
