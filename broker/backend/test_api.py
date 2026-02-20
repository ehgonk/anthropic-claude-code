"""Quick API test script"""

import httpx
import json

base_url = "http://localhost:8001"

def test_endpoints():
    """Test all API endpoints"""

    print("🧪 Testing B3 Broker API\n")
    print("=" * 60)

    # Test 1: Root endpoint
    print("\n1️⃣ GET /")
    try:
        response = httpx.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: List stocks (first page)
    print("\n2️⃣ GET /api/stocks?page=1&page_size=5")
    try:
        response = httpx.get(f"{base_url}/api/stocks", params={"page": 1, "page_size": 5})
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Total stocks: {data['total']}")
        print(f"   Page: {data['page']}/{(data['total'] + data['page_size'] - 1) // data['page_size']}")
        print(f"   Stocks on this page:")
        for stock in data['stocks']:
            print(f"      - {stock['symbol']:10s} {stock['name']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Search stocks
    print("\n3️⃣ GET /api/stocks?search=PETR")
    try:
        response = httpx.get(f"{base_url}/api/stocks", params={"search": "PETR"})
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Found {data['total']} stocks matching 'PETR':")
        for stock in data['stocks'][:5]:
            print(f"      - {stock['symbol']:10s} {stock['name']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Get specific stock
    print("\n4️⃣ GET /api/stocks/PETR4")
    try:
        response = httpx.get(f"{base_url}/api/stocks/PETR4")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            stock = response.json()
            print(f"   Symbol: {stock['symbol']}")
            print(f"   Name: {stock['name']}")
            print(f"   Price: R$ {stock['price']:.2f}")
            print(f"   Volume: {stock['volume']:,}")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 5: Get latest price
    print("\n5️⃣ GET /api/stocks/PETR4/latest")
    try:
        response = httpx.get(f"{base_url}/api/stocks/PETR4/latest")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            price = response.json()
            print(f"   Date: {price['date']}")
            print(f"   Open: R$ {price['open']:.2f}")
            print(f"   High: R$ {price['high']:.2f}")
            print(f"   Low: R$ {price['low']:.2f}")
            print(f"   Close: R$ {price['close']:.2f}")
            print(f"   Volume: {price['volume']:,}")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 6: Get price history
    print("\n6️⃣ GET /api/stocks/PETR4/prices?limit=7")
    try:
        response = httpx.get(f"{base_url}/api/stocks/PETR4/prices", params={"limit": 7})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Symbol: {data['symbol']}")
            print(f"   Total records: {data['total']}")
            print(f"   Last 7 days:")
            for price in data['prices']:
                print(f"      {price['date']}: R$ {price['close']:8.2f} (Vol: {price['volume']:,})")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 7: API documentation
    print("\n7️⃣ OpenAPI Documentation")
    print(f"   Swagger UI: {base_url}/docs")
    print(f"   ReDoc: {base_url}/redoc")
    print(f"   OpenAPI JSON: {base_url}/openapi.json")

    print("\n" + "=" * 60)
    print("✅ API tests completed!\n")


if __name__ == "__main__":
    test_endpoints()
