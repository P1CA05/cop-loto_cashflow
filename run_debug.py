"""
Debug runner to catch all errors
"""
import sys
import traceback

try:
    import app
    print("=" * 60)
    print("Starting Flask app with full error handling")
    print("=" * 60)
    app.app.run(host='0.0.0.0', port=5000, debug=False)
except Exception as e:
    print("=" * 60)
    print("FATAL ERROR:")
    print("=" * 60)
    print(f"Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("=" * 60)
    input("Press Enter to exit...")
