# Real Estate Data Enhancement & Marine Debris Data Collection Service

## Author
**Deus Francis Kandamali**  
PhD Candidate, Electrical & Computer Engineering  
University of Georgia  

---

## Overview

This repository demonstrates data-driven applications developed using modern data science, geospatial analysis, and web technologies. It contains two independent components:

1. Real Estate Data Enhancement Pipeline — a Jupyter-based workflow integrating geospatial and weather data  
2. Marine Debris Data Collection Service — a web application for environmental reporting and data management  

These projects illustrate how computational tools can support evidence-based decision-making and environmental monitoring.

---

## Part 1 — Real Estate Data Enhancement

A data processing pipeline that enriches real estate records with geospatial coordinates and historical weather information.

### Dataset

- Original dataset: Connecticut real estate transactions (2001–2020)  
- Filtered subset: Mondays in April 2019  
- Generated output: `enhanced_real_estate_april_2019.csv`  

### Processing Workflow

- Filtered transactions using Pandas  
- Geocoded addresses lacking coordinates using the Nominatim public API  
- Retrieved historical weather data using the Open-Meteo Archive API  
- Implemented caching to reduce redundant API calls  
- Generated visualizations of geographic distribution  

### Output

- Enhanced dataset with coordinates and weather attributes  
- Scatterplot visualization of geocoded properties  

---

## Part 2 — Marine Debris Data Collection Service

A Flask-based web application designed to collect, classify, and store marine debris reports submitted by users.

👉 **Live demo:** https://marinedebris.dynv6.net/  
👉 **Video overview:** https://youtu.be/NYdH0JeJdPc  

### Key Features

- User submission form for:
  - Photo upload  
  - Text description  
  - GPS coordinates  

- Automated processing:
  - Image classification using Google Gemini  
  - Translation of non-English descriptions into English  
  - Reverse geocoding of coordinates  
  - Data validation  

### Storage

- SQLite database (`database.db`)  
- Cached geocoding results (`geocode_cache.json`)  

### Classification Categories

Based on NOAA marine debris classifications:

- Plastic  
- Metal  
- Glass  
- Rubber  
- Processed Wood  
- Fabric  
- Other  

### System Components

- Flask web framework  
- Google Generative AI (Gemini) for classification and translation  
- Nominatim API for geospatial processing  
- NGINX reverse proxy  
- SSL certificates via Certbot  
- DNS-based deployment  

### Error Handling

The system validates:

- Image file integrity  
- Coordinate correctness  
- Debris relevance  
- API failures  

---

## ⚙️ Installation & Setup

Install dependencies:

