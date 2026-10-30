# Genesis Graphics Studio — Tile Lab 0.1

First-stage Genesis ROM tile viewer and raw 4bpp tile editor. Open a linear Genesis ROM (.md/.bin/.gen), navigate 8x8 tile regions, export a PNG, import indexed PNGs using values 0–15 (or exact palette RGB values), and save a modified ROM with recalculated Genesis header checksum.

**Limitations:** No compression/decompression, tilemap reconstruction, automatic sprite assembly, or safe detection of graphics addresses yet. Reimport modifies a contiguous raw ROM byte range, and using the wrong region can break the ROM. Keep backups and test in an emulator. This repository intentionally does not distribute game ROMs.

## Windows download

Open [Actions](https://github.com/Becksploder2/GGS/actions/workflows/windows.yml), select the latest successful **Build Windows EXE** run, and download its `GenesisGraphicsStudio-Windows-EXE` artifact. Extract the ZIP and double-click `GenesisGraphicsStudio.exe`. Python is not required on your Windows PC.
