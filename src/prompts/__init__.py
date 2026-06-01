SYSTEM_PROMPT = """You are ChainMind, a multi-modal onchain intelligence assistant.
You analyze blockchain data including charts, documents, transactions, and wallets."""

def get_template(template_name: str) -> str:
    templates = {
        "analysis": "Analyze the provided {data_type} and provide insights.",
        "summary": "Summarize the key findings from {data}."
    }
    return templates.get(template_name, "")
