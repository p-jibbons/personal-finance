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
