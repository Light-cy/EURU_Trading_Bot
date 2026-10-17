"""Version the existing trade, signal, and account-stat tables.

Revision ID: 0001_legacy
Revises:
"""
from alembic import context, op
import sqlalchemy as sa

revision = "0001_legacy"
down_revision = None
branch_labels = None
depends_on = None


TABLES = {
    "trades": {
        "columns": {
            "id",
            "pair",
            "signal",
            "entry_price",
            "exit_price",
            "stop_loss",
            "take_profit",
            "position_size",
            "status",
            "profit_loss",
            "profit_loss_pips",
            "profit_loss_percent",
            "entry_time",
            "exit_time",
            "close_reason",
            "indicator_signals",
            "smc_signals",
            "confidence",
        },
        "indexes": (("ix_trades_id", ["id"], False),),
    },
    "signal_logs": {
        "columns": {
            "id",
            "pair",
            "timestamp",
            "signal",
            "confidence",
            "buy_count",
            "sell_count",
            "neutral_count",
            "reason",
            "indicator_results",
            "smc_results",
            "was_executed",
        },
        "indexes": (
            ("ix_signal_logs_id", ["id"], False),
            ("ix_signal_logs_timestamp", ["timestamp"], False),
        ),
    },
    "account_stats": {
        "columns": {
            "id",
            "date",
            "starting_balance",
            "ending_balance",
            "daily_profit_loss",
            "daily_profit_loss_percent",
            "trades_won",
            "trades_lost",
            "total_trades",
            "win_rate",
            "max_drawdown",
            "sharpe_ratio",
        },
        "indexes": (
            ("ix_account_stats_id", ["id"], False),
            ("ix_account_stats_date", ["date"], True),
        ),
    },
}


def _create_table_if_missing(table_name: str) -> None:
    if not context.is_offline_mode():
        inspector = sa.inspect(op.get_bind())
        if inspector.has_table(table_name):
            actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
            missing_columns = TABLES[table_name]["columns"] - actual_columns
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise RuntimeError(
                    f"Cannot baseline {table_name}: existing table is missing columns: {missing}"
                )
            return

    if table_name == "trades":
        op.create_table(
            "trades",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("pair", sa.String(length=20), nullable=True),
            sa.Column("signal", sa.String(length=10), nullable=True),
            sa.Column("entry_price", sa.Float(), nullable=True),
            sa.Column("exit_price", sa.Float(), nullable=True),
            sa.Column("stop_loss", sa.Float(), nullable=True),
            sa.Column("take_profit", sa.Float(), nullable=True),
            sa.Column("position_size", sa.Float(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("profit_loss", sa.Float(), nullable=True),
            sa.Column("profit_loss_pips", sa.Float(), nullable=True),
            sa.Column("profit_loss_percent", sa.Float(), nullable=True),
            sa.Column("entry_time", sa.DateTime(), nullable=True),
            sa.Column("exit_time", sa.DateTime(), nullable=True),
            sa.Column("close_reason", sa.String(length=100), nullable=True),
            sa.Column("indicator_signals", sa.Text(), nullable=True),
            sa.Column("smc_signals", sa.Text(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
        )
    elif table_name == "signal_logs":
        op.create_table(
            "signal_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("pair", sa.String(length=20), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.Column("signal", sa.String(length=10), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("buy_count", sa.Integer(), nullable=True),
            sa.Column("sell_count", sa.Integer(), nullable=True),
            sa.Column("neutral_count", sa.Integer(), nullable=True),
            sa.Column("reason", sa.String(length=500), nullable=True),
            sa.Column("indicator_results", sa.Text(), nullable=True),
            sa.Column("smc_results", sa.Text(), nullable=True),
            sa.Column("was_executed", sa.Boolean(), nullable=True),
        )
    elif table_name == "account_stats":
        op.create_table(
            "account_stats",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("date", sa.DateTime(), nullable=True),
            sa.Column("starting_balance", sa.Float(), nullable=True),
            sa.Column("ending_balance", sa.Float(), nullable=True),
            sa.Column("daily_profit_loss", sa.Float(), nullable=True),
            sa.Column("daily_profit_loss_percent", sa.Float(), nullable=True),
            sa.Column("trades_won", sa.Integer(), nullable=True),
            sa.Column("trades_lost", sa.Integer(), nullable=True),
            sa.Column("total_trades", sa.Integer(), nullable=True),
            sa.Column("win_rate", sa.Float(), nullable=True),
            sa.Column("max_drawdown", sa.Float(), nullable=True),
            sa.Column("sharpe_ratio", sa.Float(), nullable=True),
        )


def upgrade() -> None:
    for table_name in TABLES:
        _create_table_if_missing(table_name)

    for table_name, table_config in TABLES.items():
        existing_indexes = (
            set()
            if context.is_offline_mode()
            else {
                index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)
            }
        )
        for index_name, columns, unique in table_config["indexes"]:
            if index_name not in existing_indexes:
                op.create_index(index_name, table_name, columns, unique=unique)


def downgrade() -> None:
    for table_name in reversed(tuple(TABLES)):
        op.drop_table(table_name)
