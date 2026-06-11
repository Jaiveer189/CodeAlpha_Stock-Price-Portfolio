from flask import Flask, render_template, request, jsonify
from groq import Groq
import os

app = Flask(__name__)

# -------------------------------------------------------
# Hard-coded stock price dictionary
# -------------------------------------------------------
stock_prices = {
    "AAPL":  {"price": 190,  "name": "Apple"},
    "GOOGL": {"price": 2800, "name": "Google"},
    "AMZN":  {"price": 3400, "name": "Amazon"},
    "MSFT":  {"price": 300,  "name": "Microsoft"},
    "TSLA":  {"price": 700,  "name": "Tesla"},
}

@app.route("/")
def index():
    return render_template("index.html", stocks=stock_prices)

@app.route("/calculate", methods=["POST"])
def calculate():
    data      = request.get_json()
    portfolio = data.get("portfolio", {})

    results          = []
    total_investment = 0

    for symbol, quantity in portfolio.items():
        if symbol not in stock_prices:
            continue
        price       = stock_prices[symbol]["price"]
        name        = stock_prices[symbol]["name"]
        stock_value = quantity * price
        total_investment += stock_value
        results.append({
            "symbol":   symbol,
            "name":     name,
            "quantity": quantity,
            "price":    price,
            "value":    stock_value,
        })

    return jsonify({
        "results": results,
        "total":   total_investment,
        "count":   len(results),
        "shares":  sum(r["quantity"] for r in results),
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    data    = request.get_json()
    results = data.get("results", [])
    total   = data.get("total", 0)

    if not results:
        return jsonify({"error": "No portfolio data received."}), 400

    lines = [
        f"{r['symbol']} ({r['name']}): {r['quantity']} shares "
        f"@ ${r['price']:,} = ${r['value']:,}"
        for r in results
    ]
    portfolio_text = "\n".join(lines)

    prompt = f"""You are a financial portfolio advisor. Analyze this stock portfolio:

{portfolio_text}

Total investment: ${total:,}

Please provide:
1. Portfolio Summary — what this portfolio looks like at a glance
2. Risk Assessment — is it too concentrated in one stock?
3. Diversification Feedback — are all stocks in the same sector?
4. Suggestions — what to consider adding or rebalancing
5. Plain English Verdict — one paragraph a beginner can understand

Keep the tone friendly, clear, and educational. Not financial advice.
"""

    try:
        # Groq client reads GROQ_API_KEY from environment variable
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        # llama-3.3-70b-versatile — Groq's best free model, very fast
        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 1024,
        )
        analysis = response.choices[0].message.content

    except Exception as e:
        return jsonify({"error": f"Groq API error: {str(e)}"}), 500

    return jsonify({"analysis": analysis})


if __name__ == "__main__":
    app.run(debug=True)