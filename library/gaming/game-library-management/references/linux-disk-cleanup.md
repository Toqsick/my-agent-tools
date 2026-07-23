# Linux Disk Cleanup für Gaming-Libraries

## Schnelle Platzgewinne auf Linux-DATA-Platten

### 1. Papierkorb analysieren (`.Trash-1000/`)
Der GNOME/KDE-Papierkorb liegt unter `.Trash-1000/files/` und kann mehrere GB verstecken.

```bash
# Größe checken
du -sh /mnt/DATA/.Trash-1000/

# Inhalt anzeigen
ls -la /mnt/DATA/.Trash-1000/files/
```

**Typischer Befund:** Alte Steam-Installationen die aus `common/` gelöscht wurden, aber als Backup im Trash landeten. Wenn ein `.csd`-Backup im steamapps-Ordner existiert, ist der Trash sicher leerbar.

### 2. Steam Recordings archivieren
Steam speichert Game-Recordings als fragmentierte `.m4s`-Chunks:

```bash
# Größe checken
du -sh /mnt/DATA/Programme/Steam/steamapps/Recordings/

# Archivieren (sicher, Original bleibt)
tar --use-compress-program 'zstd -T0 -1' -cf \
  /mnt/DATA/_Archives/Recordings/steam_rec_$(date +%Y%m%d).tar.zst \
  -C /mnt/DATA/Programme/Steam/steamapps/ Recordings/

# Integrität prüfen
zstd -t /mnt/DATA/_Archives/Recordings/steam_rec_*.tar.zst

# Original löschen (Steam legt neue an)
rm -rf /mnt/DATA/Programme/Steam/steamapps/Recordings/video/
rm -rf /mnt/DATA/Programme/Steam/steamapps/Recordings/clips/
```

### 3. Mountpoint aufräumen (UUID → LABEL)
UUID-Mounts sind schwer lesbar. Besser mit LABEL arbeiten:

```bash
# Aktuelles Label checken
lsblk -f | grep nvme

# In /etc/fstab UUID durch LABEL ersetzen
sudo sed -i 's|UUID=387a8f02-053a-40a0-b362-4de5e9a0b820|LABEL=DATA|g' /etc/fstab

# Mountpoint umbenennen
sudo mkdir -p /mnt/DATA
sudo sed -i 's|/mnt/387a8f02-053a-40a0-b362-4de5e9a0b820|/mnt/DATA|g' /etc/fstab

# Neu mounten
sudo umount /mnt/387a8f02-053a-40a0-b362-4de5e9a0b820
sudo mount -a
```

### 4. Duplikat-Erkennung
Gleiches Spiel kann an mehreren Orten liegen:

```bash
# MD5-Hash über common/ und Trash vergleichen
find /mnt/DATA/Programme/Steam/steamapps/common/ /mnt/DATA/.Trash-1000/files/ \
  -type f -exec md5sum {} + 2>/dev/null | sort | uniq -d -w32
```

### 5. Shader-Cache
Kann bei aktuellen Spielen mehrere GB pro Titel füllen:

```bash
# Größe checken
du -sh /mnt/DATA/Programme/Steam/steamapps/shadercache/

# Löschen (wird beim nächsten Start neu generiert)
rm -rf /mnt/DATA/Programme/Steam/steamapps/shadercache/*
```

## Ergebnis-Beispiel (Session 03.06.2026)

| Aktion | Platzgewinn |
|--------|-------------|
| Papierkorb leeren | 80.9 GB |
| Recordings archivieren | 7.1 GB → Archiv |
| Recordings Original löschen | 7.2 GB |
| **Gesamt frei** | **~95 GB** |
| Vorher: 92% voll → Nachher: 66% voll |
