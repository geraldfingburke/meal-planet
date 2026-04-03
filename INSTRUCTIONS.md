# Meal Planet — Step-by-Step Setup Instructions

These instructions are written for people who have **never used a terminal, Docker, or code before**. Follow every step exactly as written and you'll have Meal Planet running on your computer.

---

## Table of Contents

1. [What You'll Need](#what-youll-need)
2. [Step 1 — Install Docker Desktop](#step-1--install-docker-desktop)
3. [Step 2 — Get a Google Gemini API Key (Free)](#step-2--get-a-google-gemini-api-key-free)
4. [Step 3 — Download Meal Planet](#step-3--download-meal-planet)
5. [Step 4 — Create the Settings File](#step-4--create-the-settings-file)
6. [Step 5 — Start Meal Planet](#step-5--start-meal-planet)
7. [Step 6 — Seed the Database](#step-6--seed-the-database)
8. [Step 7 — Open the App](#step-7--open-the-app)
9. [How to Stop Meal Planet](#how-to-stop-meal-planet)
10. [How to Start It Again Later](#how-to-start-it-again-later)
11. [How to Update Meal Planet](#how-to-update-meal-planet)
12. [Using the App](#using-the-app)
13. [Troubleshooting](#troubleshooting)

---

## What You'll Need

- A computer running **Windows 10/11**, **macOS**, or **Linux**
- An internet connection (for initial setup and recipe importing)
- About **4 GB** of free disk space
- About **10–15 minutes** for the initial setup

---

## Step 1 — Install Docker Desktop

Docker is the tool that runs Meal Planet. Think of it like a container that holds everything the app needs so you don't have to install anything else.

### Windows

1. Go to [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Click the **"Download for Windows"** button.
3. Open the downloaded file (`Docker Desktop Installer.exe`) and follow the installer prompts.
4. When it asks about **WSL 2** — check that box. This is required.
5. After installation finishes, **restart your computer** when prompted.
6. After restarting, Docker Desktop should open automatically. If not, find **Docker Desktop** in your Start Menu and open it.
7. Wait until the Docker icon in your system tray (bottom-right of your screen, near the clock) shows a **green "running"** status. This may take a minute.
8. You may see a prompt to accept the Docker terms of service — click **Accept**.

### macOS

1. Go to [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Click **"Download for Mac"**. Choose **Apple Silicon** if you have an M1/M2/M3/M4 Mac, or **Intel** if you have an older Mac. (Open **Apple Menu → About This Mac** to check.)
3. Open the downloaded `.dmg` file and drag **Docker** into your **Applications** folder.
4. Open **Docker** from Applications. Allow it when macOS asks for permission.
5. Wait for the whale icon in your menu bar to stop animating — that means Docker is ready.

### Linux

1. Follow the official instructions for your distribution: [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)
2. Also install Docker Compose if it didn't come bundled (most modern installations include it).

---

## Step 2 — Get a Google Gemini API Key (Free)

Meal Planet uses Google's Gemini AI to read recipe websites and estimate grocery prices. You need a free API key.

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your **Google account** (the same kind of account you use for Gmail or YouTube).
3. Click **"Create API key"**.
4. A long string of letters and numbers will appear (it looks something like `AIzaSyD...`). This is your API key.
5. **Copy it** and save it somewhere temporarily — you'll paste it in the next step. A sticky note on your desktop, a text file, or just keep this browser tab open.

> **Important:** This key is free for personal use within Google's generous free tier, which is more than enough for Meal Planet.

---

## Step 3 — Download Meal Planet

You need to get the Meal Planet files onto your computer.

### Option A: Download as a ZIP (Easiest)

1. Go to [https://github.com/geraldfingburke/meal-planet](https://github.com/geraldfingburke/meal-planet)
2. Click the green **"Code"** button near the top-right.
3. Click **"Download ZIP"**.
4. Find the downloaded ZIP file (usually in your **Downloads** folder).
5. **Extract / unzip** the file:
   - **Windows:** Right-click the ZIP → **Extract All...** → click **Extract**.
   - **macOS:** Double-click the ZIP file.
6. You should now have a folder called `meal-planet-main`. You can move it anywhere you like (your Desktop, Documents folder, etc.).

### Option B: Using Git (If You Already Have It)

If you already have Git installed (you'd know), open a terminal and run:

```
git clone https://github.com/geraldfingburke/meal-planet.git
```

---

## Step 4 — Create the Settings File

Meal Planet needs a small settings file to know your API key and database passwords.

### Windows

1. Open the `meal-planet-main` folder (or `meal-planet` if you used Git).
2. You need to create a new file called `.env` (yes, the name starts with a dot). Here's how:
   - **Right-click** inside the folder → **New** → **Text Document**.
   - Name it `.env` (make sure it's not `.env.txt` — see Troubleshooting if Windows adds `.txt`).
3. **Right-click** the `.env` file → **Open with** → **Notepad** (or any text editor).
4. Paste the following text **exactly as shown**, but replace `your_gemini_api_key` with the API key you copied in Step 2. You can also change `changeme` to any password you like — just make sure the same password appears in both lines where it shows up:

```
POSTGRES_USER=mealplanet
POSTGRES_PASSWORD=changeme
POSTGRES_DB=mealplanet
DATABASE_URL=postgresql+asyncpg://mealplanet:changeme@db:5432/mealplanet
REDIS_URL=redis://redis:6379/0
BACKEND_CORS_ORIGINS=http://localhost:3000
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=change-this-in-production
NEXT_PUBLIC_API_URL=http://localhost:8000
```

5. **Save the file** (Ctrl+S) and close Notepad.

> **Critical:** If you change `changeme` to a different password, it must be the same in both the `POSTGRES_PASSWORD` line AND inside the `DATABASE_URL` line (the part between `://mealplanet:` and `@db`). For example, if your password is `MyPassword123`:
>
> - `POSTGRES_PASSWORD=MyPassword123`
> - `DATABASE_URL=postgresql+asyncpg://mealplanet:MyPassword123@db:5432/mealplanet`

### macOS

1. Open the `meal-planet-main` folder in **Finder**.
2. Open **TextEdit** (find it in Applications, or press Cmd+Space and type "TextEdit").
3. In TextEdit, go to the menu bar: **Format → Make Plain Text** (this is important).
4. Paste the same text shown above (the block starting with `POSTGRES_USER=mealplanet`), replacing `your_gemini_api_key` with your actual key.
5. **Save** the file (Cmd+S):
   - Navigate to your `meal-planet-main` folder.
   - Name the file `.env` (yes, starting with a dot).
   - If macOS warns that names starting with a dot are reserved, click **"Use ."**

---

## Step 5 — Start Meal Planet

This is where Docker builds and starts all the pieces of the app. The first time takes 3–5 minutes because it downloads and builds everything. After that, it starts in seconds.

### Windows

1. Open the `meal-planet-main` folder in File Explorer.
2. Click in the **address bar** at the top of the File Explorer window (where it shows the path), type `cmd`, and press **Enter**. This opens a command prompt pointed at the right folder.
3. Type this command and press **Enter**:

```
docker compose up --build
```

4. You will see a LOT of text scrolling past. This is normal. Wait until you see lines that say things like:
   - `backend-1   | Uvicorn running on http://0.0.0.0:8000`
   - `frontend-1  | Ready`

   This means everything is running!

> **Do not close this window.** Meal Planet runs as long as this window stays open. You can minimize it.

### macOS

1. Open **Terminal** (press Cmd+Space, type "Terminal", press Enter).
2. Type `cd ` (with a space after it), then **drag the `meal-planet-main` folder from Finder into the Terminal window**. This fills in the path automatically. Press **Enter**.
3. Type and run:

```
docker compose up --build
```

4. Wait for the same "Uvicorn running" / "Ready" messages as described above.

### Linux

1. Open a terminal, navigate to the folder, and run `docker compose up --build`.

---

## Step 6 — Seed the Database

This step creates the initial data Meal Planet needs (a default family record and common cooking ingredients). **You only need to do this once, the very first time.**

### Open a Second Terminal

Leave the first terminal running (that's running the app). You need a second one.

#### Windows

- Open a **new** Command Prompt window (Start Menu → search "cmd" → open it).
- Navigate to the folder by typing:
  ```
  cd path\to\meal-planet-main
  ```
  Replace `path\to\meal-planet-main` with the actual location. For example, if it's on your Desktop:
  ```
  cd %USERPROFILE%\Desktop\meal-planet-main
  ```

#### macOS

- Open a new Terminal window (Cmd+N or Shell → New Window).
- Navigate by dragging the folder in again, or type:
  ```
  cd ~/Desktop/meal-planet-main
  ```

### Run the Seed Command

In this second terminal, type and run:

```
docker compose exec backend python -m app.seed
```

You should see a brief output confirming the seed was successful. If it says something like "Family created" or finishes without errors, you're all set.

**You can close this second terminal now.** You won't need it again unless you're troubleshooting.

---

## Step 7 — Open the App

1. Open your web browser (Chrome, Firefox, Edge, Safari — any will work).
2. Go to: **[http://localhost:3000](http://localhost:3000)**

You should see the Meal Planet dashboard. You're done with setup!

---

## How to Stop Meal Planet

When you're done using Meal Planet for the day:

1. Go to the terminal window where all the text is scrolling (the one from Step 5).
2. Press **Ctrl+C** on your keyboard (hold the Ctrl key and press the C key).
3. Wait a few seconds for everything to stop gracefully.

Your data is saved. Nothing is lost when you stop it.

---

## How to Start It Again Later

1. Make sure **Docker Desktop is running** (open it from your Start Menu / Applications if it isn't).
2. Open a terminal / command prompt in the `meal-planet-main` folder (same as Step 5).
3. Type and run:

```
docker compose up
```

Note: you don't need `--build` this time (that was only for the first time, or after updates). It starts much faster now.

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## How to Update Meal Planet

If a new version is released:

### If You Downloaded the ZIP

1. Stop Meal Planet (Ctrl+C in the terminal).
2. Download the new ZIP from GitHub.
3. Extract it to the same location, overwriting the old files.
4. **Copy your `.env` file** from the old folder into the new one (so you don't lose your settings).
5. Start again with `docker compose up --build`.

### If You Used Git

1. Stop Meal Planet (Ctrl+C in the terminal).
2. In the terminal, navigate to the folder and run:
   ```
   git pull
   docker compose up --build
   ```

---

## Using the App

Once Meal Planet is running and you've opened it in your browser, here's how to use each part.

### Dashboard (Home Page)

The first page you see. It provides a quick overview. Use the left sidebar to navigate to other sections.

### Recipes

This is where you manage your collection of recipes.

- **Import a Recipe from a Website:** At the top of the Recipes page, paste a recipe URL (from any cooking website) into the text box and click **Import**. The AI will read the page and extract the recipe automatically — title, ingredients, instructions, tags, and category. This takes about 10–20 seconds. A progress indicator will appear.
- **Add a Recipe Manually:** Click **"Add Recipe"** in the top-right corner. Fill in the title, category (breakfast/lunch/dinner/dessert/any), servings, ingredients, instructions, and tags.
- **View a Recipe:** Click on any recipe card or the **View** button to see the full recipe with ingredients and instructions.
- **Edit a Recipe:** On the recipe detail page, click **Edit** to change the title, category, instructions, or tags. Click **Save** when done.
- **Edit Tags Inline:** On a recipe's detail page, hover over any tag and click the **✕** to remove it. Use the "Add a tag" input at the bottom to add new ones.
- **Delete a Recipe:** Click the red **Delete** button on a recipe card. You'll be asked to confirm.
- **Scale Servings:** On the recipe detail page, change the number in the "Servings" field. All ingredient quantities will recalculate automatically.

### Planner

The weekly meal planner. This is where you decide what to eat each day.

- **Navigate Weeks:** Use the **← Prev** and **Next →** buttons to move between weeks. Click **Today** to jump back to the current week.
- **Add a Meal:** Click **"+ add"** under any meal slot (breakfast, lunch, or dinner for any day). A search popup appears — type to find a recipe, then click it to assign it.
- **Set Servings:** Each meal shows how many servings it's set to. Click the servings number on any meal to change it.
- **Default Servings:** The **"Default Servings"** number at the top of the page sets the starting number for newly added meals. Change it before adding meals if you want a different default.
- **Fill Week:** Click the **"Fill Week"** button to automatically fill in empty meal slots. A dialog lets you choose which meal types to fill (breakfast, lunch, dinner). The app picks category-appropriate recipes you haven't used recently.
- **Remove a Meal:** Hover over a meal and click the **✕** that appears.
- **Export to Calendar:** Click **"Export .ics"** to download a calendar file you can import into Google Calendar, Outlook, or Apple Calendar.

### Grocery List

Generates a shopping list from your planned meals.

- **Generate a List:** Pick a date range (or use the **1 Week** / **2 Weeks** buttons for quick selection), then click **"Generate Shopping List"**. The AI creates a deduplicated, organized list with estimated Walmart prices.
- **Check Off Items:** While shopping, click the checkbox next to each item to cross it off.
- **Print:** Click **Print** to print the list.
- **Save as Text:** Click **"Save as Text"** to download the list as a plain text file.
- **View Previous Lists:** Click **"See Older Lists"** to browse your previously generated grocery lists. Click any of them to view it.
- **Latest List on Load:** When you visit the Grocery List page, it automatically loads your most recently generated list.

### Spinner

Can't decide what to cook? The Dinner Spinner picks a random recipe for you.

- It favors recipes you **haven't cooked recently**, so you get variety.
- You can **filter by tags** (like "chicken", "quick", "vegetarian") to narrow down the options before spinning.

### Reports

A dashboard showing insights about your meal planning habits and spending.

- **Spending Over Time** — See how your grocery spending has changed from list to list.
- **Top 5 Recipes** — The recipes you've planned the most.
- **Most Expensive Day** — The single highest-cost day based on recipe cost-per-serving data.
- **Spending by Category** — Average and total spending broken down by grocery category (produce, dairy, meat, etc.).

> **Note:** Reports data comes from generated grocery lists. You'll need to generate at least a few lists before the reports become meaningful.

---

## Troubleshooting

### Windows says the file is `.env.txt` instead of `.env`

By default, Windows hides file extensions. To fix this:

1. In File Explorer, click **View** in the top menu.
2. Check **File name extensions** (or on Windows 11, click **Show → File name extensions**).
3. Now you can see the full name. Rename the file from `.env.txt` to `.env`.
4. Windows will warn you about changing the extension — click **Yes**.

### `docker compose` says "command not found"

- Make sure Docker Desktop is running. Look for the whale icon in your system tray (Windows) or menu bar (macOS).
- If you installed Docker very recently, try **restarting your computer**.
- On older systems, try `docker-compose` (with a hyphen) instead of `docker compose` (with a space).

### The app shows a blank page or "connection refused"

- Check that both the backend and frontend are running. Look at the terminal — you should see log messages from both.
- Make sure you're going to `http://localhost:3000` (not `https`).
- Wait 30 seconds after starting — sometimes the frontend takes a moment to compile on the first visit.

### "Gemini API" errors when importing a recipe

- Check that your `GEMINI_API_KEY` in the `.env` file is correct (no extra spaces or quotes around it).
- Make sure you have internet access.
- The free tier has rate limits. If you import many recipes rapidly, wait a minute and try again.

### The database seed step fails

- Make sure the app is fully running first (wait for the "Uvicorn running" message in the terminal before running the seed command).
- Make sure you're using a **second** terminal window, not the one that's running the app.

### I want to erase everything and start fresh

1. Stop Meal Planet (Ctrl+C).
2. Run: `docker compose down -v` (the `-v` flag deletes the database).
3. Start again with `docker compose up --build`.
4. Run the seed command again (Step 6).
