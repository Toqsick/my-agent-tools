# NPC-Datenbank & JSON-Bridge Patterns

> **Stand:** 20. Juni 2026
> **Ziel:** NPCs in SQLite3 speichern, aus JSON importieren, nach GreyScript injizieren
> **Voraussetzungen:** Python 3.11+, sqlite3 (3.50.4)

## 1. NPC-Datenbank Schema

```python
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "greyhack-npc.db"

def init_npc_db(db_path: str = None) -> sqlite3.Connection:
    """Erstellt NPC-DB mit Tabellen: npcs, npc_dialogues, npc_trades, player_actions"""
    if db_path is None:
        db_path = str(DB_PATH)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS npcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL DEFAULT 'neutral',
            location TEXT,
            ip_address TEXT,
            description TEXT,
            health INTEGER DEFAULT 100,
            faction TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS npc_dialogues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            npc_id INTEGER NOT NULL,
            trigger TEXT NOT NULL,
            response TEXT NOT NULL,
            condition TEXT,
            priority INTEGER DEFAULT 0,
            FOREIGN KEY (npc_id) REFERENCES npcs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS npc_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            npc_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            currency TEXT DEFAULT 'crypto',
            stock INTEGER DEFAULT -1,
            FOREIGN KEY (npc_id) REFERENCES npcs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS player_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            action TEXT NOT NULL,
            target_npc TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_npc_location ON npcs(location);
        CREATE INDEX IF NOT EXISTS idx_npc_faction ON npcs(faction);
        CREATE INDEX IF NOT EXISTS idx_dialogue_trigger ON npc_dialogues(trigger);
        CREATE INDEX IF NOT EXISTS idx_dialogue_npc ON npc_dialogues(npc_id);
    """)
    conn.commit()
    return conn
```

## 2. NPCDatabase Wrapper

```python
class NPCDatabase:
    """SQLite3-Wrapper für NPC-Daten. Context-Manager unterstützt."""
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.conn = init_npc_db(self.db_path)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def add_npc(self, name: str, npc_type: str = "neutral", location: str = None,
                ip_address: str = None, description: str = None,
                health: int = 100, faction: str = None) -> int:
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO npcs (name, type, location, ip_address, description, health, faction) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, npc_type, location, ip_address, description, health, faction))
        self.conn.commit()
        return c.lastrowid

    def add_dialogue(self, npc_id: int, trigger: str, response: str,
                     condition: str = None, priority: int = 0) -> int:
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO npc_dialogues (npc_id, trigger, response, condition, priority) "
            "VALUES (?, ?, ?, ?, ?)", (npc_id, trigger, response, condition, priority))
        self.conn.commit()
        return c.lastrowid

    def add_trade(self, npc_id: int, item_name: str, price: int,
                  currency: str = "crypto", stock: int = -1) -> int:
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO npc_trades (npc_id, item_name, price, currency, stock) "
            "VALUES (?, ?, ?, ?, ?)", (npc_id, item_name, price, currency, stock))
        self.conn.commit()
        return c.lastrowid

    def get_npc_by_name(self, name: str) -> dict:
        c = self.conn.cursor()
        c.execute("SELECT * FROM npcs WHERE name = ?", (name,))
        row = c.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in c.description]
        return dict(zip(columns, row))

    def get_npcs_by_location(self, location: str) -> list:
        c = self.conn.cursor()
        c.execute("SELECT * FROM npcs WHERE location = ?", (location,))
        columns = [desc[0] for desc in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]

    def get_npcs_by_faction(self, faction: str) -> list:
        c = self.conn.cursor()
        c.execute("SELECT * FROM npcs WHERE faction = ?", (faction,))
        columns = [desc[0] for desc in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]

    def get_dialogue(self, npc_id: int, trigger: str) -> dict:
        c = self.conn.cursor()
        c.execute("SELECT * FROM npc_dialogues WHERE npc_id = ? AND trigger = ? "
                  "ORDER BY priority DESC LIMIT 1", (npc_id, trigger))
        row = c.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in c.description]
        return dict(zip(columns, row))

    def get_all_dialogues(self, npc_id: int) -> list:
        c = self.conn.cursor()
        c.execute("SELECT * FROM npc_dialogues WHERE npc_id = ? ORDER BY priority DESC", (npc_id,))
        columns = [desc[0] for desc in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]

    def get_trades(self, npc_id: int) -> list:
        c = self.conn.cursor()
        c.execute("SELECT * FROM npc_trades WHERE npc_id = ?", (npc_id,))
        columns = [desc[0] for desc in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]

    def search_npcs(self, query: str) -> list:
        c = self.conn.cursor()
        like = f"%{query}%"
        c.execute("SELECT * FROM npcs WHERE name LIKE ? OR description LIKE ? OR location LIKE ?",
                  (like, like, like))
        columns = [desc[0] for desc in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]

    def update_npc(self, npc_id: int, **kwargs) -> bool:
        allowed = {"name", "type", "location", "ip_address", "description", "health", "faction"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [npc_id]
        c = self.conn.cursor()
        c.execute(f"UPDATE npcs SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
        self.conn.commit()
        return c.rowcount > 0

    def delete_npc(self, npc_id: int) -> bool:
        c = self.conn.cursor()
        c.execute("DELETE FROM npcs WHERE id = ?", (npc_id,))
        self.conn.commit()
        return c.rowcount > 0

    def stats(self) -> dict:
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM npcs")
        npc_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM npc_dialogues")
        dialogue_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM npc_trades")
        trade_count = c.fetchone()[0]
        c.execute("SELECT DISTINCT faction FROM npcs WHERE faction IS NOT NULL")
        factions = [row[0] for row in c.fetchall()]
        return {"npcs": npc_count, "dialogues": dialogue_count, "trades": trade_count, "factions": factions}
```

## 3. JSON → SQLite3 Import

```python
import json

def import_npcs_from_json(json_path: str, db_path: str = None) -> dict:
    """
    Importiert NPC-Daten aus JSON in SQLite3.
    Erwartetes Format: {"npcs": [{name, type, location, ip_address, description,
                                   health, faction, dialogues: [...], trades: [...]}]}
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with NPCDatabase(db_path) as db:
        imported = 0
        for npc_data in data.get("npcs", []):
            npc_id = db.add_npc(
                name=npc_data["name"], npc_type=npc_data.get("type", "neutral"),
                location=npc_data.get("location"), ip_address=npc_data.get("ip_address"),
                description=npc_data.get("description"), health=npc_data.get("health", 100),
                faction=npc_data.get("faction"))
            for dlg in npc_data.get("dialogues", []):
                db.add_dialogue(npc_id, dlg["trigger"], dlg["response"],
                                dlg.get("condition"), dlg.get("priority", 0))
            for trade in npc_data.get("trades", []):
                db.add_trade(npc_id, trade["item_name"], trade["price"],
                              trade.get("currency", "crypto"), trade.get("stock", -1))
            imported += 1
        return {"imported": imported, "stats": db.stats()}
```

## 4. SQLite3 → JSON Export

```python
def export_npcs_to_json(db_path: str = None, json_path: str = None,
                        faction: str = None, location: str = None) -> dict:
    """Exportiert NPCs aus SQLite3 als JSON, optional gefiltert."""
    with NPCDatabase(db_path) as db:
        c = db.conn.cursor()
        query = "SELECT * FROM npcs WHERE 1=1"
        params = []
        if faction:
            query += " AND faction = ?"
            params.append(faction)
        if location:
            query += " AND location = ?"
            params.append(location)
        c.execute(query, params)
        columns = [desc[0] for desc in c.description]
        npcs = [dict(zip(columns, row)) for row in c.fetchall()]
        for npc in npcs:
            npc["dialogues"] = db.get_all_dialogues(npc["id"])
            npc["trades"] = db.get_trades(npc["id"])
        result = {"npcs": npcs, "total": len(npcs)}
        if json_path:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        return result
```

## 5. GTFOBins → NPC-Bridge

```python
def import_gtfobins_as_npcs(json_path: str, db_path: str = None) -> dict:
    """Importiert GTFOBins-Datenbank (63 Binaries) als NPCs mit Exploit-Daten."""
    with open(json_path, 'r', encoding='utf-8') as f:
        gtfo = json.load(f)
    with NPCDatabase(db_path) as db:
        imported = 0
        for binary_name, binary_data in gtfo.get("binaries", {}).items():
            npc_id = db.add_npc(
                name=binary_name, npc_type="binary",
                location="/usr/bin/" + binary_name,
                description=f"GTFOBins: {len(binary_data.get('functions', {}))} Funktionen")
            for func_name, func_data in binary_data.get("functions", {}).items():
                for mode in ["suid", "sudo", "unprivileged"]:
                    if func_data.get(mode):
                        code = func_data.get("code", [])
                        db.add_dialogue(
                            npc_id, f"{func_name}:{mode}",
                            code[0] if code else "N/A",
                            condition=f"mode={mode}",
                            priority=1 if mode == "suid" else 0)
            imported += 1
        return {"imported": imported, "stats": db.stats()}
```

## 6. NPC → GreyScript Template-Injection

```python
def inject_npc_to_greyscript(npc: dict, src_template: str, output_path: str) -> bool:
    """Injiziert NPC-Daten in ein GreyScript-Template.
    Platzhalter: {{NPC_NAME}}, {{NPC_TYPE}}, {{NPC_LOCATION}}, {{NPC_IP}}, {{NPC_DIALOGUES}}
    """
    with open(src_template, 'r', encoding='utf-8') as f:
        template = f.read()
    replacements = {
        "{{NPC_NAME}}": npc.get("name", "Unknown"),
        "{{NPC_TYPE}}": npc.get("type", "neutral"),
        "{{NPC_LOCATION}}": npc.get("location", ""),
        "{{NPC_IP}}": npc.get("ip_address", ""),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    dialogues_gs = ""
    for dlg in npc.get("dialogues", []):
        condition = dlg.get("condition", "")
        if condition:
            dialogues_gs += f'if {condition} then\n'
            dialogues_gs += f'    print("{dlg["response"]}")\n'
            dialogues_gs += f'end if\n'
        else:
            dialogues_gs += f'// Trigger: {dlg["trigger"]}\n'
            dialogues_gs += f'print("{dlg["response"]}")\n'
    template = template.replace("{{NPC_DIALOGUES}}", dialogues_gs)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)
    return True
```

## 7. Vollständige Pipeline

```python
def full_npc_pipeline(json_path: str, db_path: str = None):
    """JSON → SQLite3 → GreyScript → greybel build → greybel execute → Parse"""
    # 1. Import
    result = import_npcs_from_json(json_path, db_path)
    # 2. Load
    with NPCDatabase(db_path) as db:
        npc = db.get_npc_by_name("Reraldi")
        if not npc:
            return
        npc["dialogues"] = db.get_all_dialogues(npc["id"])
    # 3. Generate GreyScript
    inject_npc_to_greyscript(npc, "/tmp/npc_template.src", "/tmp/npc_generated.src")
    # 4. Build
    build_result = greybel_build("/tmp/npc_generated.src")
    # 5. Execute
    exec_result = greybel_execute("/tmp/npc_generated.src")
    # 6. Parse
    parsed = parse_greybel_output(exec_result["stdout"], format="lines")
    return {"npc": npc, "build": build_result, "execute": exec_result, "parsed": parsed}
```
