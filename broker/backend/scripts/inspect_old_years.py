#!/usr/bin/env python3
"""
Inspect old B3 ZIP files to understand their internal structure
"""

import asyncio
import httpx
import zipfile
import io
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def inspect_year(year: int):
    """Inspect a single year's ZIP file structure"""
    url = f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"

    print(f"\n{'='*70}")
    print(f"📅 Inspecting year: {year}")
    print(f"🔗 URL: {url}")
    print(f"{'='*70}")

    # B3 requires proper headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8',
    }

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, headers=headers) as client:
            print("⬇️  Downloading...")
            response = await client.get(url)
            response.raise_for_status()

            print(f"✅ Downloaded {len(response.content) / 1024:.1f} KB")

            # Inspect ZIP contents
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                print(f"\n📦 ZIP contents ({len(zf.namelist())} files):")
                print(f"{'':>4} {'Filename':<40} {'Size (KB)':>12} {'Compressed':>12}")
                print(f"{'':>4} {'-'*40} {'-'*12} {'-'*12}")

                for i, file_info in enumerate(zf.infolist(), 1):
                    size_kb = file_info.file_size / 1024
                    compressed_kb = file_info.compress_size / 1024
                    print(f"{'':>4} {file_info.filename:<40} {size_kb:>11.1f}K {compressed_kb:>11.1f}K")

                # Try to peek at the first file's content
                if zf.namelist():
                    first_file = zf.namelist()[0]
                    print(f"\n📄 First 500 bytes of '{first_file}':")
                    print("-" * 70)

                    with zf.open(first_file) as f:
                        content = f.read(500)

                        # Try different encodings
                        for encoding in ['latin-1', 'utf-8', 'cp1252']:
                            try:
                                decoded = content.decode(encoding)
                                print(f"\n✅ Decoded with {encoding}:")
                                print(decoded[:500])
                                break
                            except:
                                continue
                        else:
                            print("❌ Could not decode - showing raw bytes:")
                            print(content[:500])

            return True

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code} - {e.response.reason_phrase}")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False


async def main():
    """Inspect multiple years"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  B3 ZIP INSPECTOR - Check old file formats                       ║
╚══════════════════════════════════════════════════════════════════╝

⚠️  Run this on Windows to avoid B3's firewall blocking!
    """)

    # Test problematic years
    years_to_test = [1994, 1995, 2000, 2001, 2002, 2025]

    results = {}
    for year in years_to_test:
        success = await inspect_year(year)
        results[year] = success

        # Be nice to B3 servers
        await asyncio.sleep(2)

    # Summary
    print("\n\n")
    print("="*70)
    print("📊 INSPECTION SUMMARY")
    print("="*70)

    for year, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{year}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
