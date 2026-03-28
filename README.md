# WealthCapital Content Engine

An end-to-end creator intelligence platform built for a VC-backed investment firm. It automates the discovery, scraping, enrichment, and analysis of LinkedIn thought leaders relevant to the startup and venture capital ecosystem.

## What it does

The pipeline ingests LinkedIn creator profiles and their posts via PhantomBuster, runs each post through an AI enrichment layer (Anthropic Claude / Google Gemini) to extract structured signals — hook style, engagement score, tone, topic, shareability — then stores everything in PostgreSQL and surfaces it through a custom analytics dashboard.

The dashboard gives the team a live view of which creators are driving the most engagement, what content formats and hook styles perform best, and which posts are worth putting in a swipe file for content inspiration.

## Architecture

```
PhantomBuster (scrape) → Python pipeline → AI enrichment → PostgreSQL + Excel
                                                                    ↓
                                                         Next.js dashboard (Vercel)
```

**Pipeline** (`/scripts`)
- Scrapes creator profiles and recent posts via PhantomBuster API
- Enriches each post with Claude Haiku / Gemini 2.0 Flash — classifying topic, hook style, hook strength (1–5), engagement score, tone, relevance, and shareability
- Computes creator-level engagement rates and credibility scores
- Writes output to structured Excel files and ingests into PostgreSQL via Prisma

**Dashboard** (`/dashboard`)
- Next.js 16 app deployed on Vercel
- 4 tabs: Creators, Posts, Analytics, Insights
- Analytics tab: engagement by format, hook style performance, topic distribution, hook strength vs. engagement scatter plot — all built with pure SVG (no chart library dependency)
- Insights tab: auto-derives Adopt / Adapt / Avoid recommendations and key takeaways directly from the data
- PIN-gated with server-side validation so credentials never touch the client bundle

## Tech Stack

| Layer | Technologies |
|---|---|
| Scraping | PhantomBuster API, Python |
| AI Enrichment | Anthropic Claude (Haiku), Google Gemini 2.0 Flash |
| Storage | PostgreSQL (Supabase), Prisma ORM |
| Dashboard | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| Deployment | Vercel |
| Data | openpyxl, xlsx, psycopg2 |
