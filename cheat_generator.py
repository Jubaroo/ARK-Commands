import sys
import os
import re
import json
from typing import Optional, List

import requests
from bs4 import BeautifulSoup
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QListWidget, QFormLayout, QListView

# Determine directory for resources when running packaged or in source
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_PATH = sys._MEIPASS  # PyInstaller bundle path
else:
    BASE_PATH = os.path.dirname(__file__)

# Paths for cached JSON data
CACHE_ITEMS_FILE     = os.path.join(BASE_PATH, "items_cache.json")
CACHE_CREATURES_FILE = os.path.join(BASE_PATH, "creatures_cache.json")
CACHE_LOCATIONS_FILE = os.path.join(BASE_PATH, "locations_cache.json")
CACHE_COLORS_FILE    = os.path.join(BASE_PATH, "colors_cache.json")
CACHE_COMMANDS_FILE  = os.path.join(BASE_PATH, "commands_cache.json")
CACHE_TAMING_FILE    = os.path.join(BASE_PATH, "taming_cache.json")
BASE_URL             = "https://arkids.net"


def _load_json(path: str) -> Optional[list]:
    """
    Load and parse JSON file at given path.
    Return list on success, or None if missing or invalid.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save_json(path: str, data) -> None:
    """
    Serialize Python data to JSON file with indentation.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _create_completer(items: List[str]) -> QtWidgets.QCompleter:
    """
    Build a case-insensitive autocomplete object from list of strings.
    """
    comp = QtWidgets.QCompleter(items)
    comp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    comp.setFilterMode(QtCore.Qt.MatchContains)
    return comp


# Data retrieval functions: use cache when available, otherwise scrape pages

def load_items() -> list[dict]:
    """
    Return list of {name, id} for all items, caching results.
    """
    if (cached := _load_json(CACHE_ITEMS_FILE)):
        return cached
    items, page = [], 1
    while True:
        url = BASE_URL + ("/items" if page == 1 else f"/items/page/{page}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            break
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            name = cols[1].get_text(strip=True)
            syntax = cols[3].get_text(strip=True).split()
            gfi_id = syntax[2] if len(syntax) >= 3 else cols[2].get_text(strip=True)
            items.append({"name": name, "id": gfi_id})
        if not soup.find("a", string="Next Page"):
            break
        page += 1
    _save_json(CACHE_ITEMS_FILE, items)
    return items


def load_creatures() -> list[dict]:
    """
    Return list of {name, class} for creatures, caching pages.
    """
    if (cached := _load_json(CACHE_CREATURES_FILE)):
        return cached
    creatures, page = [], 1
    while True:
        url = BASE_URL + ("/creatures" if page == 1 else f"/creatures/page/{page}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            break
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            name = cols[1].get_text(strip=True)
            raw = cols[2].get_text(strip=True)
            cls = raw.split(".")[-1].strip("'\"")
            creatures.append({"name": name, "class": cls})
        if not soup.find("a", string="Next Page"):
            break
        page += 1
    _save_json(CACHE_CREATURES_FILE, creatures)
    return creatures

def load_taming() -> list[dict]:
    try:
        with open(CACHE_TAMING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def load_locations() -> list[dict]:
    """
    Return list of {name, code} for map locations, caching result.
    """
    if cached := _load_json(CACHE_LOCATIONS_FILE):
        return cached
    resp = requests.get(f"{BASE_URL}/locations", timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    locations = []
    for row in soup.select("table tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue
        name = cols[2].get_text(strip=True)
        coord = cols[5].get_text(strip=True).replace("cheat setplayerpos ", "").strip()
        locations.append({"name": name, "code": coord})
    _save_json(CACHE_LOCATIONS_FILE, locations)
    return locations


def load_colors() -> list[dict]:
    """
    Return list of {name, id, hex} for dino color options.
    """
    if (cached := _load_json(CACHE_COLORS_FILE)):
        return cached
    resp = requests.get(f"{BASE_URL}/color-ids", timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    colors = []
    for opt in soup.select("select option"):
        val, hexcol = opt["value"], opt.get("data-color")
        name = opt.get_text(strip=True).rsplit("(", 1)[0].strip()
        colors.append({"name": name, "id": val, "hex": hexcol})
    _save_json(CACHE_COLORS_FILE, colors)
    return colors


def load_commands() -> list[dict]:
    """
    Return list of {name, description, syntax} for console commands.
    Scrape all pages if no cached data.
    """
    if (cached := _load_json(CACHE_COMMANDS_FILE)):
        return cached
    cmds, page = [], 1
    while True:
        url = BASE_URL + ("/commands" if page == 1 else f"/commands/page/{page}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        for tr in soup.select("table#table-view tbody > tr"):
            tds = tr.find_all("td", recursive=False)
            if len(tds) < 4:
                continue
            name = tds[0].get_text(strip=True)
            desc = tds[1].get_text(strip=True)
            box = tds[3].find("div", class_="ac-code-showcase__box")
            if not box:
                continue
            syntax = " ".join(box.stripped_strings)
            cmds.append({"name": name, "description": desc, "syntax": syntax})
        if not soup.find("a", string="Next Page"):
            break
        page += 1
    _save_json(CACHE_COMMANDS_FILE, cmds)
    return cmds


def _resource_path(rel_name: str) -> str:
    """
    Get absolute path to resource inside PyInstaller bundle or source.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel_name)
    return os.path.join(os.path.dirname(__file__), rel_name)


class CheatApp(QtWidgets.QMainWindow):
    """
    GUI application for filtering and generating ARK cheat commands.
    """
    def __init__(self, items, creatures, locations, colors, commands):
        super().__init__()
        self.items, self.creatures = items, creatures
        self.locations, self.colors = locations, colors
        self.taming = load_taming()
        self.commands = commands
        self.auto_copy = True
        self._build_ui()

    def _build_ui(self) -> None:
        """
        Assemble main window, tabs, controls, and styling.
        """
        self.setWindowTitle("ARK Ascended Cheat Generator")
        self.setWindowIcon(QtGui.QIcon(_resource_path("icon.ico")))

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        vbox = QtWidgets.QVBoxLayout(central)

        self.tabs = QtWidgets.QTabWidget()
        vbox.addWidget(self.tabs)

        # Items tab
        items_tab, self.search_items, self.dd_items = self._make_tab(
            "Filter items…", [i["name"] for i in self.items]
        )
        self._add_item_options(items_tab)
        self.tabs.addTab(items_tab, "Items")

        # Creatures tab
        cre_tab, self.search_creatures, self.dd_creatures = self._make_tab(
            "Filter creatures…", [c["name"] for c in self.creatures]
        )
        self.tabs.addTab(cre_tab, "Creatures")

        # Taming tab
        tame_tab, self.search_taming, self.dd_taming = self._make_tab(
            "Filter creatures…", [c["name"] for c in self.creatures]
        )
        # record its index so we can detect when it's shown
        self.taming_index = self.tabs.addTab(tame_tab, "Taming")

        # prepare plain labels instead of list‐widgets/group‐boxes
        self.lbl_type = QLabel()
        self.lbl_type.setFrameShape(QLabel.NoFrame)
        self.lbl_type.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.lbl_feed = QLabel()
        self.lbl_feed.setFrameShape(QLabel.NoFrame)
        self.lbl_feed.setWordWrap(True)
        self.lbl_feed.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        self.lbl_notes = QLabel()
        self.lbl_notes.setFrameShape(QLabel.NoFrame)
        self.lbl_notes.setWordWrap(True)
        self.lbl_notes.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        # lay them out in a simple form
        self.tame_form = QFormLayout()
        self.tame_form.addRow(self.lbl_type)                # full row: "Tame type: X"
        self.tame_form.addRow("Feed:",  self.lbl_feed)      # label + feed text
        self.tame_form.addRow("Notes:", self.lbl_notes)     # label + notes text

        # insert the form into the tab
        layout = tame_tab.layout() or QtWidgets.QVBoxLayout(tame_tab)
        layout.addLayout(self.tame_form)

        # Locations tab
        loc_tab, self.search_locations, self.dd_locations = self._make_tab(
            "Filter locations…", [l["name"] for l in self.locations]
        )
        self.tabs.addTab(loc_tab, "Locations")

        # Dino Color tab
        col_tab = self._make_color_tab()
        self.tabs.addTab(col_tab, "Dino Color")

        # Commands tab
        cmd_tab, self.search_commands, self.dd_commands = self._make_tab(
            "Filter commands…", [c["name"] for c in self.commands]
        )
        self._add_command_ui(cmd_tab)
        self.tabs.addTab(cmd_tab, "Commands")

        # Toolbar and status field
        self._add_toolbar()

        # Connect events and shortcuts
        self._connect_signals()

        # Initial filter and output
        self._filter_lists()
        self._update_output()

        # Immediately populate the Taming labels with the first creature
        self._update_taming_info()

    @staticmethod
    def _make_tab(placeholder: str, completer_items: List[str]):
        """
        Create a tab containing a search box and dropdown.
        Returns (tab_widget, search_field, combo_box).
        """
        tab = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(tab)
        search = QtWidgets.QLineEdit()
        search.setPlaceholderText(placeholder)
        search.setCompleter(_create_completer(completer_items))
        combo = QtWidgets.QComboBox()
        lay.addWidget(search)
        lay.addWidget(combo)
        return tab, search, combo

    def _add_item_options(self, tab: QtWidgets.QWidget) -> None:
        """
        Add quantity, quality, and blueprint checkbox controls.
        """
        group = QtWidgets.QGroupBox("Item Options")
        form = QtWidgets.QFormLayout(group)
        self.qty = QtWidgets.QSpinBox()
        self.qty.setRange(1, 9999)
        self.qty.setValue(1)
        self.qual = QtWidgets.QSpinBox()
        self.qual.setRange(0, 100)
        self.qual.setValue(1)
        self.bp = QtWidgets.QCheckBox("Blueprint")
        form.addRow("Quantity:", self.qty)
        form.addRow("Quality:", self.qual)
        form.addRow("", self.bp)
        tab.layout().addWidget(group)

    def _make_color_tab(self) -> QtWidgets.QWidget:
        """
        Build tab UI for selecting dino color region and filterable palette.
        """
        col_tab = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(col_tab)
        self.search_colors = QtWidgets.QLineEdit()
        self.search_colors.setPlaceholderText("Filter colors…")
        lay.addWidget(self.search_colors)
        self.dd_region = QtWidgets.QComboBox()
        for i in range(6):
            self.dd_region.addItem(str(i), i)
        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(QtWidgets.QLabel("Region:"))
        hl.addWidget(self.dd_region)
        hl.addStretch()
        lay.addLayout(hl)
        self.dd_colors = QtWidgets.QComboBox()
        lay.addWidget(self.dd_colors)
        return col_tab

    def _add_command_ui(self, tab: QtWidgets.QWidget) -> None:
        """
        Insert description label and dynamic parameter area in Commands tab.
        """
        self.desc_lbl = QtWidgets.QLabel()
        self.desc_lbl.setWordWrap(True)
        tab.layout().addWidget(self.desc_lbl)
        cmd_group = QtWidgets.QGroupBox("Command Options")
        self.cmd_params_layout = QtWidgets.QFormLayout(cmd_group)
        tab.layout().addWidget(cmd_group)
        self.cmd_param_widgets: List[tuple[str, QtWidgets.QWidget]] = []

    def _add_toolbar(self) -> None:
        """
        Setup toolbar with auto-copy toggle and manual copy button.
        """
        tb = QtWidgets.QToolBar()
        self.addToolBar(QtCore.Qt.TopToolBarArea, tb)
        self.auto_copy_act = QtWidgets.QAction("Auto-copy", self, checkable=True, checked=True)
        tb.addAction(self.auto_copy_act)
        copy_act = QtWidgets.QAction(QtGui.QIcon.fromTheme("edit-copy"), "Copy", self)
        tb.addAction(copy_act)
        copy_act.triggered.connect(self._copy_to_clip)
        self.out_lbl = QtWidgets.QLineEdit()
        self.out_lbl.setReadOnly(True)
        self.statusBar().addPermanentWidget(self.out_lbl, 1)

    def _connect_signals(self) -> None:
        """
        Wire UI control events to filtering and output update handlers.
        """
        # Tab‐switch & combo/slider/spinbox events all go to _update_output
        widgets = (
            self.dd_items, self.dd_creatures, self.dd_locations,
            self.dd_colors, self.dd_region, self.qty, self.qual, self.bp, self.tabs
        )
        for w in widgets:
            if isinstance(w, QtWidgets.QTabWidget):
                w.currentChanged.connect(self._update_output)
            elif isinstance(w, QtWidgets.QComboBox):
                w.currentIndexChanged.connect(self._update_output)
            elif isinstance(w, QtWidgets.QSpinBox):
                w.valueChanged.connect(self._update_output)
            else:
                w.stateChanged.connect(self._update_output)

        # Commands tab signals
        self.dd_commands.currentIndexChanged.connect(self._update_cmd_desc)
        self.dd_commands.currentIndexChanged.connect(self._build_cmd_inputs)

        # Taming tab: update labels when selection changes
        self.dd_taming.currentIndexChanged.connect(self._update_taming_info)

        # Also refresh when user clicks into the Taming tab
        self.tabs.currentChanged.connect(
            lambda idx: self._update_taming_info()
                        if idx == self.taming_index else None
        )

        # Search boxes → filter lists
        for le in (
            self.search_items,
            self.search_creatures,
            self.search_taming,
            self.search_locations,
            self.search_colors,
            self.search_commands,
        ):
            le.textChanged.connect(self._filter_lists)

        # Keyboard shortcuts
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+C"), self, self._copy_to_clip)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+F"), self, self._focus_search)
        for i in range(5):
            QtWidgets.QShortcut(
                QtGui.QKeySequence(f"Ctrl+{i+1}"),
                self,
                lambda ix=i: self.tabs.setCurrentIndex(ix)
            )

    def _filter_lists(self) -> None:
        """
        Apply search filters to all dropdown lists and rebuild command inputs.
        """
        # Items
        self._update_combo(
            self.search_items.text(),
            self.items,
            self.dd_items,
            "name",
            "id",
        )

        # Creatures for spawning
        self._update_combo(
            self.search_creatures.text(),
            self.creatures,
            self.dd_creatures,
            "name",
            "class",
        )

        # Creatures for taming
        self._update_combo(
            self.search_taming.text(),  # <-- use the taming search box
            self.taming,                # <-- data source is the taming list
            self.dd_taming,
            "name",
            "name",                     # we store the creature name as data too
        )

        # Locations
        self._update_combo(
            self.search_locations.text(),
            self.locations,
            self.dd_locations,
            "name",
            "code",
        )

        # Colors & Commands (unchanged)
        self._update_colors()
        self._update_commands()

        # Rebuild command inputs & output
        self._build_cmd_inputs()
        self._update_output()

    @staticmethod
    def _update_combo(search: str, source: list, combo: QtWidgets.QComboBox, key_name: str, key_data: str) -> None:
        """
        Refresh combo entries based on search term matching source[key_name].
        """
        combo.blockSignals(True)
        combo.clear()
        term = search.lower()
        for item in source:
            if term in item[key_name].lower():
                combo.addItem(item[key_name], item[key_data])
        combo.blockSignals(False)

    def _update_taming_info(self) -> None:
        """
        Called when the user picks a creature or switches to the Taming tab.
        Fills in the three QLabel widgets with tame-type, feed, and notes.
        """
        name = self.dd_taming.currentText()
        entry = next((t for t in self.taming if t["name"] == name), None)

        if not entry:
            self.lbl_type .setText("Tame type: —")
            self.lbl_feed .setText("—")
            self.lbl_notes.setText("No data.")
            return

        # Tame type
        self.lbl_type.setText(f"Tame type: {entry.get('tame_type', '—')}")

        # Feed
        self.lbl_feed.setText(entry.get("feed", "") or "—")

        # Notes
        self.lbl_notes.setText(entry.get("notes", ""))

    def _update_colors(self) -> None:
        """
        Filter and display color options with their hex swatches.
        """
        term = self.search_colors.text().lower()
        self.dd_colors.blockSignals(True)
        self.dd_colors.clear()
        for c in self.colors:
            if term in c["name"].lower():
                pix = QtGui.QPixmap(16, 16)
                pix.fill(QtGui.QColor(c["hex"]))
                self.dd_colors.addItem(QtGui.QIcon(pix), c["name"], c)
        self.dd_colors.blockSignals(False)

    def _update_commands(self) -> None:
        """
        Filter commands list based on name or description.
        """
        term = self.search_commands.text().lower()
        self.dd_commands.blockSignals(True)
        self.dd_commands.clear()
        for cmd in self.commands:
            if term in cmd["name"].lower() or term in cmd["description"].lower():
                self.dd_commands.addItem(cmd["name"], cmd)
        self.dd_commands.blockSignals(False)

    def _update_cmd_desc(self) -> None:
        """
        Show description of currently selected command.
        """
        data = self.dd_commands.currentData()
        self.desc_lbl.setText(data["description"] if data else "")

    def _build_cmd_inputs(self) -> None:
        """
        Create input widgets for parameters of the chosen command.
        """
        # Clear old inputs
        while self.cmd_params_layout.count():
            self.cmd_params_layout.removeRow(0)
        self.cmd_param_widgets.clear()

        cmd = self.dd_commands.currentData()
        if not cmd:
            return
        name, syntax = cmd["name"], cmd["syntax"]

        # Specialized UI for KillAOE command
        if name == "KillAOE":
            # Category dropdown
            cb = QtWidgets.QComboBox()
            for opt in ["pawns", "dinos", "tamed", "players", "wild", "structures"]:
                cb.addItem(opt, opt)
            cb.setToolTip("Select category – choose target group for kill aoe command")
            cb.currentIndexChanged.connect(self._update_output)
            self.cmd_params_layout.addRow("Category:", cb)
            self.cmd_param_widgets.append(("Category", cb))
            # Radius spinbox
            sp = self._make_spin(0, 9999, "Radius in units")
            self.cmd_params_layout.addRow("Radius:", sp)
            self.cmd_param_widgets.append(("Radius", sp))

        # Specialized UI for GFI command
        elif len(syntax.split()) > 1 and syntax.split()[1].upper() == "GFI":
            # Item dropdown (uses GFI codes behind the scenes)
            cb_item = QtWidgets.QComboBox()
            for it in self.items:
                cb_item.addItem(it["name"], it["id"])
            cb_item.setToolTip("Select item by name")
            cb_item.currentIndexChanged.connect(self._update_output)
            self.cmd_params_layout.addRow("Item:", cb_item)
            self.cmd_param_widgets.append(("Blueprint / GFI", cb_item))

            # Amount spinbox
            sp_amount = self._make_spin(1, 9999, "Quantity of item to give")
            self.cmd_params_layout.addRow("Amount:", sp_amount)
            self.cmd_param_widgets.append(("Amount", sp_amount))

            # Quality spinbox
            sp_quality = self._make_spin(0, 100, "Quality percentage of item")
            self.cmd_params_layout.addRow("Quality:", sp_quality)
            self.cmd_param_widgets.append(("Quality", sp_quality))

            # Force Blueprint checkbox (0 = use GFI code, 1 = use full blueprint)
            cb_force = self._make_checkbox("Use full blueprint instead of GFI code")
            self.cmd_params_layout.addRow("Force Blueprint:", cb_force)
            self.cmd_param_widgets.append(("Force Blueprint", cb_force))

        # Specialized UI for SetGamma command
        elif name == "SetGamma":
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 60)  # integer steps
            slider.setTickInterval(1)
            slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            slider.setValue(10)  # default → 1.0
            slider.setToolTip("Gamma value from 0.0 (dark) to 6.0 (bright)")
            slider.valueChanged.connect(self._update_output)

            self.cmd_params_layout.addRow("Gamma:", slider)
            self.cmd_param_widgets.append(("Value", slider))

        # Specialized UI for ClearWater (new checkbox)
        elif name == "ClearWater":
            cb_clear = QtWidgets.QCheckBox("Disable underwater volumetric fog")
            cb_clear.setToolTip("Check to disable fog (r.VolumetricFog 0), uncheck to enable fog (r.VolumetricFog 1)")
            cb_clear.stateChanged.connect(self._update_output)
            self.cmd_params_layout.addRow("Clear Water:", cb_clear)
            self.cmd_param_widgets.append(("ClearWater", cb_clear))

        # Specialized UI for SpawnExactDino parameters
        elif name == "SpawnExactDino":
            cb_bp = QtWidgets.QComboBox()
            for c in self.creatures:
                cb_bp.addItem(c["name"], c["class"])
            cb_bp.setToolTip("Creature Blueprint – pick the dino to spawn")
            cb_bp.currentIndexChanged.connect(self._update_output)
            self.cmd_params_layout.addRow("Blueprint:", cb_bp)
            self.cmd_param_widgets.append(("Blueprint", cb_bp))

            cb_sb = QtWidgets.QComboBox()
            for i in self.items:
                cb_sb.addItem(i["name"], i["id"])
            cb_sb.setToolTip("Saddle Blueprint – pick a saddle or leave blank")
            cb_sb.currentIndexChanged.connect(self._update_output)
            self.cmd_params_layout.addRow("Saddle Blueprint:", cb_sb)
            self.cmd_param_widgets.append(("Saddle Blueprint", cb_sb))

            for label, widget in [
                *((arg, self._make_spin(0,9999,arg)) for arg in ("Saddle Quality","Base Level","Extra Levels")),
                *((arg, self._make_lineedit("e.g. 10,13,...",arg)) for arg in ("Base Stats","Added Stats")),
                ("Name", self._make_lineedit("MyDino","Name")),
                *((arg, self._make_checkbox(arg)) for arg in ("Cloned","Neutered")),
                *((arg, self._make_lineedit(ph,arg)) for arg,ph in [("Tamed Date","YYYY-MM-DD"),("Uploaded From","Location"),("Imprinter Name","Name"),("Imprinter ID","UE4 ID")]),
                ("Imprint Quality", self._make_spin(0,100,"Imprint Quality")),
                ("Fixed 0", self._make_fixed_zero()),
                ("Region Colors", self._make_lineedit("e.g. 12,49,...","Region Colors")),
                *((arg, self._make_spin(-9999,9999,arg)) for arg in ("Creature ID","Experience","Spawn Distance","Spawn Y","Spawn Z"))
            ]:
                self.cmd_params_layout.addRow(f"{label}:", widget)
                self.cmd_param_widgets.append((label, widget))

        # Generic parameter parsing from syntax <...>
        else:
            for param in re.findall(r"<([^>]+)>", syntax):
                if any(x in param for x in ("Amount","Level","Quality","Stats")):
                    w = self._make_spin(0,999999,param)
                elif param.lower().startswith(("true","false","prevent","cloned","neutered")):
                    w = self._make_checkbox(param)
                else:
                    w = self._make_lineedit(param,param)
                self.cmd_params_layout.addRow(f"{param}:", w)
                self.cmd_param_widgets.append((param,w))

        self._update_output()

    def _make_spin(self, lo:int, hi:int, tip:str) -> QtWidgets.QSpinBox:
        w = QtWidgets.QSpinBox()
        w.setRange(lo,hi)
        w.setToolTip(tip)
        w.valueChanged.connect(self._update_output)
        return w

    def _make_lineedit(self, ph:str, tip:str) -> QtWidgets.QLineEdit:
        w = QtWidgets.QLineEdit()
        w.setPlaceholderText(ph)
        w.setToolTip(tip)
        w.textChanged.connect(self._update_output)
        return w

    def _make_checkbox(self, tip:str) -> QtWidgets.QCheckBox:
        w = QtWidgets.QCheckBox()
        w.setToolTip(tip)
        w.stateChanged.connect(self._update_output)
        return w

    def _make_fixed_zero(self) -> QtWidgets.QSpinBox:
        w = QtWidgets.QSpinBox()
        w.setRange(0,0)
        w.setValue(0)
        w.setToolTip("Must be 0")
        w.setEnabled(False)
        return w

    def _update_output(self) -> None:
        """
        Build final cheat command string based on active tab and inputs.
        Auto-copy to clipboard if enabled.  Leaves output blank on Taming tab.
        """
        tab = self.tabs.currentIndex()
        txt = ""

        # Items tab (0)
        if tab == 0:
            if (gid := self.dd_items.currentData()):
                txt = f"cheat gfi {gid} {self.qty.value()} {self.qual.value()} {int(self.bp.isChecked())}"

        # Creature spawn tab (1)
        elif tab == 1:
            if (cls := self.dd_creatures.currentData()):
                txt = f"admincheat Summon {cls}"

        # Taming tab (2) → no command output
        elif tab == 2:
            txt = ""  # explicitly blank

        # Teleport (Locations) tab (3)
        elif tab == 3:
            if (data := self.dd_locations.currentData()):
                x, y, z = data.split()
                txt = f"cheat setplayerpos {x} {y} {z}"

        # Dino Color tab (4)
        elif tab == 4:
            region = self.dd_region.currentData()
            if region is not None and (c := self.dd_colors.currentData()):
                txt = f"cheat setTargetDinoColor {region} {c['id']}"

        # Commands & custom console commands tab (5+)
        else:
            if (cmd := self.dd_commands.currentData()):
                if cmd["name"] == "ClearWater":
                    cb = next(
                        (w for name, w in self.cmd_param_widgets if name == "ClearWater"),
                        None
                    )
                    if cb:
                        fog_state = "0" if cb.isChecked() else "1"
                        txt = f"r.VolumetricFog {fog_state}"
                else:
                    parts = cmd["syntax"].split()[:2]
                    for _, w in self.cmd_param_widgets:
                        if isinstance(w, QtWidgets.QSpinBox):
                            parts.append(str(w.value()))
                        elif isinstance(w, QtWidgets.QSlider):
                            parts.append(f"{w.value()/10:.1f}")
                        elif isinstance(w, QtWidgets.QCheckBox):
                            parts.append("1" if w.isChecked() else "0")
                        elif isinstance(w, QtWidgets.QLineEdit):
                            parts.append(w.text().strip())
                        elif isinstance(w, QtWidgets.QComboBox):
                            d = w.currentData()
                            parts.append(str(d) if d is not None else w.currentText())
                    txt = " ".join(parts)

        # Update the output field and auto-copy if needed
        self.out_lbl.setText(txt)
        if self.auto_copy_act.isChecked() and txt:
            QtWidgets.QApplication.clipboard().setText(txt)

    def _copy_to_clip(self) -> None:
        """
        Copy current output text to clipboard and show status.
        """
        if (txt := self.out_lbl.text()):
            QtWidgets.QApplication.clipboard().setText(txt)
            self.statusBar().showMessage("Copied!", 1500)

    def _focus_search(self) -> None:
        """
        Focus the search box in the active tab.
        """
        idx = self.tabs.currentIndex()
        fields = [
            self.search_items,
            self.search_creatures,
            self.search_locations,
            self.search_colors,
            self.search_commands
        ]
        fields[idx].setFocus()


def run_app() -> None:
    """
    Initialize Qt application, load data, and launch main window.
    """
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QtGui.QPalette()
    pal.setColor(QtGui.QPalette.Window,          QtGui.QColor(45, 45, 45))
    pal.setColor(QtGui.QPalette.WindowText,      QtGui.QColor(220, 220, 220))
    pal.setColor(QtGui.QPalette.Base,            QtGui.QColor(35, 35, 35))
    pal.setColor(QtGui.QPalette.AlternateBase,   QtGui.QColor(55, 55, 55))
    pal.setColor(QtGui.QPalette.Text,            QtGui.QColor(220, 220, 220))
    pal.setColor(QtGui.QPalette.Button,          QtGui.QColor(60, 60, 60))
    pal.setColor(QtGui.QPalette.ButtonText,      QtGui.QColor(220, 220, 220))
    pal.setColor(QtGui.QPalette.Highlight,       QtGui.QColor(38, 79, 120))
    pal.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(220, 220, 220))
    app.setPalette(pal)

    splash_pix = QtGui.QPixmap(300, 200)
    splash_pix.fill(QtGui.QColor(60, 60, 60))
    splash = QtWidgets.QSplashScreen(splash_pix)
    splash.showMessage("Loading data…", QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom, QtGui.QColor("white"))
    splash.show()
    app.processEvents()

    items     = load_items()
    items.sort(key=lambda c: c["name"].lower())
    creatures = load_creatures()
    creatures.sort(key=lambda c: c["name"].lower())
    locations = load_locations()
    locations.sort(key=lambda c: c["name"].lower())
    colors    = load_colors()
    commands  = load_commands()
    commands.sort(key=lambda c: c["name"].lower())

    splash.finish(None)

    w = CheatApp(items, creatures, locations, colors, commands)
    w.resize(750, 500)
    w.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
