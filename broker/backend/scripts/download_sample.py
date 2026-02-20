"""Download a sample COTAHIST file for testing"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.b3_cotahist import B3CotahistService
from app.config import settings


async def main():
    """Download COTAHIST for 2024"""
    output_dir = settings.data_dir / "b3_cotahist"
    output_dir.mkdir(parents=True, exist_ok=True)

    service = B3CotahistService()

    print("📥 Downloading COTAHIST 2024...")

    try:
        # Download ZIP
        zip_content = await service.download_cotahist(2024)

        # Extract TXT
        txt_content = service.extract_txt_from_zip(zip_content)

        # Save to file
        output_file = output_dir / "COTAHIST_A2024.txt"
        output_file.write_text(txt_content, encoding='latin-1')

        print(f"✅ Downloaded and saved to: {output_file}")
        print(f"   File size: {len(txt_content):,} bytes")
        print(f"   Lines: {len(txt_content.splitlines()):,}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
