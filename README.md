# 🚀 GitHub Trending Tracker

**Every Monday at 9AM: grab your coffee ☕ and discover the top 10 fastest-growing GitHub repositories of the week 🚀**

## 📌 Overview

This project automatically fetches the **top 10 fastest-growing GitHub repositories of the week** and updates the results every Monday using **GitHub Actions**.

It saves the results in:
- `trending_weekly.csv`
- `trending_weekly.json`

## ⚡ Features

- Automated weekly execution every Monday
- Tracks the top 10 trending GitHub repositories
- Saves results in CSV and JSON
- Built with Python and GitHub Actions

## ⚙️ How it works

1. A GitHub Actions workflow runs every Monday
2. The Python script fetches GitHub Trending repositories for the week
3. It extracts repository data like:
   - repository name
   - weekly stars
   - total stars
   - language
4. The results are saved into CSV and JSON files
5. The repo is updated automatically

## 📊 Example output

| Rank | Repository | Weekly Stars | Total Stars | Language |
|------|------------|--------------|-------------|----------|
| 1 | example/repo1 | 1200 | 54000 | Python |
| 2 | example/repo2 | 980 | 31000 | JavaScript |
| 3 | example/repo3 | 870 | 22000 | Go |

## 🛠️ Run locally

```bash
pip install -r requirements.txt
python github_fastest_growing.py
