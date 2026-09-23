import logging
import os
import sqlite3
from datetime import datetime

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
try:
    ALLOWED_USER_ID = int(os.environ["ALLOWED_USER_ID"])
except (KeyError, ValueError):
    raise RuntimeError("ALLOWED_USER_ID harus berupa angka di file .env")
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN belum diisi di file .env")

DATABASE_PATH = "tracefund.db"
MONTH_NAMES = (
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("tracefund")


def initialize_database() -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('masuk', 'keluar')),
            amount INTEGER NOT NULL CHECK(amount >= 0),
            description TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS budgets (
            month TEXT PRIMARY KEY,
            amount INTEGER NOT NULL CHECK(amount > 0)
        )""")


def format_rupiah(amount: int) -> str:
    sign = "- " if amount < 0 else ""
    return f"{sign}Rp{abs(amount):,.0f}".replace(",", ".")


def format_rupiah_aligned(amount: int, width: int) -> str:
    value = format_rupiah(amount)
    if amount >= 0:
        value = "  " + value
    return f"{value:<{width}}"


def format_month(month_key: str) -> str:
    year, month = month_key.split("-")
    return f"{MONTH_NAMES[int(month) - 1]} {year}"


def is_allowed_user(interaction: discord.Interaction) -> bool:
    return interaction.user.id == ALLOWED_USER_ID


async def reject_unauthorized(interaction: discord.Interaction) -> None:
    message = "Kamu tidak memiliki akses ke bot ini."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class TraceFundClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        initialize_database()
        synced = await self.tree.sync()
        logger.info("Berhasil sync %d slash command", len(synced))

    async def on_ready(self) -> None:
        for guild in self.guilds:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("Berhasil sync %d command ke server %s", len(synced), guild.name)
        logger.info("Bot online sebagai %s", self.user)


client = TraceFundClient()


@client.tree.command(name="pemasukan", description="Catat pemasukan baru")
@app_commands.describe(nominal="Nominal dalam rupiah", deskripsi="Sumber pemasukan")
async def pemasukan(interaction: discord.Interaction, nominal: int, deskripsi: str) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    if nominal <= 0:
        await interaction.response.send_message("Nominal harus lebih dari 0.", ephemeral=True)
        return
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "INSERT INTO transactions (date, type, amount, description) VALUES (?, 'masuk', ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), nominal, deskripsi.strip()),
        )
    await interaction.response.send_message(
        f"Pemasukan {format_rupiah(nominal)} untuk **{deskripsi.strip()}** berhasil dicatat.",
        ephemeral=True,
    )


@client.tree.command(name="pengeluaran", description="Catat pengeluaran baru")
@app_commands.describe(nominal="Nominal dalam rupiah", barang="Nama barang atau kebutuhan")
async def pengeluaran(interaction: discord.Interaction, nominal: int, barang: str) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    if nominal <= 0:
        await interaction.response.send_message("Nominal harus lebih dari 0.", ephemeral=True)
        return
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "INSERT INTO transactions (date, type, amount, description) VALUES (?, 'keluar', ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), nominal, barang.strip()),
        )
    await interaction.response.send_message(
        f"Pengeluaran {format_rupiah(nominal)} untuk **{barang.strip()}** berhasil dicatat.",
        ephemeral=True,
    )


@client.tree.command(name="riwayat", description="Lihat transaksi terakhir")
@app_commands.describe(bulan="Opsional: bulan 1-12", tahun="Opsional: tahun")
async def riwayat(
    interaction: discord.Interaction, bulan: int | None = None, tahun: int | None = None
) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    if bulan is not None and not 1 <= bulan <= 12:
        await interaction.response.send_message("Bulan harus 1-12.", ephemeral=True)
        return
    if tahun is not None and not 2000 <= tahun <= 2100:
        await interaction.response.send_message("Tahun harus valid.", ephemeral=True)
        return
    filters = []
    parameters: list[str] = []
    if tahun is not None:
        filters.append("date LIKE ?")
        parameters.append(f"{tahun:04d}-%")
    if bulan is not None:
        filters.append("date LIKE ?")
        parameters.append(f"{tahun or datetime.now().year:04d}-{bulan:02d}-%")
    where_clause = f" WHERE {' AND '.join(filters)}" if filters else ""
    period_filtered = bulan is not None or tahun is not None
    limit_clause = "" if period_filtered else " LIMIT 15"
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT id, date, type, amount, description FROM transactions"
            + where_clause
            + " ORDER BY date ASC, id ASC"
            + limit_clause,
            parameters,
        ).fetchall()
    if not rows:
        await interaction.response.send_message("Tidak ada transaksi pada periode tersebut.", ephemeral=True)
        return
    period = "15 transaksi terakhir"
    if period_filtered:
        period = "Detail transaksi"
        if bulan is not None:
            period += f" {MONTH_NAMES[bulan - 1]} {tahun or datetime.now().year}"
        elif tahun is not None:
            period += f" tahun {tahun}"
    lines = []
    income = expense = 0
    income_count = expense_count = 0
    for transaction_id, date, transaction_type, amount, description in rows:
        if transaction_type == "masuk":
            income += amount
            income_count += 1
        else:
            expense += amount
            expense_count += 1
    summary = (
        f"**{period}**\n"
        f"Pemasukan ({income_count}): {format_rupiah(income)}\n"
        f"Pengeluaran ({expense_count}): {format_rupiah(expense)}\n"
        f"Saldo: {format_rupiah(income - expense)}\n\n"
    )
    if period_filtered:
        income_rows = [
            (transaction_id, date[:10], amount, description)
            for transaction_id, date, transaction_type, amount, description in rows
            if transaction_type == "masuk"
        ]
        expense_rows = [
            (transaction_id, date[:10], amount, description)
            for transaction_id, date, transaction_type, amount, description in rows
            if transaction_type == "keluar"
        ]
        row_count = max(len(income_rows), len(expense_rows))
        income_width = max(12, *(len(format_rupiah(amount)) for _, _, amount, _ in income_rows))
        expense_width = max(12, *(len(format_rupiah(amount)) for _, _, amount, _ in expense_rows))
        left_values = [
            f"#{transaction_id} {date} {format_rupiah_aligned(amount, income_width)} {description}"
            for transaction_id, date, amount, description in income_rows
        ]
        right_values = [
            f"#{transaction_id} {date} {format_rupiah_aligned(amount, expense_width)} {description}"
            for transaction_id, date, amount, description in expense_rows
        ]
        left_width = max(38, len("PEMASUKAN"), *(len(value) for value in left_values))
        right_width = max(38, len("PENGELUARAN"), *(len(value) for value in right_values))
        table_lines = [
            f"{'PEMASUKAN':<{left_width}} | PENGELUARAN",
            "-" * left_width + "-+-" + "-" * right_width,
        ]
        for index in range(row_count):
            left = left_values[index] if index < len(left_values) else ""
            right = right_values[index] if index < len(right_values) else ""
            table_lines.append(f"{left:<{left_width}} | {right}")
        table = "```text\n" + "\n".join(table_lines) + "\n```"
        await interaction.response.send_message(summary + table, ephemeral=True)
        return

    lines = [
        f"`#{transaction_id}` {date[:10]} | {transaction_type:<6} | "
        f"{format_rupiah(amount):>12} | {description}"
        for transaction_id, date, transaction_type, amount, description in rows
    ]
    chunks = []
    current_chunk = summary
    for line in lines:
        if len(current_chunk) + len(line) + 1 > 1900:
            chunks.append(current_chunk)
            current_chunk = "**Detail transaksi (lanjutan)**\n"
        current_chunk += line + "\n"
    if current_chunk.strip():
        chunks.append(current_chunk)
    await interaction.response.send_message(chunks[0], ephemeral=True)
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk, ephemeral=True)


@client.tree.command(name="ubah", description="Ubah transaksi berdasarkan ID")
@app_commands.describe(id_transaksi="ID dari command /riwayat", nominal="Nominal baru", deskripsi="Deskripsi baru")
async def ubah(interaction: discord.Interaction, id_transaksi: int, nominal: int, deskripsi: str) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    if nominal <= 0 or not deskripsi.strip():
        await interaction.response.send_message("Nominal harus lebih dari 0 dan deskripsi wajib diisi.", ephemeral=True)
        return
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "UPDATE transactions SET amount = ?, description = ? WHERE id = ?",
            (nominal, deskripsi.strip(), id_transaksi),
        )
    if cursor.rowcount == 0:
        await interaction.response.send_message("Transaksi dengan ID tersebut tidak ditemukan.", ephemeral=True)
        return
    await interaction.response.send_message(f"Transaksi #{id_transaksi} berhasil diubah.", ephemeral=True)


@client.tree.command(name="hapus", description="Hapus transaksi berdasarkan ID")
@app_commands.describe(id_transaksi="ID dari command /riwayat")
async def hapus(interaction: discord.Interaction, id_transaksi: int) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute("DELETE FROM transactions WHERE id = ?", (id_transaksi,))
    if cursor.rowcount == 0:
        await interaction.response.send_message("Transaksi dengan ID tersebut tidak ditemukan.", ephemeral=True)
        return
    await interaction.response.send_message(f"Transaksi #{id_transaksi} berhasil dihapus.", ephemeral=True)


def validate_period(bulan: int | None, tahun: int | None) -> bool:
    return (bulan is None or 1 <= bulan <= 12) and (tahun is None or 2000 <= tahun <= 2100)


@client.tree.command(name="budget", description="Tetapkan batas pengeluaran bulanan")
@app_commands.describe(nominal="Batas pengeluaran", bulan="Opsional: bulan 1-12", tahun="Opsional: tahun")
async def budget(
    interaction: discord.Interaction,
    nominal: int,
    bulan: int | None = None,
    tahun: int | None = None,
) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    if nominal <= 0 or not validate_period(bulan, tahun):
        await interaction.response.send_message("Nominal harus lebih dari 0, bulan 1-12, dan tahun harus valid.", ephemeral=True)
        return
    now = datetime.now()
    month_key = f"{tahun or now.year:04d}-{bulan or now.month:02d}"
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "INSERT INTO budgets (month, amount) VALUES (?, ?) "
            "ON CONFLICT(month) DO UPDATE SET amount = excluded.amount",
            (month_key, nominal),
        )
    await interaction.response.send_message(
        f"Budget {format_month(month_key)} ditetapkan sebesar {format_rupiah(nominal)}.",
        ephemeral=True,
    )


@client.tree.command(name="cekbudget", description="Cek pemakaian budget bulanan")
@app_commands.describe(bulan="Opsional: bulan 1-12", tahun="Opsional: tahun")
async def cekbudget(
    interaction: discord.Interaction, bulan: int | None = None, tahun: int | None = None
) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    if not validate_period(bulan, tahun):
        await interaction.response.send_message("Bulan harus 1-12 dan tahun harus valid.", ephemeral=True)
        return
    now = datetime.now()
    month_key = f"{tahun or now.year:04d}-{bulan or now.month:02d}"
    with sqlite3.connect(DATABASE_PATH) as connection:
        budget_row = connection.execute("SELECT amount FROM budgets WHERE month = ?", (month_key,)).fetchone()
        spent = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'keluar' AND date LIKE ?",
            (month_key + "-%",),
        ).fetchone()[0]
    if budget_row is None:
        await interaction.response.send_message(
            f"Belum ada budget untuk {format_month(month_key)}. Gunakan /budget terlebih dahulu.",
            ephemeral=True,
        )
        return
    limit = budget_row[0]
    remaining = limit - spent
    status = "tersisa" if remaining >= 0 else "melebihi batas"
    await interaction.response.send_message(
        f"**Budget {format_month(month_key)}**\n"
        f"Batas: {format_rupiah(limit)}\n"
        f"Terpakai: {format_rupiah(spent)}\n"
        f"{status.title()}: {format_rupiah(abs(remaining))}",
        ephemeral=True,
    )


@client.tree.command(name="ringkasan", description="Lihat ringkasan keuangan bulan tertentu")
@app_commands.describe(bulan="Bulan 1-12, kosongkan untuk bulan ini", tahun="Tahun, kosongkan untuk tahun ini")
async def ringkasan(
    interaction: discord.Interaction, bulan: int | None = None, tahun: int | None = None
) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    now = datetime.now()
    bulan = bulan or now.month
    tahun = tahun or now.year
    if not 1 <= bulan <= 12 or not 2000 <= tahun <= 2100:
        await interaction.response.send_message("Bulan harus 1-12 dan tahun harus valid.", ephemeral=True)
        return
    prefix = f"{tahun:04d}-{bulan:02d}-%"
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT type, COALESCE(SUM(amount), 0), COUNT(*) FROM transactions WHERE date LIKE ? GROUP BY type",
            (prefix,),
        ).fetchall()
    totals = {transaction_type: (amount, count) for transaction_type, amount, count in rows}
    masuk, masuk_count = totals.get("masuk", (0, 0))
    keluar, keluar_count = totals.get("keluar", (0, 0))
    await interaction.response.send_message(
        f"**Ringkasan {bulan:02d}/{tahun}**\n"
        f"Pemasukan ({masuk_count}): {format_rupiah(masuk)}\n"
        f"Pengeluaran ({keluar_count}): {format_rupiah(keluar)}\n"
        f"Saldo: {format_rupiah(masuk - keluar)}",
        ephemeral=True,
    )


@client.tree.command(name="total", description="Hitung total pengeluaran untuk suatu barang")
@app_commands.describe(
    barang="Nama barang atau kategori, misalnya cukur atau bensin",
    bulan="Opsional: bulan 1-12",
    tahun="Opsional: tahun",
)
async def total(
    interaction: discord.Interaction,
    barang: str,
    bulan: int | None = None,
    tahun: int | None = None,
) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    barang = barang.strip()
    if not barang:
        await interaction.response.send_message("Nama barang tidak boleh kosong.", ephemeral=True)
        return
    if bulan is not None and not 1 <= bulan <= 12:
        await interaction.response.send_message("Bulan harus 1-12.", ephemeral=True)
        return
    if tahun is not None and not 2000 <= tahun <= 2100:
        await interaction.response.send_message("Tahun harus valid.", ephemeral=True)
        return

    filters = ["type = 'keluar'", "description LIKE ? COLLATE NOCASE"]
    parameters: list[object] = [f"%{barang}%"]
    if tahun is not None:
        filters.append("date LIKE ?")
        parameters.append(f"{tahun:04d}-%")
    if bulan is not None:
        filters.append("date LIKE ?")
        parameters.append(f"{tahun or datetime.now().year:04d}-{bulan:02d}-%")
    query = (
        "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM transactions WHERE "
        + " AND ".join(filters)
    )
    with sqlite3.connect(DATABASE_PATH) as connection:
        amount, count = connection.execute(query, parameters).fetchone()

    period = "sepanjang waktu"
    if bulan is not None:
        period = f"bulan {bulan:02d}/{tahun or datetime.now().year}"
    elif tahun is not None:
        period = f"tahun {tahun}"
    await interaction.response.send_message(
        f"**Total pengeluaran untuk '{barang}' ({period})**\n"
        f"{count} transaksi: {format_rupiah(amount)}",
        ephemeral=True,
    )


@client.tree.command(name="analisis", description="Cari bulan terbaik dan terbesar dari keuanganmu")
async def analisis(interaction: discord.Interaction) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute("""
            SELECT substr(date, 1, 7) AS month,
                   COALESCE(SUM(CASE WHEN type = 'masuk' THEN amount ELSE 0 END), 0) AS income,
                   COALESCE(SUM(CASE WHEN type = 'keluar' THEN amount ELSE 0 END), 0) AS expense
            FROM transactions
            GROUP BY month
            ORDER BY month
        """).fetchall()
    if not rows:
        await interaction.response.send_message("Belum ada transaksi untuk dianalisis.", ephemeral=True)
        return

    month_data = [
        (month, income, expense, income - expense)
        for month, income, expense in rows
    ]
    highest_income = max(month_data, key=lambda item: item[1])
    highest_expense = max(month_data, key=lambda item: item[2])
    best_balance = max(month_data, key=lambda item: item[3])
    worst_balance = min(month_data, key=lambda item: item[3])

    await interaction.response.send_message(
        "**Analisis Keuangan Semua Bulan**\n"
        f"Pemasukan terbesar: **{format_month(highest_income[0])}** - {format_rupiah(highest_income[1])}\n"
        f"Pengeluaran terbesar: **{format_month(highest_expense[0])}** - {format_rupiah(highest_expense[2])}\n"
        f"Saldo terbaik: **{format_month(best_balance[0])}** - {format_rupiah(best_balance[3])}\n"
        f"Saldo terburuk: **{format_month(worst_balance[0])}** - {format_rupiah(worst_balance[3])}\n\n"
        "Detail per bulan akan dikirim setelah pesan ini.",
        ephemeral=True,
    )
    formatted_data = [
        (format_month(month), format_rupiah(income), format_rupiah(expense), format_rupiah(balance))
        for month, income, expense, balance in month_data
    ]
    month_width = max(len("BULAN"), *(len(row[0]) for row in formatted_data))
    income_width = max(len("PEMASUKAN"), *(len(row[1]) for row in formatted_data))
    expense_width = max(len("PENGELUARAN"), *(len(row[2]) for row in formatted_data))
    balance_width = max(len("SALDO"), *(len(row[3]) for row in formatted_data))
    detail_lines = [
        f"{month:<{month_width}}  {income:<{income_width}}  "
        f"{expense:<{expense_width}}  {balance:<{balance_width}}"
        for month, income, expense, balance in formatted_data
    ]
    chunks = []
    table_header = (
        f"{'BULAN':<{month_width}} | {'PEMASUKAN':<{income_width}} | "
        f"{'PENGELUARAN':<{expense_width}} | {'SALDO':<{balance_width}}\n"
    )
    table_separator = (
        "-" * month_width + "-+-" + "-" * income_width + "-+-"
        + "-" * expense_width + "-+-" + "-" * balance_width + "\n"
    )
    current_chunk = "**Detail Semua Bulan**\n```text\n" + table_header + table_separator
    for line in detail_lines:
        if len(current_chunk) + len(line) + 4 > 1800:
            chunks.append(current_chunk + "```")
            current_chunk = "**Detail Semua Bulan (lanjutan)**\n```text\n" + table_header + table_separator
        current_chunk += line + "\n"
    if current_chunk.strip():
        chunks.append(current_chunk + "```")
    for chunk in chunks:
        await interaction.followup.send(chunk, ephemeral=True)


@client.tree.command(name="tahunan", description="Lihat total pemasukan dan pengeluaran dalam satu tahun")
@app_commands.describe(tahun="Opsional: tahun yang ingin dilihat")
async def tahunan(interaction: discord.Interaction, tahun: int | None = None) -> None:
    if not is_allowed_user(interaction):
        await reject_unauthorized(interaction)
        return
    tahun = tahun or datetime.now().year
    if not 2000 <= tahun <= 2100:
        await interaction.response.send_message("Tahun harus valid.", ephemeral=True)
        return
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT type, COALESCE(SUM(amount), 0), COUNT(*) "
            "FROM transactions WHERE date LIKE ? GROUP BY type",
            (f"{tahun:04d}-%",),
        ).fetchall()
    totals = {transaction_type: (amount, count) for transaction_type, amount, count in rows}
    income, income_count = totals.get("masuk", (0, 0))
    expense, expense_count = totals.get("keluar", (0, 0))
    await interaction.response.send_message(
        f"**Ringkasan Tahunan {tahun}**\n"
        f"Pemasukan ({income_count} transaksi): {format_rupiah(income)}\n"
        f"Pengeluaran ({expense_count} transaksi): {format_rupiah(expense)}\n"
        f"Saldo: {format_rupiah(income - expense)}",
        ephemeral=True,
    )


@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    logger.error("Command error", exc_info=error)
    if isinstance(error, app_commands.CommandInvokeError) and isinstance(error.original, sqlite3.Error):
        message = "Database sedang bermasalah. Cek log bot."
    else:
        message = "Terjadi kesalahan saat menjalankan command. Cek log bot."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


client.run(DISCORD_TOKEN)