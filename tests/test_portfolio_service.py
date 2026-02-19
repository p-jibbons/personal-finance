import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from app.services.portfolio_service import (
    load_portfolio,
    save_portfolio,
    add_position,
    delete_position,
    enrich_portfolio,
    get_position_performance,
)


@pytest.fixture
def temp_portfolio_dir(monkeypatch):
    """Create a temporary directory for portfolio CSV during tests."""
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / "test_portfolio.csv"

    # Patch the PORTFOLIO_FILE constant to use temp file
    monkeypatch.setattr("app.services.portfolio_service.PORTFOLIO_FILE", temp_file)

    yield temp_file

    # Cleanup
    shutil.rmtree(temp_dir)


class TestLoadPortfolio:
    """Tests for load_portfolio function."""

    def test_load_portfolio_creates_file_if_not_exists(self, temp_portfolio_dir):
        """Test that load_portfolio creates a new CSV with
        correct columns if file doesn't exist."""
        assert not temp_portfolio_dir.exists()

        df = load_portfolio()

        assert temp_portfolio_dir.exists()
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert list(df.columns) == ["symbol", "buy_date", "shares", "sell_date"]

    def test_load_portfolio_reads_existing_file(self, temp_portfolio_dir):
        """Test that load_portfolio correctly reads an existing CSV file."""
        # Create a test CSV file
        test_data = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT"],
                "buy_date": ["2024-01-01", "2024-02-01"],
                "shares": [10, 20],
                "sell_date": ["", "2024-03-01"],
            }
        )
        temp_portfolio_dir.parent.mkdir(parents=True, exist_ok=True)
        test_data.to_csv(temp_portfolio_dir, index=False)

        df = load_portfolio()

        assert len(df) == 2
        assert df.loc[0, "symbol"] == "AAPL"
        assert df.loc[1, "symbol"] == "MSFT"
        assert df.loc[0, "shares"] == 10


class TestSavePortfolio:
    """Tests for save_portfolio function."""

    def test_save_portfolio_creates_directory_if_not_exists(self, temp_portfolio_dir):
        """Test that save_portfolio creates parent directory if it doesn't exist."""
        # Remove the directory if it exists from fixture
        if temp_portfolio_dir.parent.exists():
            shutil.rmtree(temp_portfolio_dir.parent)

        assert not temp_portfolio_dir.parent.exists()

        test_df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "buy_date": ["2024-01-01"],
                "shares": [10],
                "sell_date": [""],
            }
        )

        save_portfolio(test_df)

        assert temp_portfolio_dir.exists()
        assert temp_portfolio_dir.parent.exists()

    def test_save_portfolio_writes_correct_data(self, temp_portfolio_dir):
        """Test that save_portfolio writes data correctly to CSV."""
        test_df = pd.DataFrame(
            {
                "symbol": ["GOOGL"],
                "buy_date": ["2024-06-15"],
                "shares": [5],
                "sell_date": [""],
            }
        )

        save_portfolio(test_df)

        # Read back and verify
        saved_df = pd.read_csv(temp_portfolio_dir)
        assert len(saved_df) == 1
        assert saved_df.loc[0, "symbol"] == "GOOGL"
        assert saved_df.loc[0, "shares"] == 5


class TestAddPosition:
    """Tests for add_position function."""

    def test_add_position_to_empty_portfolio(self, temp_portfolio_dir):
        """Test adding a position to an empty portfolio."""
        df = add_position("AAPL", "2024-01-15", 10.5)

        assert len(df) == 1
        assert df.loc[0, "symbol"] == "AAPL"
        assert df.loc[0, "buy_date"] == "2024-01-15"
        assert df.loc[0, "shares"] == 10.5
        assert df.loc[0, "sell_date"] == ""

    def test_add_position_with_sell_date(self, temp_portfolio_dir):
        """Test adding a position with a sell date."""
        df = add_position("MSFT", "2024-01-01", 20, "2024-06-01")

        assert len(df) == 1
        assert df.loc[0, "sell_date"] == "2024-06-01"

    def test_add_position_converts_symbol_to_uppercase(self, temp_portfolio_dir):
        """Test that symbol is converted to uppercase."""
        df = add_position("aapl", "2024-01-01", 5)

        assert df.loc[0, "symbol"] == "AAPL"

    def test_add_multiple_positions(self, temp_portfolio_dir):
        """Test adding multiple positions sequentially."""
        add_position("AAPL", "2024-01-01", 10)
        add_position("MSFT", "2024-02-01", 20)
        df = add_position("GOOGL", "2024-03-01", 5)

        assert len(df) == 3
        assert df.loc[0, "symbol"] == "AAPL"
        assert df.loc[1, "symbol"] == "MSFT"
        assert df.loc[2, "symbol"] == "GOOGL"

    def test_add_position_persists_to_file(self, temp_portfolio_dir):
        """Test that added position is actually saved to CSV file."""
        add_position("AAPL", "2024-01-01", 10)

        # Load directly from file
        saved_df = pd.read_csv(temp_portfolio_dir)
        assert len(saved_df) == 1
        assert saved_df.loc[0, "symbol"] == "AAPL"


class TestDeletePosition:
    """Tests for delete_position function."""

    def test_delete_position_by_index(self, temp_portfolio_dir):
        """Test deleting a position by index."""
        add_position("AAPL", "2024-01-01", 10)
        add_position("MSFT", "2024-02-01", 20)
        add_position("GOOGL", "2024-03-01", 5)

        df = delete_position(1)  # Delete MSFT

        assert len(df) == 2
        assert df.loc[0, "symbol"] == "AAPL"
        assert df.loc[1, "symbol"] == "GOOGL"

    def test_delete_position_reindexes_correctly(self, temp_portfolio_dir):
        """Test that indices are reset after deletion."""
        add_position("AAPL", "2024-01-01", 10)
        add_position("MSFT", "2024-02-01", 20)

        df = delete_position(0)  # Delete AAPL

        assert len(df) == 1
        assert df.index.tolist() == [0]  # Index should be reset to [0]
        assert df.loc[0, "symbol"] == "MSFT"

    def test_delete_position_persists_to_file(self, temp_portfolio_dir):
        """Test that deletion persists to the CSV file."""
        add_position("AAPL", "2024-01-01", 10)
        add_position("MSFT", "2024-02-01", 20)

        delete_position(0)

        # Load directly from file
        saved_df = pd.read_csv(temp_portfolio_dir)
        assert len(saved_df) == 1
        assert saved_df.loc[0, "symbol"] == "MSFT"

    def test_delete_last_remaining_position(self, temp_portfolio_dir):
        """Test deleting the last position results in empty portfolio."""
        add_position("AAPL", "2024-01-01", 10)

        df = delete_position(0)

        assert len(df) == 0
        assert df.empty


class TestPortfolioDataIntegrity:
    """Integration tests for data integrity across operations."""

    def test_load_save_cycle_preserves_data(self, temp_portfolio_dir):
        """Test that loading and saving preserves all data correctly."""
        original_df = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT", "GOOGL"],
                "buy_date": ["2024-01-01", "2024-02-01", "2024-03-01"],
                "shares": [10.5, 20.0, 5.25],
                "sell_date": ["", "2024-06-01", ""],
            }
        )

        save_portfolio(original_df)
        loaded_df = load_portfolio()

        pd.testing.assert_frame_equal(original_df, loaded_df)

    def test_empty_sell_dates_handled_correctly(self, temp_portfolio_dir):
        """Test that empty sell dates are handled consistently."""
        add_position("AAPL", "2024-01-01", 10, None)
        df = load_portfolio()

        assert df.loc[0, "sell_date"] == ""


class TestEnrichPortfolio:
    """Tests for enrich_portfolio function."""

    @pytest.fixture
    def mock_prices(self, monkeypatch):
        """Mock stock price functions to return fixed values."""

        def mock_get_close_price(symbol, date):
            # Return different prices based on symbol and date
            prices = {
                "AAPL": {"2024-01-01": 150.0, "2024-06-01": 180.0},
                "MSFT": {"2024-02-01": 300.0, "2024-07-01": 280.0},
                "GOOGL": {"2024-03-01": 140.0},
            }
            return prices.get(symbol, {}).get(date, 100.0)

        def mock_get_current_price(symbol):
            # Return current prices
            current_prices = {"AAPL": 200.0, "MSFT": 350.0, "GOOGL": 160.0}
            return current_prices.get(symbol, 100.0)

        monkeypatch.setattr(
            "app.services.portfolio_service.get_close_price", mock_get_close_price
        )
        monkeypatch.setattr(
            "app.services.portfolio_service.get_current_price",
            mock_get_current_price,
        )

    def test_enrich_empty_portfolio(self):
        """Test enriching an empty portfolio."""
        df = pd.DataFrame(
            {
                "symbol": pd.Series(dtype="str"),
                "buy_date": pd.Series(dtype="str"),
                "shares": pd.Series(dtype="float"),
                "sell_date": pd.Series(dtype="str"),
            }
        )
        enriched = enrich_portfolio(df)
        assert enriched.empty

    def test_enrich_open_position(self, mock_prices):
        """Test enriching an open position with current price."""
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "buy_date": ["2024-01-01"],
                "shares": [10.0],
                "sell_date": [""],
            }
        )

        enriched = enrich_portfolio(df)

        assert enriched.loc[0, "buy_price"] == 150.0
        assert enriched.loc[0, "current_price"] == 200.0
        assert enriched.loc[0, "cost_basis"] == 1500.0  # 10 * 150
        assert enriched.loc[0, "current_value"] == 2000.0  # 10 * 200
        assert enriched.loc[0, "gain_loss"] == 500.0  # 2000 - 1500
        assert enriched.loc[0, "gain_loss_pct"] == pytest.approx(33.33, rel=0.01)
        assert enriched.loc[0, "status"] == "Open"
        assert enriched.loc[0, "sell_price"] == 0.0
        assert enriched.loc[0, "sold_value"] == 0.0

    def test_enrich_closed_position(self, mock_prices):
        """Test enriching a closed position with sell price."""
        df = pd.DataFrame(
            {
                "symbol": ["MSFT"],
                "buy_date": ["2024-02-01"],
                "shares": [5.0],
                "sell_date": ["2024-07-01"],
            }
        )

        enriched = enrich_portfolio(df)

        assert enriched.loc[0, "buy_price"] == 300.0
        assert enriched.loc[0, "sell_price"] == 280.0
        assert enriched.loc[0, "cost_basis"] == 1500.0  # 5 * 300
        assert enriched.loc[0, "sold_value"] == 1400.0  # 5 * 280
        assert enriched.loc[0, "gain_loss"] == -100.0  # 1400 - 1500
        assert enriched.loc[0, "gain_loss_pct"] == pytest.approx(-6.67, rel=0.01)
        assert enriched.loc[0, "status"] == "Closed"
        assert enriched.loc[0, "current_price"] == 0.0
        assert enriched.loc[0, "current_value"] == 0.0

    def test_enrich_multiple_positions(self, mock_prices):
        """Test enriching portfolio with multiple positions."""
        df = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT", "GOOGL"],
                "buy_date": ["2024-01-01", "2024-02-01", "2024-03-01"],
                "shares": [10.0, 5.0, 8.0],
                "sell_date": ["", "2024-07-01", ""],
            }
        )

        enriched = enrich_portfolio(df)

        assert len(enriched) == 3
        assert enriched.loc[0, "status"] == "Open"
        assert enriched.loc[1, "status"] == "Closed"
        assert enriched.loc[2, "status"] == "Open"

        # Check AAPL (open)
        assert enriched.loc[0, "gain_loss"] == 500.0

        # Check MSFT (closed, loss)
        assert enriched.loc[1, "gain_loss"] == -100.0

        # Check GOOGL (open)
        assert enriched.loc[2, "cost_basis"] == 1120.0  # 8 * 140
        assert enriched.loc[2, "current_value"] == 1280.0  # 8 * 160

    def test_enrich_zero_cost_basis(self, mock_prices):
        """Test that zero cost basis doesn't cause division errors."""
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "buy_date": ["2024-01-01"],
                "shares": [0.0],
                "sell_date": [""],
            }
        )

        enriched = enrich_portfolio(df)

        assert enriched.loc[0, "cost_basis"] == 0.0
        assert enriched.loc[0, "gain_loss_pct"] == 0.0


class TestGetPositionPerformance:
    """Tests for get_position_performance function."""

    def test_performance_empty_portfolio(self):
        """Test performance analysis with empty portfolio."""
        df = pd.DataFrame()
        result = get_position_performance(df)

        assert result["top_gainers"].empty
        assert result["top_losers"].empty

    def test_performance_single_position(self):
        """Test performance analysis with single position."""
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "shares": [10.0],
                "cost_basis": [1500.0],
                "current_value": [2000.0],
                "sold_value": [0.0],
                "gain_loss": [500.0],
                "gain_loss_pct": [33.33],
                "status": ["Open"],
            }
        )

        result = get_position_performance(df)

        assert len(result["top_gainers"]) == 1
        assert len(result["top_losers"]) == 1
        assert result["top_gainers"].loc[0, "symbol"] == "AAPL"

    def test_performance_sorting(self):
        """Test that positions are sorted correctly by gain/loss percentage."""
        df = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"],
                "shares": [10.0, 5.0, 8.0, 3.0, 6.0],
                "cost_basis": [1000.0] * 5,
                "current_value": [1500.0, 800.0, 1200.0, 1100.0, 900.0],
                "sold_value": [0.0] * 5,
                "gain_loss": [500.0, -200.0, 200.0, 100.0, -100.0],
                "gain_loss_pct": [50.0, -20.0, 20.0, 10.0, -10.0],
                "status": ["Open"] * 5,
            }
        )

        result = get_position_performance(df)

        # Top gainers should be sorted descending
        assert result["top_gainers"].iloc[0]["symbol"] == "AAPL"  # 50%
        assert result["top_gainers"].iloc[1]["symbol"] == "GOOGL"  # 20%
        assert result["top_gainers"].iloc[2]["symbol"] == "TSLA"  # 10%

        # Top losers should be sorted ascending (most negative first)
        assert result["top_losers"].iloc[0]["symbol"] == "MSFT"  # -20%
        assert result["top_losers"].iloc[1]["symbol"] == "AMZN"  # -10%

    def test_performance_max_five_positions(self):
        """Test that only top 5 gainers and losers are returned."""
        # Create 10 positions
        symbols = [f"SYM{i}" for i in range(10)]
        percentages = list(range(-50, 50, 10))  # -50, -40, ..., 30, 40

        df = pd.DataFrame(
            {
                "symbol": symbols,
                "shares": [10.0] * 10,
                "cost_basis": [1000.0] * 10,
                "current_value": [1000.0] * 10,
                "sold_value": [0.0] * 10,
                "gain_loss": [0.0] * 10,
                "gain_loss_pct": percentages,
                "status": ["Open"] * 10,
            }
        )

        result = get_position_performance(df)

        assert len(result["top_gainers"]) == 5
        assert len(result["top_losers"]) == 5

        # Check top gainer is the highest percentage
        assert result["top_gainers"].iloc[0]["gain_loss_pct"] == 40.0

        # Check top loser is the lowest percentage
        assert result["top_losers"].iloc[0]["gain_loss_pct"] == -50.0
