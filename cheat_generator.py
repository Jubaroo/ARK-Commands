import sys
import os
import json
import requests
from bs4 import BeautifulSoup
from PyQt5 import QtWidgets, QtGui, QtCore

# Determine base path (supports PyInstaller)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(__file__)

# --- cache files & base URL ---
CACHE_ITEMS_FILE      = os.path.join(BASE_PATH, "items_cache.json")
CACHE_CREATURES_FILE  = os.path.join(BASE_PATH, "creatures_cache.json")
CACHE_LOCATIONS_FILE  = os.path.join(BASE_PATH, "locations_cache.json")
CACHE_COLORS_FILE     = os.path.join(BASE_PATH, "colors_cache.json")
CACHE_COMMANDS_FILE   = os.path.join(BASE_PATH, "commands_cache.json")
BASE_URL              = "https://arkids.net"

# --- loaders ---
def load_items():
    try:
        return json.load(open(CACHE_ITEMS_FILE, encoding="utf-8"))
    except:
        pass
    items, page = [], 1
    while True:
        url = BASE_URL + ("/items" if page == 1 else f"/items/page/{page}")
        r = requests.get(url)
        if r.status_code != 200: break
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table: break
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 4: continue
            name = cols[1].get_text(strip=True)
            syntax = cols[3].get_text(strip=True).split()
            gfi_id = syntax[2] if len(syntax) >= 3 else cols[2].get_text(strip=True)
            items.append({"name": name, "id": gfi_id})
        if not soup.find("a", string="Next Page"): break
        page += 1
    with open(CACHE_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return items

def load_creatures():
    if os.path.exists(CACHE_CREATURES_FILE):
        try: return json.load(open(CACHE_CREATURES_FILE, encoding="utf-8"))
        except: pass
    creatures, page = [], 1
    while True:
        url = BASE_URL + ("/creatures" if page == 1 else f"/creatures/page/{page}")
        r = requests.get(url)
        if r.status_code != 200: break
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table: break
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 3: continue
            name = cols[1].get_text(strip=True)
            raw  = cols[2].get_text(strip=True)
            cls  = raw.split(".")[-1].strip("'\"")
            creatures.append({"name": name, "class": cls})
        if not soup.find("a", string="Next Page"): break
        page += 1
    with open(CACHE_CREATURES_FILE, "w", encoding="utf-8") as f:
        json.dump(creatures, f, ensure_ascii=False, indent=2)
    return creatures

def load_locations():
    if os.path.exists(CACHE_LOCATIONS_FILE):
        try: return json.load(open(CACHE_LOCATIONS_FILE, encoding="utf-8"))
        except: pass
    locations = []
    r = requests.get(f"{BASE_URL}/locations")
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 6: continue
        name  = cols[2].get_text(strip=True)
        coord = cols[5].get_text(strip=True).replace("cheat setplayerpos ", "").strip()
        locations.append({"name": name, "code": coord})
    with open(CACHE_LOCATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)
    return locations

def load_colors():
    if os.path.exists(CACHE_COLORS_FILE):
        try: return json.load(open(CACHE_COLORS_FILE, encoding="utf-8"))
        except: pass
    r = requests.get(f"{BASE_URL}/color-ids")
    soup = BeautifulSoup(r.text, "html.parser")
    select = soup.find("select")
    colors = []
    for opt in select.find_all("option"):
        val, hexcol = opt["value"], opt.get("data-color")
        name = opt.get_text(strip=True).rsplit("(", 1)[0].strip()
        colors.append({"name": name, "id": val, "hex": hexcol})
    with open(CACHE_COLORS_FILE, "w", encoding="utf-8") as f:
        json.dump(colors, f, ensure_ascii=False, indent=2)
    return colors

def load_commands():
    if os.path.exists(CACHE_COMMANDS_FILE):
        try: return json.load(open(CACHE_COMMANDS_FILE, encoding="utf-8"))
        except: pass
    cmds, page = [], 1
    while True:
        url = BASE_URL + ("/commands" if page == 1 else f"/commands/page/{page}")
        r = requests.get(url)
        if r.status_code != 200: break
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", id="table-view")
        if not table: break
        for tr in table.find("tbody").find_all("tr", recursive=False):
            tds = tr.find_all("td", recursive=False)
            if len(tds) < 4: continue
            name = tds[0].get_text(strip=True)
            desc = tds[1].get_text(strip=True)
            box = tds[3].find("div", class_="ac-code-showcase__box")
            if not box: continue
            raw    = " ".join(box.stripped_strings)
            syntax = " ".join(raw.split())
            cmds.append({"name": name, "description": desc, "syntax": syntax})
        if not soup.find("a", string="Next Page"): break
        page += 1
    with open(CACHE_COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(cmds, f, ensure_ascii=False, indent=2)
    return cmds

# --- Main GUI class ---
class CheatApp(QtWidgets.QWidget):
    def __init__(self, items, creatures, locations, colors, commands):
        super().__init__()
        self.items, self.creatures = items, creatures
        self.locations, self.colors = locations, colors
        self.commands = commands
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ARK Ascended Cheat Generator")
        main_layout = QtWidgets.QVBoxLayout(self)
        tabs = QtWidgets.QTabWidget(); main_layout.addWidget(tabs)

        # -- Items tab --
        items_tab = QtWidgets.QWidget(); items_layout = QtWidgets.QVBoxLayout(items_tab)
        self.search_items = QtWidgets.QLineEdit(placeholderText="Filter items…"); items_layout.addWidget(self.search_items)
        self.dd_items     = QtWidgets.QComboBox(); items_layout.addWidget(self.dd_items)
        grp = QtWidgets.QGroupBox("Item Options"); form = QtWidgets.QFormLayout(grp)
        self.qty = QtWidgets.QSpinBox(); self.qty.setRange(1,9999); self.qty.setValue(1)
        self.qual= QtWidgets.QSpinBox(); self.qual.setRange(0,100); self.qual.setValue(1)
        self.bp = QtWidgets.QCheckBox("Blueprint")
        form.addRow("Quantity:", self.qty); form.addRow("Quality: ", self.qual); form.addRow("", self.bp)
        items_layout.addWidget(grp); tabs.addTab(items_tab, "Items")

        # -- Creatures tab --
        creatures_tab = QtWidgets.QWidget(); creatures_layout = QtWidgets.QVBoxLayout(creatures_tab)
        self.search_creatures = QtWidgets.QLineEdit(placeholderText="Filter creatures…"); creatures_layout.addWidget(self.search_creatures)
        self.dd_creatures = QtWidgets.QComboBox(); creatures_layout.addWidget(self.dd_creatures)
        tabs.addTab(creatures_tab, "Creatures")

        # -- Locations tab --
        locations_tab = QtWidgets.QWidget(); loc_layout = QtWidgets.QVBoxLayout(locations_tab)
        self.search_locations = QtWidgets.QLineEdit(placeholderText="Filter locations…"); loc_layout.addWidget(self.search_locations)
        self.dd_locations = QtWidgets.QComboBox(); loc_layout.addWidget(self.dd_locations)
        tabs.addTab(locations_tab, "Locations")

        # -- Colors tab --
        colors_tab = QtWidgets.QWidget(); col_layout = QtWidgets.QVBoxLayout(colors_tab)
        self.search_colors = QtWidgets.QLineEdit(placeholderText="Filter colors…"); col_layout.addWidget(self.search_colors)
        self.dd_colors = QtWidgets.QComboBox(); col_layout.addWidget(self.dd_colors)
        tabs.addTab(colors_tab, "Colors")

        # -- Commands tab --
        commands_tab = QtWidgets.QWidget(); com_layout = QtWidgets.QVBoxLayout(commands_tab)
        self.search_commands = QtWidgets.QLineEdit(placeholderText="Filter commands…"); com_layout.addWidget(self.search_commands)
        self.dd_commands = QtWidgets.QComboBox(); com_layout.addWidget(self.dd_commands)
        self.desc_lbl = QtWidgets.QLabel(wordWrap=True); com_layout.addWidget(self.desc_lbl)
        tabs.addTab(commands_tab, "Commands")

        # -- Generate & copy --
        ctrl = QtWidgets.QHBoxLayout()
        self.gen = QtWidgets.QPushButton("Generate Code", icon=QtGui.QIcon.fromTheme("code-run"))
        self.out = QtWidgets.QLineEdit(readOnly=True)
        self.cp  = QtWidgets.QPushButton("Copy", icon=QtGui.QIcon.fromTheme("edit-copy"))
        ctrl.addWidget(self.gen); ctrl.addWidget(self.out); ctrl.addWidget(self.cp)
        main_layout.addLayout(ctrl)

        # connections
        self.search_items.textChanged.connect(self.update_items)
        self.search_creatures.textChanged.connect(self.update_creatures)
        self.search_locations.textChanged.connect(self.update_locations)
        self.search_colors.textChanged.connect(self.update_colors)
        self.search_commands.textChanged.connect(self.update_commands)
        self.dd_commands.currentIndexChanged.connect(self.update_command_desc)
        self.gen.clicked.connect(self.generate_code)
        self.cp.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(self.out.text()))

        # initial populate
        self.update_items(); self.update_creatures()
        self.update_locations(); self.update_colors()
        self.update_commands()

    # update functions...
    def update_items(self):
        term = self.search_items.text().lower()
        self.dd_items.clear()
        for i in self.items:
            if term in i["name"].lower():
                self.dd_items.addItem(i["name"], i["id"])

    def update_creatures(self):
        term = self.search_creatures.text().lower()
        self.dd_creatures.clear()
        for c in self.creatures:
            if term in c["name"].lower():
                self.dd_creatures.addItem(c["name"], c["class"])

    def update_locations(self):
        term = self.search_locations.text().lower()
        self.dd_locations.clear()
        for l in self.locations:
            if term in l["name"].lower():
                self.dd_locations.addItem(l["name"], l["code"])

    def update_colors(self):
        term = self.search_colors.text().lower()
        self.dd_colors.clear()
        for c in self.colors:
            if term in c["name"].lower():
                pix = QtGui.QPixmap(16,16); pix.fill(QtGui.QColor(c["hex"]))
                self.dd_colors.addItem(QtGui.QIcon(pix), c["name"], c)

    def update_commands(self):
        term = self.search_commands.text().lower()
        self.dd_commands.clear()
        for cmd in self.commands:
            if term in cmd["name"].lower() or term in cmd["description"].lower():
                self.dd_commands.addItem(cmd["name"], cmd)

    def update_command_desc(self):
        data = self.dd_commands.currentData()
        self.desc_lbl.setText(data["description"] if data else "")

    def generate_code(self):
        idx = self.findChild(QtWidgets.QTabWidget).currentIndex()
        if idx == 0:
            gid = self.dd_items.currentData()
            self.out.setText(f"cheat gfi {gid} {self.qty.value()} {self.qual.value()} {int(self.bp.isChecked())}")
        elif idx == 1:
            cls = self.dd_creatures.currentData()
            self.out.setText(f"admincheat Summon {cls}")
        elif idx == 2:
            x,y,z = self.dd_locations.currentData().split()
            self.out.setText(f"cheat setplayerpos {x} {y} {z}")
        elif idx == 3:
            c = self.dd_colors.currentData()
            self.out.setText(f"{c['id']} ({c['hex']})")
        else:
            data = self.dd_commands.currentData()
            self.out.setText(data["syntax"] if data else "")

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    dark = QtGui.QPalette()
    dark.setColor(QtGui.QPalette.Window, QtGui.QColor(45,45,45))
    dark.setColor(QtGui.QPalette.WindowText, QtGui.QColor(220,220,220))
    dark.setColor(QtGui.QPalette.Base, QtGui.QColor(35,35,35))
    dark.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(55,55,55))
    dark.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(220,220,220))
    dark.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(20,20,20))
    dark.setColor(QtGui.QPalette.Text, QtGui.QColor(220,220,220))
    dark.setColor(QtGui.QPalette.Button, QtGui.QColor(60,60,60))
    dark.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(220,220,220))
    dark.setColor(QtGui.QPalette.Highlight, QtGui.QColor(38,79,120))
    dark.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(220,220,220))
    app.setPalette(dark)

    # show splash
    splash_pix = QtGui.QPixmap(300,200)
    splash_pix.fill(QtGui.QColor(60,60,60))
    splash = QtWidgets.QSplashScreen(splash_pix)
    splash.showMessage("Loading data…", QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom, QtCore.Qt.white)
    splash.show()
    app.processEvents()

    # load everything
    items     = load_items()
    creatures = load_creatures()
    locations = load_locations()
    colors    = load_colors()
    commands  = load_commands()

    # launch main window
    splash.finish(None)
    w = CheatApp(items, creatures, locations, colors, commands)
    w.resize(700, 500)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
