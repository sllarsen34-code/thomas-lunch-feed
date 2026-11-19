# Thomas Elementary automatic lunch calendar

Creates a rolling ~70-day all-day lunch calendar from Gretna Public Schools' LINQ Connect API.

## Setup

1. Create a **public** GitHub repository (e.g., `thomas-lunch-feed`).
2. Upload `generate.py` and `.github/workflows/update.yml`, preserving the folder structure. You can also upload this entire extracted folder using GitHub's web interface or Git.
3. Under **Settings → Pages**, select **Source: GitHub Actions**.
4. Under **Actions**, select **Update Thomas Elementary lunch calendar → Run workflow**.
5. When the workflow succeeds, open `https://YOUR-USERNAME.github.io/thomas-lunch-feed/lunch.ics` and confirm it starts with `BEGIN:VCALENDAR` and includes `BEGIN:VEVENT`.
6. In the Skylight app, go to **Synced Calendars → Sync new calendar → Calendar URL** and enter the URL above. Assign the desired profile/color if offered.

## Notes

- GitHub Actions and Pages may have usage restrictions and limits. The scheduled workflow runs once daily, typically around 6:17 a.m. CST / 7:17 a.m. CDT, but GitHub schedules are not guaranteed to run exactly on time.
- **If the workflow fails with HTTP 403 or 429, LINQ is blocking cloud access.** The project cannot guarantee a fully automatic feed until an authorized retrieval path is available. Don't publish a blank or stale menu as current.
- **The calendar URL is public**, as is the lunch menu. No child or account details are included.
- This uses LINQ's currently documented `FamilyMenuSessions → MenuPlans → Days → MenuMeals → RecipeCategories → Recipes` structure. It has not been tested against a live Thomas Elementary response in this environment. Inspect the first generated entries to confirm categories and date formatting.
- To avoid an empty feed, the generator fails if it finds no lunch entries. GitHub Pages may retain its previous successful deployment; check the workflow periodically.
- Published lunch menu content is subject to school changes and LINQ availability. Skylight controls how often it refreshes subscriptions.
