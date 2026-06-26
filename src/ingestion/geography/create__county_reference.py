from pathlib import Path
import pandas as pd

INPUT = Path("data/silver/geography/tract_reference.parquet")
OUTPUT = Path("data/silver/geography/county_reference.parquet")


def main():
    tract_df = pd.read_parquet(INPUT)

    county_df = (
        tract_df[
            [
                "county_fips",
                "state_fips",
                "county_code",
                "county_name",
            ]
        ]
        .drop_duplicates()
        .sort_values("county_fips")
    )

    county_df.to_parquet(OUTPUT, index=False)

    print(f"Counties: {len(county_df)}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()