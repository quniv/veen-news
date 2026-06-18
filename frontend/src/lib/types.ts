export type Category =
  | 'technology'
  | 'ai'
  | 'devops'
  | 'world'
  | 'vietnam'
  | 'innovations'
  | 'robotics'
  | 'open_source';

export interface Article {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  category: Category;
  summary: string;
  score: number;
  cluster_id: string | null;
}

export interface Cluster {
  id: string;
  topic: string;
  summary: string;
  article_ids: string[];
  article_count: number;
}

export interface DigestStats {
  fetched: number;
  after_filter: number;
  published: number;
  clusters_formed: number;
  sources_crawled: number;
}

export interface DailyRecap {
  global_analysis: string;
  vietnam_analysis: string;
  watch_list: string;
  full_summary: string;
}

export interface Digest {
  generated_at: string | null;
  date: string | null;
  categories: Record<Category, Article[]>;
  clusters: Cluster[];
  daily_recap: DailyRecap | null;
  stats: DigestStats;
}

export const CATEGORY_LABELS: Record<Category, string> = {
  technology: 'Technology',
  ai: 'AI',
  devops: 'DevOps',
  world: 'World',
  vietnam: 'Vietnam',
  innovations: 'Innovations',
  robotics: 'Robotics',
  open_source: 'Open Source',
};

export const CATEGORIES: Category[] = [
  'technology',
  'ai',
  'devops',
  'world',
  'vietnam',
  'innovations',
  'robotics',
  'open_source',
];
