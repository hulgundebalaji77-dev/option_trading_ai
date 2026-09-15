class RiskEngine:
    def _init_(self, rr_ratio: float = 2.0):
        self.rr = rr_ratio

    def get_trade_levels(self, price: float, atr: float, action: str) -> dict:
        sl_points = round(max(atr * 1.5, 20.0), 1)
        tgt_points = round(sl_points * self.rr, 1)

        if action == "BUY_CE":
            sl = round(price - sl_points, 1)
            tgt = round(price + tgt_points, 1)
        elif action == "BUY_PE":
            sl = round(price + sl_points, 1)
            tgt = round(price - tgt_points, 1)
        else:
            return {}

        return {
            "entry": price,
            "sl": sl,
            "target": tgt,
            "sl_pts": sl_points,
            "tgt_pts": tgt_points
        }
