import argparse
import re
import sqlite3
from datetime import datetime
from pathlib import Path

MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "agustus": 8,
    "september": 9, "oktober": 10, "november": 11,
    "desember": 12, "december": 12,
}
AMOUNT_PATTERN = re.compile(r"^\s*([\d.,]+)\s*[kK]\s*$")


def parse_amount(value: str) -> int:
    match = AMOUNT_PATTERN.match(value)
    if not match:
        raise ValueError(f"Nominal tidak valid: {value!r}")
    number = match.group(1).replace(".", "").replace(",", ".")
    return round(float(number) * 1000)


def parse_file(path: Path) -> list[tuple[str, str, int, str]]:
    month_name, year_text = path.stem.rsplit(" ", 1)
    month = MONTHS[month_name.lower()]
    base_date = datetime(int(year_text), month, 1, 12, 0).isoformat()
    transaction_type = None
    transactions = []
    text = path.read_text(encoding="utf-8")

    for raw_line in text.splitlines():
        line = re.sub(r"<[^>]+>|&nbsp;", "", raw_line).strip()
        if not line:
            continue
        label = re.sub(r"[:\s]+$", "", line).lower()
        if label == "pemasukan":
            transaction_type = "masuk"
            continue
        if label in {"pengeluaran", "pengeluran"}:
            transaction_type = "keluar"
            continue
        if transaction_type == "masuk":
            try:
                amount = parse_amount(line)
            except ValueError:
                continue
            transactions.append((base_date, "masuk", amount, "Pemasukan"))
        elif transaction_type == "keluar" and ":" in line:
            description, amount_text = line.rsplit(":", 1)
            try:
                amount = parse_amount(amount_text)
            except ValueError:
                continue
            transactions.append((base_date, "keluar", amount, description.strip()))
    return transactions


def seed_database(source_dir: str = r"C:\Users\BEST LAPTOP\Downloads\pengeluaran uang"):
    source = Path(source_dir)
    files = sorted(source.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"Tidak ada file Markdown di {source}")

    transactions = [row for path in files for row in parse_file(path)]
    with sqlite3.connect("tracefund.db") as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('masuk', 'keluar')),
            amount INTEGER NOT NULL CHECK(amount >= 0),
            description TEXT NOT NULL
        )""")
        connection.execute("DELETE FROM transactions")
        connection.executemany(
            "INSERT INTO transactions (date, type, amount, description) VALUES (?, ?, ?, ?)",
            transactions,
        )
    print(f"Mengimpor {len(transactions)} transaksi dari {len(files)} file ke tracefund.db")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import file transaksi Markdown ke SQLite")
    parser.add_argument(
        "--source-dir",
        default=r"C:\Users\BEST LAPTOP\Downloads\pengeluaran uang",
        help="Folder yang berisi file Markdown transaksi",
    )
    args = parser.parse_args()
    seed_database(args.source_dir)
