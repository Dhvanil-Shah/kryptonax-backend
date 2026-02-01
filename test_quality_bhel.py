from quality_score import calculate_quality_score
import json

ticker = "BHEL.BO"
print(f"\nTesting quality score for {ticker}...")
result = calculate_quality_score(ticker)

if result and "error" in result:
    print(f"\n❌ ERROR: {result['error']}")
    print(f"Message: {result.get('message', 'N/A')}")
else:
    print(f"\n✅ SUCCESS!")
    print(f"Company: {result.get('company_name', 'N/A')}")
    print(f"Overall Score: {result.get('overall_score', 'N/A')}/100")
    print(f"Grade: {result.get('grade', 'N/A')}")
    print(f"Verdict: {result.get('verdict', 'N/A')}")
