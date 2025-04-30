# ARK Ascended Cheat Generator

A simple, offline‑capable GUI tool for generating common "cheat" and admin commands in ARK: Survival Ascended. Quickly generate item `gfi` commands, creature spawns, teleport coordinates, color IDs, and full admin syntax without memorizing or typing long console calls.

---

## 📦 Features

- **Item GFI**  – Generate `cheat gfi <ItemID> <Quantity> <Quality> <Blueprint>` commands.
- **Creature Spawns** – One‑click `admincheat Summon <CreatureClass>` spawns.
- **Teleportation** – Copy‑ready `cheat setplayerpos <X> <Y> <Z>` coordinates.
- **Color IDs** – Browse and preview color IDs with hex values.
- **Full Commands** – Search and copy any admin/cheat syntax from the official Ark IDs list.
- **Local Caching** – Loads from bundled JSON caches for instant offline startup; no scraping required.
- **Dark Mode UI** – Eye‑friendly palette via Qt Fusion theme.

---

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/ark-cheat-generator.git
   cd ark-cheat-generator
   ```

2. **Install dependencies** (requires Python 3.7+)

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**

   ```bash
   python cheat_generator.py
   ```

> **Note:** This release bundles pre-built JSON caches; no network access or scraping is required at runtime.

---

## 📦 Building the EXE

To distribute as a standalone executable, use PyInstaller:

```powershell
pip install pyinstaller
python -m PyInstaller \
  --onefile \
  --windowed \
  --icon=icon.ico \
  --add-data "items_cache.json;." \
  --add-data "creatures_cache.json;." \
  --add-data "locations_cache.json;." \
  --add-data "colors_cache.json;." \
  --add-data "commands_cache.json;." \
  cheat_generator.py
```

After building, your EXE will already include all five JSON caches so no scraping is needed at runtime.

---

## ⚙️ Usage

1. Launch the app.
2. Select the appropriate tab (Items, Creatures, Locations, Colors, Commands).
3. Filter or browse the dropdown.
4. Click **Generate Code** to copy the console command to your clipboard.

---

## 📁 Project Structure

```
ark-cheat-generator/
├── items_cache.json       # Cached Item IDs
├── creatures_cache.json   # Cached Creature Classes
├── locations_cache.json   # Cached Teleport Coordinates
├── colors_cache.json      # Cached Color IDs
├── commands_cache.json    # Cached Admin Command Syntax
├── cheat_generator.py     # Main application script
└── requirements.txt       # Python dependencies
```

---

## 🤝 Contributing

Contributions and improvements are welcome:

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -m "Add awesome feature"`
4. Push to your branch: `git push origin feature/YourFeature`
5. Open a Pull Request.

Please ensure code styling consistency and update documentation as needed.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).
