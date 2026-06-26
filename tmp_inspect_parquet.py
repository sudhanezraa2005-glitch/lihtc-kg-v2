from pathlib import Path
import pandas as pd

for path in [Path('data/silver/fhfa/tract_hpi.parquet'), Path('data/silver/fhfa/conforming_limits.parquet')]:
    df = pd.read_parquet(path)
    print('FILE:', path)
    print('COLUMNS:', list(df.columns))
    print('DTYPES:')
    print(df.dtypes.to_dict())
    print('---')
