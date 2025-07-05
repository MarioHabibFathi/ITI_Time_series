import pandas as pd
import numpy as np
import io
import re
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import STL
import base64
from typing import Optional

class TimeSeriesEDA:
    def __init__(self, file_content: bytes, filename: str):
        self.file_content = file_content
        self.filename = filename
        self.sep = self._detect_separator()
        self.df = self._read_file()

    def _detect_separator(self) -> str:
        text = self.file_content.decode(errors='ignore')
        potential_seps = [',', '\t', ';', '|']
        counts = {sep: text.count(sep) for sep in potential_seps}
        return max(counts, key=counts.get)

    def _read_file(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(io.StringIO(self.file_content.decode()), sep=self.sep)
            return df
        except Exception as e:
            raise ValueError(f"Could not read file: {e}")

    def basic_info(self) -> dict:
        return {
            "shape": self.df.shape,
            "columns": list(self.df.columns),
            "dtypes": self.df.dtypes.astype(str).to_dict(),
            "nulls": self.df.isnull().sum().to_dict()
        }

    def column_value_counts(self, column: str, top_n: int = 10) -> dict:
        return self.df[column].value_counts().head(top_n).to_dict()

    def suggest_cast_type(self, column: str) -> str:
        series = self.df[column]
        try:
            pd.to_numeric(series.dropna(), errors='raise')
            return "numeric"
        except:
            pass
        try:
            pd.to_datetime(series.dropna(), errors='raise')
            return "datetime"
        except:
            pass
        return "string"

    def try_cast_column(self, column: str, dtype: str) -> dict:
        try:
            if dtype == 'numeric':
                casted = pd.to_numeric(self.df[column], errors='coerce')
            elif dtype == 'datetime':
                casted = pd.to_datetime(self.df[column], errors='coerce')
            else:
                casted = self.df[column].astype(dtype, errors='ignore')
        except Exception as e:
            return {"success": False, "error": str(e)}

        nulls_after_cast = casted.isnull().sum()
        total_rows = len(casted)
        if nulls_after_cast == 0:
            self.df[column] = casted
            return {"success": True, "message": f"Column {column} successfully cast to {dtype}."}
        else:
            return {
                "success": False,
                "message": f"{nulls_after_cast} / {total_rows} rows cannot be converted to {dtype}.",
                "convertible_rows": total_rows - nulls_after_cast,
                "non_convertible_rows": nulls_after_cast
            }

    def drop_non_convertible_rows(self, column: str, dtype: str) -> dict:
        if dtype == 'numeric':
            casted = pd.to_numeric(self.df[column], errors='coerce')
        elif dtype == 'datetime':
            casted = pd.to_datetime(self.df[column], errors='coerce')
        else:
            casted = self.df[column].astype(dtype, errors='ignore')

        before = len(self.df)
        self.df = self.df.loc[casted.notnull()].copy()
        self.df[column] = casted.loc[casted.notnull()]
        after = len(self.df)
        return {"dropped_rows": before - after, "remaining_rows": after}

    def check_datetime_column(self, datetime_col: str) -> dict:
        try:
            dt_series = pd.to_datetime(self.df[datetime_col], errors='coerce')
            null_count = dt_series.isnull().sum()
            if null_count > 0:
                return {"success": False, "message": f"{null_count} rows could not be converted to datetime."}
            return {"success": True, "message": "Datetime column is valid.", "min_date": dt_series.min(), "max_date": dt_series.max()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_frequency_applicability(self, datetime_col: str, freq: str) -> dict:
        dt_series = pd.to_datetime(self.df[datetime_col], errors='coerce').dropna().sort_values()
        inferred_freq = pd.infer_freq(dt_series)
        if inferred_freq is None:
            return {"applicable": False, "reason": "Irregular datetime intervals, frequency inference failed."}
        is_applicable = pd.date_range(start=dt_series.iloc[0], end=dt_series.iloc[-1], freq=freq).shape[0] > 0
        return {
            "applicable": is_applicable,
            "inferred_freq": inferred_freq,
            "reason": None if is_applicable else "Requested frequency does not align with data."
        }

    def preview_resample(self, datetime_col: str, freq: str, agg: str = 'mean', rows: int = 5) -> dict:
        self.df[datetime_col] = pd.to_datetime(self.df[datetime_col])
        self.df.set_index(datetime_col, inplace=True)
        resampled = self.df.resample(freq).agg(agg)
        return resampled.reset_index().head(rows).to_dict(orient='records')
    
    def seasonal_decomposition(self, datetime_col: str, target_col: str, freq: Optional[int] = None) -> str:
        self.df[datetime_col] = pd.to_datetime(self.df[datetime_col])
        self.df.set_index(datetime_col, inplace=True)
        series = self.df[target_col].dropna()

        if freq is None:
            freq = pd.infer_freq(series.index)
            if freq is None:
                raise ValueError("Could not infer frequency for STL decomposition.")
        
        stl = STL(series, period=freq if isinstance(freq, int) else None, robust=True)
        result = stl.fit()

        fig, ax = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
        ax[0].plot(series, label='Observed')
        ax[0].legend()
        ax[1].plot(result.trend, label='Trend')
        ax[1].legend()
        ax[2].plot(result.seasonal, label='Seasonal')
        ax[2].legend()
        ax[3].plot(result.resid, label='Residual')
        ax[3].legend()
        plt.tight_layout()

        return self._fig_to_base64(fig)

    def _fig_to_base64(self, fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')


    def _fig_to_base64(self, fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    def save_cleaned_csv(self) -> bytes:
        output = io.StringIO()
        self.df.to_csv(output, index=False, sep=self.sep)
        return output.getvalue().encode()
