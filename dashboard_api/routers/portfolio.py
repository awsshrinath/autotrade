from fastapi import APIRouter, Depends
import sys
import os

# Add project root to path to allow importing 'services'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from services.portfolio_manager import PortfolioManager, Portfolio
from utils.gcp_utils import get_firestore_client
from google.cloud.firestore_v1.client import Client

router = APIRouter()

# Dependency for PortfolioManager
def get_portfolio_manager(db: Client = Depends(get_firestore_client)) -> PortfolioManager:
    return PortfolioManager(firestore_client=db)


@router.get("/overview", response_model=Portfolio)
async def get_portfolio_overview(
    portfolio_manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """
    Retrieves the current overview of the entire trading portfolio,
    including total value, cash, open positions, and performance metrics.
    """
    return portfolio_manager.get_portfolio_overview() 