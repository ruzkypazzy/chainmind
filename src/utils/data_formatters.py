"""Output formatting utilities"""

class DataFormatters:
    @staticmethod
    def format_address(address: str) -> str:
        if len(address) > 10:
            return f"{address[:6]}...{address[-4:]}"
        return address
    
    @staticmethod
    def format_usd(amount: float) -> str:
        return f"${amount:,.2f}"
