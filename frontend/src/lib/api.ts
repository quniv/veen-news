import { PUBLIC_DATA_BASE_URL } from '$env/static/public';
import type { Digest } from './types';

const BASE = PUBLIC_DATA_BASE_URL || '';

function dataUrl(path: string): string {
  return BASE ? `${BASE}/${path}` : `/${path}`;
}

export async function fetchLatest(): Promise<Digest> {
  const url = dataUrl('data/latest.json');
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`Failed to fetch latest digest: ${res.status}`);
  return res.json();
}

export async function fetchDigest(date: string): Promise<Digest> {
  const url = dataUrl(`data/daily/${date}.json`);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch digest for ${date}: ${res.status}`);
  return res.json();
}

export async function fetchIndex(): Promise<{
  updated_at: string | null;
  latest_date: string | null;
  daily: { date: string; path: string; article_count: number }[];
  weekly: { week: string; path: string; article_count: number }[];
  monthly: { month: string; path: string; article_count: number }[];
}> {
  const url = dataUrl('data/index.json');
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch index: ${res.status}`);
  return res.json();
}

export async function fetchWeekly(week: string): Promise<unknown> {
  const url = dataUrl(`data/weekly/${week}.json`);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch weekly recap: ${res.status}`);
  return res.json();
}

export async function fetchMonthly(month: string): Promise<unknown> {
  const url = dataUrl(`data/monthly/${month}.json`);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch monthly recap: ${res.status}`);
  return res.json();
}
