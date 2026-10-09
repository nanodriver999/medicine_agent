"""Opt-in ChEMBL API download. Requires network access; not called by CI."""
import argparse
from amo.chembl_data import fetch_pool, write_pool


def main():
    parser = argparse.ArgumentParser(description="Fetch a public ChEMBL molecule screening pool")
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--out", default="data/processed/chembl_pool.csv")
    args = parser.parse_args()
    rows, metadata = fetch_pool(args.count)
    if len(rows) < args.count:
        raise SystemExit(f"Only {len(rows)} candidates collected; requested {args.count}")
    manifest = write_pool(rows, metadata, args.out)
    print(f"Saved {len(rows)} unique canonical structures to {args.out}; "
          f"SHA256={manifest['sha256']}")


if __name__ == "__main__":
    main()
