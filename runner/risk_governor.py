from datetime import datetime

class RiskGovernor:
    def __init__(self, max_daily_loss, max_trades, cutoff_time="15:00"):
        self.max_daily_loss = max_daily_loss
        self.max_trades = max_trades
        self.cutoff_time = cutoff_time
        self.total_loss = 0
        self.trade_count = 0

    def update_trade(self, pnl):
        self.total_loss += pnl
        self.trade_count += 1

    def can_trade(self):
        now = datetime.now().strftime("%H:%M")
        if self.total_loss <= -self.max_daily_loss:
            print(f"❌ RiskGovernor: Max daily loss reached ({self.total_loss}). No more trades.")
            return False
        if self.trade_count >= self.max_trades:
            print(f"❌ RiskGovernor: Max trades reached ({self.trade_count}).")
            return False
        if now >= self.cutoff_time:
            print(f"⏰ RiskGovernor: Time cutoff reached ({now} ≥ {self.cutoff_time}).")
            return False
        return True

    def reset_day(self):
        self.total_loss = 0
        self.trade_count = 0
