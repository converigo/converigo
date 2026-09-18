"""Pure-Python OLE2/CFBF preflight for XLS files.

No external dependencies. Parses Compound File Binary Format (CFBF) structure
to locate Workbook/Book stream and extract BOF record version to classify
BIFF variants: BIFF5 (0x0500), BIFF8 (0x0600), or reject unsupported/corrupt files.

Used by xls_to_xlsx plugin to fast-reject incompatible inputs before invoking
LibreOffice conversion.
"""

import enum
from pathlib import Path
from typing import Optional


class BiffClassification(enum.Enum):
    """BIFF format classification for admission control."""
    BIFF5 = "biff5"  # Excel 5.0/95 (BOF 0x0500)
    BIFF8 = "biff8"  # Excel 97-2003 (BOF 0x0600)
    NOT_OLE2 = "not_ole2"  # Not a Compound File
    NO_WORKBOOK_STREAM = "no_workbook_stream"  # OLE2 but missing Workbook/Book stream
    UNSUPPORTED_BIFF = "unsupported_biff"  # Other BIFF version (e.g., 0x0550)
    CORRUPT = "corrupt"  # Truncated or malformed structure


# CFBF magic signature
MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")

# Special FAT sector values
FREESECT = 0xFFFFFFFF
ENDOFCHAIN = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
DIFSECT = 0xFFFFFFFC

# Directory entry type codes
ENTRY_EMPTY = 0
ENTRY_STORAGE = 1
ENTRY_STREAM = 2
ENTRY_ROOT = 5

# BOF record opcode
BOF_OPCODE = 0x0809

# Accepted BIFF versions
BIFF5_VERSION = 0x0500
BIFF8_VERSION = 0x0600


def _u16(data: bytes, offset: int) -> int:
    """Read little-endian uint16 at offset."""
    return int.from_bytes(data[offset:offset + 2], "little")


def _u32(data: bytes, offset: int) -> int:
    """Read little-endian uint32 at offset."""
    return int.from_bytes(data[offset:offset + 4], "little")


def _parse_cfbf(raw: bytes, stream_name: str) -> Optional[bytes]:
    """Parse CFBF structure and return first 8 bytes of named stream.
    
    Args:
        raw: Complete file bytes
        stream_name: Target stream name ("Workbook" or "Book")
    
    Returns:
        First 8 bytes of stream if found, None otherwise.
    """
    if len(raw) < 512 or raw[:8] != MAGIC:
        return None
    
    # Parse header
    sector_size = 1 << _u16(raw, 30)
    mini_sector_size = 1 << _u16(raw, 32)
    mini_cutoff = _u32(raw, 56)
    first_dir_sector = _u32(raw, 48)
    
    # Build DIFAT (master FAT index) from header and extension sectors
    difat = [_u32(raw, 76 + 4 * i) for i in range(109)]
    next_difat = _u32(raw, 68)
    seen_difat = set()
    
    while next_difat not in (FREESECT, ENDOFCHAIN) and next_difat not in seen_difat:
        if next_difat < 0 or (next_difat + 1) * sector_size > len(raw):
            break
        seen_difat.add(next_difat)
        base = (next_difat + 1) * sector_size
        for i in range(sector_size // 4 - 1):
            difat.append(_u32(raw, base + 4 * i))
        next_difat = _u32(raw, base + sector_size - 4)
    
    # Build FAT from sectors listed in DIFAT
    fat = []
    for sec in difat:
        if sec in (FREESECT, ENDOFCHAIN, FATSECT, DIFSECT):
            continue
        if sec < 0 or (sec + 1) * sector_size > len(raw):
            continue
        base = (sec + 1) * sector_size
        chunk = raw[base:base + sector_size]
        fat.extend(_u32(chunk, i) for i in range(0, len(chunk), 4))
    
    def follow_chain(start: int, limit: int = 8192) -> list[int]:
        """Follow FAT chain from start sector, return sector list (capped)."""
        result = []
        current = start
        seen = set()
        while current not in (ENDOFCHAIN, FREESECT) and len(result) < limit:
            if current in seen or current < 0 or current >= len(fat):
                break
            seen.add(current)
            result.append(current)
            current = fat[current]
        return result
    
    def read_sector(sector_num: int) -> bytes:
        """Read a single sector by index."""
        base = (sector_num + 1) * sector_size
        return raw[base:base + sector_size]

    
    # Walk directory entries to find target stream
    root_start_sector = None
    target_start_sector = None
    target_size = None
    
    for dir_sector in follow_chain(first_dir_sector, limit=64):
        dir_data = read_sector(dir_sector)
        for i in range(0, len(dir_data), 128):
            entry = dir_data[i:i + 128]
            if len(entry) < 128:
                break
            
            # Decode name (UTF-16LE, null-terminated)
            name_raw = entry[:64]
            try:
                name = name_raw.decode("utf-16-le", "ignore").replace("\x00", "").strip()
            except:
                name = ""
            
            entry_type = entry[66]
            start_sector = _u32(entry, 116)
            size = _u32(entry, 120)
            
            if entry_type == ENTRY_ROOT:
                root_start_sector = start_sector
            elif entry_type == ENTRY_STREAM and name == stream_name:
                target_start_sector = start_sector
                target_size = size
                break
        
        if target_start_sector is not None:
            break
    
    if target_start_sector is None or target_size is None:
        return None
    
    # Read first 8 bytes of target stream
    if target_size >= mini_cutoff:
        # Regular stream: read from first sector
        chain = follow_chain(target_start_sector, limit=1)
        if not chain:
            return None
        sector_data = read_sector(chain[0])
        return sector_data[:8]
    else:
        # Mini stream: data stored in root entry's stream
        if root_start_sector is None or root_start_sector in (FREESECT, ENDOFCHAIN):
            return None
        
        # Assemble mini stream from root sectors
        mini_stream = bytearray()
        for sec in follow_chain(root_start_sector, limit=1024):
            mini_stream.extend(read_sector(sec))
            if len(mini_stream) >= (target_start_sector + 1) * mini_sector_size:
                break
        
        # Extract target data from mini stream
        offset = target_start_sector * mini_sector_size
        return bytes(mini_stream[offset:offset + 8])


def _classify_bof(data: bytes) -> BiffClassification:
    """Classify BIFF version from BOF record header.
    
    Args:
        data: First 8 bytes of Workbook stream
    
    Returns:
        Classification enum value
    """
    if len(data) < 6:
        return BiffClassification.CORRUPT
    
    opcode = _u16(data, 0)
    if opcode != BOF_OPCODE:
        return BiffClassification.UNSUPPORTED_BIFF
    
    # BOF record has variable length; version is at offset +4
    # BIFF5/7: record length 0x0008, version at +4
    # BIFF8:   record length 0x0010, version at +4
    record_len = _u16(data, 2)
    if record_len < 6:
        return BiffClassification.CORRUPT
    
    version = _u16(data, 4)
    if version == BIFF5_VERSION:
        return BiffClassification.BIFF5
    elif version == BIFF8_VERSION:
        return BiffClassification.BIFF8
    else:
        return BiffClassification.UNSUPPORTED_BIFF


def classify_xls(file_path: Path) -> BiffClassification:
    """Classify XLS file by parsing OLE2 structure and BOF record.
    
    This is a fast preflight check (no external dependencies) to reject
    unsupported/corrupt files before invoking LibreOffice conversion.
    
    Args:
        file_path: Path to candidate XLS file
    
    Returns:
        BiffClassification enum indicating acceptance or rejection reason
    
    Examples:
        >>> classify_xls(Path("sample_biff8.xls"))
        <BiffClassification.BIFF8: 'biff8'>
        
        >>> classify_xls(Path("masquerade.xls"))  # Actually XLSX
        <BiffClassification.NOT_OLE2: 'not_ole2'>
    """
    try:
        raw = file_path.read_bytes()
    except (OSError, IOError):
        return BiffClassification.CORRUPT
    
    if len(raw) < 512 or raw[:8] != MAGIC:
        return BiffClassification.NOT_OLE2
    
    # Try "Workbook" stream first (BIFF5/8 standard)
    stream_data = _parse_cfbf(raw, "Workbook")
    
    # Fall back to "Book" stream (rare variant)
    if stream_data is None:
        stream_data = _parse_cfbf(raw, "Book")
    
    if stream_data is None:
        return BiffClassification.NO_WORKBOOK_STREAM
    
    return _classify_bof(stream_data)


def is_acceptable(classification: BiffClassification) -> bool:
    """Check if classification is acceptable for conversion.
    
    Args:
        classification: Result from classify_xls()
    
    Returns:
        True if BIFF5 or BIFF8, False otherwise
    """
    return classification in (BiffClassification.BIFF5, BiffClassification.BIFF8)
