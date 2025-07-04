# Claude Project Manifest: MommyNature

## 📍 Overview

Use python3 to run scripts.

MommyNature is a web app that helps users discover scenic nature spots near them, curated from Reddit posts and enriched with data from Google Places. It presents the results on an interactive map with GPT-powered summaries and user-friendly filters (mood, time, pet-friendly, etc.).

---

## 📁 Project Structure

```
mommy-nature/
├── backend/
│   ├── main.py               # FastAPI server, handles endpoints for scraping, GPT, places data
│   ├── reddit_scraper.py     # Uses PRAW to collect relevant location posts from subreddits
│   ├── gpt_summary.py        # Calls LLM (OpenAI or Claude) to generate warm summaries
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx           # Main Leaflet map UI
│   └── package.json
├── supabase/
│   ├── schema.sql            # PostGIS-enabled schema for locations, users, pins
│   └── config.ts             # Supabase client config
├── claude.md                 # This file
├── README.md
└── .env
```

---

## 💡 Key Features / Logic

* Scraper pulls posts from r/sanfrancisco, r/hiking, etc., looking for geotaggable locations
* FastAPI endpoints provide frontend with enriched location data
* Supabase stores locations with PostGIS spatial fields for proximity filtering
* GPT or Claude used to generate “Mommy-style” summaries (e.g., advice, vibe)
* React frontend with Leaflet displays clickable map markers
* Future: Auth + saved maps + offline access + nature “packs”

---

## 🔧 Current Challenges / Help Needed

* [ ] Supabase: Writing spatial queries (e.g., “find spots within 30 miles”)
* [ ] GPT summaries: Make tone warm + useful + mom-like
* [ ] Image enrichment: Pull public IG photos for better preview
* [ ] Pricing strategy: what would make someone pay \$5/month?

---

## 🧠 Claude, Please Help Me With...

1. Improving `reddit_scraper.py` to filter only posts that have clear location references (lat/lng or known place names).
2. Writing GPT prompts that generate practical, friendly, “mom-style” tips for each location.
3. Designing a pricing page and a compelling Pro plan.
4. Writing Supabase RLS rules so users only see their own saved maps.

---

*Thanks, Claude!*
