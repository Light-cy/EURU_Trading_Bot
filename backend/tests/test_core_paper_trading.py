import unittest
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.trading_system.execution.executor import TradeExecutor
from src.trading_system.database import models as database_models
from src.trading_system.config.settings import _env_bool, _validate_market_data_mode
from src.trading_system.ai import train_model
from src.trading_system.backtesting.run_backtest import load_historical_csv
from src.trading_system.market import real_mt5
from src.trading_system import main as trading_main
from src.trading_system.risk.manager import RiskManager
from src.trading_system.smc.manager import SMCManager


class RiskManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = RiskManager(account_balance=10_000, risk_percent=1)

    def test_fixed_risk_buy_calculates_position_and_reward(self):
        result = self.manager.calculate_position(
            current_price=1.1,
            stop_loss_pips=50,
            signal="BUY",
        )

        self.assertEqual(result.position_size, 0.2)
        self.assertEqual(result.stop_loss, 1.095)
        self.assertEqual(result.take_profit, 1.11)
        self.assertEqual(result.risk_amount, 100)
        self.assertEqual(result.reward_amount, 200)
        self.assertEqual(result.risk_reward_ratio, 2)

    def test_sell_prices_are_mirrored_and_size_rounding_does_not_exceed_budget(self):
        result = self.manager.calculate_position(
            current_price=1.1,
            stop_loss_pips=50,
            signal="SELL",
        )

        self.assertEqual(result.stop_loss, 1.105)
        self.assertEqual(result.take_profit, 1.09)
        self.assertLessEqual(result.risk_amount, 100)
        self.assertEqual(result.risk_reward_ratio, 2)

    def test_lot_size_rounding_down_stays_within_risk_budget(self):
        manager = RiskManager(account_balance=10_100, risk_percent=1)
        result = manager.calculate_position(
            current_price=1.1,
            stop_loss_pips=50,
            signal="BUY",
        )

        self.assertEqual(result.position_size, 0.2)
        self.assertEqual(result.risk_amount, 100)
        self.assertLessEqual(result.risk_amount, 101)

    def test_atr_in_price_units_converts_to_pips(self):
        result = self.manager.calculate_position(
            current_price=1.1,
            stop_loss_pips=50,
            signal="BUY",
            atr_value=0.001,
        )

        self.assertEqual(result.stop_loss, 1.099)
        self.assertEqual(result.take_profit, 1.102)

    def test_rejects_invalid_signal(self):
        with self.assertRaisesRegex(ValueError, "signal must be BUY or SELL"):
            self.manager.calculate_position(
                current_price=1.1,
                stop_loss_pips=50,
                signal="HOLD",
            )


class TradeExecutorTests(unittest.TestCase):
    def test_opens_paper_position_without_connecting_or_sending_broker_order(self):
        market_data = Mock()
        market_data.connected = False
        market_data.connect.side_effect = AssertionError("executor must not connect")
        executor = TradeExecutor(market_data)

        result = executor.execute_buy(
            pair="EURUSD",
            entry_price=1.1,
            stop_loss=1.095,
            take_profit=1.11,
            position_size=0.2,
            confidence=0.9,
            indicator_signals={},
            smc_signals={},
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["execution_mode"], "paper")
        self.assertEqual(len(executor.open_trades), 1)
        market_data.connect.assert_not_called()


class DatabaseMigrationTests(unittest.TestCase):
    def test_database_manager_requires_migrations_instead_of_creating_tables(self):
        with (
            patch.object(
                database_models,
                "_migration_revisions",
                return_value=(None, "0001_legacy"),
            ),
            patch.object(database_models.Base.metadata, "create_all") as create_all,
        ):
            with self.assertRaisesRegex(RuntimeError, "migration state is uninitialized"):
                database_models.DatabaseManager()

        create_all.assert_not_called()


class SyntheticDataBoundaryTests(unittest.TestCase):
    def test_environment_boolean_rejects_unrecognized_values(self):
        with patch.dict("os.environ", {"TEST_FLAG": "sometimes"}):
            with self.assertRaisesRegex(ValueError, "must be 'true' or 'false'"):
                _env_bool("TEST_FLAG", False)

    def test_ml_startup_fails_when_artifact_is_unavailable(self):
        system = object.__new__(trading_main.TradingSystem)
        with (
            patch.object(trading_main.settings, "USE_ML_MODEL", True),
            patch.object(trading_main, "XGBoostSignalModel") as model_class,
        ):
            model_class.return_value.is_trained = False
            with self.assertRaisesRegex(RuntimeError, "no valid trained model"):
                system._init_ml_model()

    def test_model_loader_rejects_artifacts_without_provenance_metadata(self):
        from src.trading_system.ai.model import XGBoostSignalModel

        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / "model.pkl"
            model_path.write_bytes(b"unverified-model")
            model_path.with_name("model_scaler.pkl").write_bytes(b"unverified-scaler")
            model = XGBoostSignalModel(
                model_path=str(model_path),
                expected_pair="EURUSD",
            )

            model.load()

        self.assertFalse(model.is_trained)

    def test_model_loader_checks_real_data_metadata_and_artifact_hashes(self):
        from src.trading_system.ai.model import XGBoostSignalModel

        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / "model.pkl"
            scaler_path = Path(directory) / "model_scaler.pkl"
            dataset_path = Path(directory) / "training_dataset_EURUSD.csv"
            model_path.write_bytes(b"model")
            scaler_path.write_bytes(b"scaler")
            dataset_path.write_bytes(b"real-source-data")

            model = XGBoostSignalModel(
                model_path=str(model_path),
                expected_pair="EURUSD",
            )
            with self.assertRaisesRegex(ValueError, "read-only MT5"):
                model.save_training_metadata(
                    data_source="synthetic",
                    pair="EURUSD",
                    timeframe="M15",
                    dataset_path=str(dataset_path),
                )

            model.save_training_metadata(
                data_source="mt5_read_only",
                pair="EURUSD",
                timeframe="M15",
                dataset_path=str(dataset_path),
            )
            with patch("src.trading_system.ai.model.joblib.load", side_effect=[object(), object()]):
                model.load()
            self.assertTrue(model.is_trained)

            scaler_path.write_bytes(b"modified-scaler")
            stale_model = XGBoostSignalModel(
                model_path=str(model_path),
                expected_pair="EURUSD",
            )
            stale_model.load()
            self.assertFalse(stale_model.is_trained)

            scaler_path.write_bytes(b"scaler")
            dataset_path.write_bytes(b"modified-source-data")
            stale_dataset_model = XGBoostSignalModel(
                model_path=str(model_path),
                expected_pair="EURUSD",
            )
            stale_dataset_model.load()
            self.assertFalse(stale_dataset_model.is_trained)

    def test_synthetic_market_data_is_restricted_to_development_and_tests(self):
        for environment in ("development", "test"):
            with self.subTest(environment=environment):
                _validate_market_data_mode(environment, True)

        for environment in ("production", "staging"):
            with self.subTest(environment=environment):
                with self.assertRaisesRegex(ValueError, "restricted"):
                    _validate_market_data_mode(environment, True)

        _validate_market_data_mode("production", False)

    def test_model_training_refuses_synthetic_data_without_connecting(self):
        with (
            patch.object(train_model.settings, "MOCK_MT5", True),
            patch.object(train_model, "RealMT5") as real_mt5,
            self.assertRaisesRegex(RuntimeError, "synthetic market data"),
        ):
            train_model.main()

        real_mt5.assert_not_called()

    def test_backtest_requires_caller_supplied_historical_data(self):
        with self.assertRaisesRegex(FileNotFoundError, "not found"):
            load_historical_csv(Path("/missing/historical-data.csv"))

    def test_backtest_rejects_unsorted_or_invalid_candles(self):
        import pandas as pd

        rows = [
            {
                "time": (
                    datetime(2026, 1, 1, tzinfo=timezone.utc)
                    + timedelta(minutes=minute)
                ).isoformat(),
                "open": 1.1,
                "high": 1.101,
                "low": 1.099,
                "close": 1.1,
                "volume": 100,
            }
            for minute in range(201)
        ]
        rows[2]["time"] = rows[1]["time"]
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candles.csv"
            pd.DataFrame(rows).to_csv(csv_path, index=False)
            with self.assertRaisesRegex(ValueError, "ascending, unique"):
                load_historical_csv(csv_path)

    def test_backtest_rejects_inconsistent_ohlc_values(self):
        import pandas as pd

        rows = [
            {
                "time": (
                    datetime(2026, 1, 1, tzinfo=timezone.utc)
                    + timedelta(minutes=minute)
                ).isoformat(),
                "open": 1.1,
                "high": 1.101,
                "low": 1.099,
                "close": 1.1,
                "volume": 100,
            }
            for minute in range(201)
        ]
        rows[0]["high"] = 1.09
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candles.csv"
            pd.DataFrame(rows).to_csv(csv_path, index=False)
            with self.assertRaisesRegex(ValueError, "invalid OHLC"):
                load_historical_csv(csv_path)

    def test_backtest_accepts_valid_historical_candle_csv(self):
        import pandas as pd

        rows = [
            {
                "time": (
                    datetime(2026, 1, 1, tzinfo=timezone.utc)
                    + timedelta(minutes=minute)
                ).isoformat(),
                "open": 1.1,
                "high": 1.101,
                "low": 1.099,
                "close": 1.1,
                "volume": 100,
            }
            for minute in range(201)
        ]
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "candles.csv"
            pd.DataFrame(rows).to_csv(csv_path, index=False)
            data = load_historical_csv(csv_path)

        self.assertEqual(len(data), 201)
        self.assertTrue(data["time"].is_monotonic_increasing)


class SMCResponseContractTests(unittest.TestCase):
    def test_payload_uses_the_shape_consumed_by_dashboard(self):
        manager = SMCManager()
        manager.structure.analyze = Mock(
            return_value=SimpleNamespace(
                bos="BULLISH",
                choch="NONE",
                trend="UPTREND",
                confidence=0.8,
                reason="test",
            )
        )
        manager.ob_detector.detect = Mock(
            return_value={
                "signal": "BUY",
                "confidence": 0.88,
                "reason": "test",
                "ob": {"type": "BULLISH", "top": 1.1, "bottom": 1.09},
            }
        )
        manager.fvg_detector.detect = Mock(
            return_value={
                "signal": "SELL",
                "confidence": 0.82,
                "reason": "test",
                "fvg": {"type": "BEARISH", "top": 1.1, "bottom": 1.09},
            }
        )

        result = manager.run_all(Mock())

        self.assertEqual(set(result), {"structure", "order_block", "fvg"})
        self.assertIn("choch", result["structure"])
        self.assertEqual(result["order_block"]["ob"]["type"], "BULLISH")
        self.assertEqual(result["fvg"]["signal"], "SELL")


class ReadOnlyMT5Tests(unittest.TestCase):
    def test_failed_real_connection_does_not_fall_back_to_mock(self):
        real_client = Mock()
        real_client.connect.return_value = False
        system = trading_main.TradingSystem.__new__(trading_main.TradingSystem)

        with (
            patch.object(trading_main.settings, "MOCK_MT5", False),
            patch.object(trading_main, "RealMT5", return_value=real_client),
            patch.object(trading_main, "MockMT5") as mock_client,
        ):
            with self.assertRaisesRegex(RuntimeError, "Refusing to fall back"):
                system._init_mt5()

        mock_client.assert_not_called()

    def test_reports_account_market_and_realized_costs_without_orders(self):
        fake_mt5 = SimpleNamespace(
            account_info=lambda: SimpleNamespace(
                balance=9_950.0,
                equity=10_000.0,
                margin=100.0,
                margin_free=9_900.0,
                currency="USD",
                login=12345,
                server="Demo",
                trade_allowed=True,
            ),
            symbol_info_tick=lambda pair: SimpleNamespace(
                bid=1.0999,
                ask=1.1001,
                time=1_700_000_000,
            ),
            history_deals_get=lambda start, end: [
                SimpleNamespace(profit=25.0, commission=-2.0, swap=-1.0, fee=-0.5),
                SimpleNamespace(profit=-5.0, commission=-1.0, swap=0.0),
            ],
            last_error=lambda: "test error",
        )
        client = real_mt5.RealMT5(pair="EURUSD")
        client.connected = True

        with patch.object(real_mt5, "mt5", fake_mt5):
            account = client.get_account_info()
            market = client.get_current_price()
            performance = client.get_recent_performance(days=30)

        self.assertEqual(account["balance"], 9_950.0)
        self.assertEqual(account["server"], "Demo")
        self.assertAlmostEqual(market["spread"], 0.0002)
        self.assertEqual(performance["deal_count"], 2)
        self.assertEqual(performance["commission"], -3.0)
        self.assertEqual(performance["swap"], -1.0)
        self.assertEqual(performance["fees"], -0.5)
        self.assertEqual(performance["net_realized"], 15.5)

    def test_rejects_unavailable_account_data(self):
        fake_mt5 = SimpleNamespace(
            account_info=lambda: None,
            last_error=lambda: "terminal unavailable",
        )
        client = real_mt5.RealMT5(pair="EURUSD")
        client.connected = True

        with patch.object(real_mt5, "mt5", fake_mt5):
            with self.assertRaisesRegex(RuntimeError, "terminal unavailable"):
                client.get_account_info()


if __name__ == "__main__":
    unittest.main()
