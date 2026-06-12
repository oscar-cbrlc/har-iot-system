from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pandas as pd
import numpy as np

class MagnitudeCalculatorTransformer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_copy = X.copy()
        X_copy['accel_mag'] = np.sqrt(X_copy['accel_x']**2 + X_copy['accel_y']**2 + X_copy['accel_z']**2)
        X_copy['gyro_mag'] = np.sqrt(X_copy['pitch']**2 + X_copy['roll']**2 + X_copy['yaw']**2)
        return X_copy

def median_filter(data, window_size):
  median_filtered = data.copy()
  median_filtered = median_filtered.rolling(window=window_size, center=True, min_periods=1).median()
  return median_filtered

class MedianFilterTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, window_size=5, numeric_cols=['accel_mag', 'gyro_mag']):
        self.window_size = window_size
        self.numeric_cols = numeric_cols

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input X must be a pandas DataFrame.")

        if 'activity' in X.columns:
            df_filtered_list = []
            for activity_name in X['activity'].unique():
                df_activity = X[X['activity'] == activity_name].copy()
                filtered_data = median_filter(df_activity[self.numeric_cols], self.window_size)
                df_activity[self.numeric_cols] = filtered_data
                df_filtered_list.append(df_activity)
            return pd.concat(df_filtered_list).reset_index(drop=True)
        else:
            filtered_data = median_filter(X[self.numeric_cols], self.window_size)
            X_copy = X.copy()
            X_copy[self.numeric_cols] = filtered_data
            return X_copy

class FeatureExtractorTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, window_size=5):
        self.window_size = window_size

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Input X must be a pandas DataFrame.")

        if 'accel_mag' not in X.columns or 'gyro_mag' not in X.columns:
            raise ValueError("DataFrame must contain 'accel_mag', and 'gyro_mag' columns.")

        processed_dfs = []
        if 'activity' in X.columns:
            for activity_name in X['activity'].unique():
                df_activity = X[X['activity'] == activity_name].copy()
                df_activity['window_id'] = np.arange(len(df_activity)) // self.window_size
                processed_dfs.append(df_activity)
            df_processed_with_windows = pd.concat(processed_dfs).reset_index(drop=True)
            groupby_cols = ['activity', 'window_id']
        else:
            X_copy = X.copy()
            X_copy['window_id'] = np.arange(len(X_copy)) // self.window_size
            df_processed_with_windows = X_copy
            groupby_cols = ['window_id']

        ml_features = df_processed_with_windows.groupby(groupby_cols).agg(
            accel_mean=('accel_mag', 'mean'),
            accel_var=('accel_mag', 'var'),
            gyro_mean=('gyro_mag', 'mean'),
            gyro_var=('gyro_mag', 'var'),
            accel_max=('accel_mag', 'max'),
            accel_min=('accel_mag', 'min'),
            gyro_max=('gyro_mag', 'max'),
            gyro_min=('gyro_mag', 'min'),
        ).reset_index()

        ml_features = ml_features.dropna()

        return ml_features


class FullPreprocessingTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, median_window_size=5, feature_window_size=5):
        self.median_window_size = median_window_size
        self.feature_window_size = feature_window_size
        self.magnitude_step = MagnitudeCalculatorTransformer()
        self.median_filter_step = MedianFilterTransformer(window_size=median_window_size)
        self.feature_extractor_step = FeatureExtractorTransformer(window_size=feature_window_size)
        self.scaler_step = StandardScaler()
        #self.label_encoder_step = LabelEncoder()
        self.feature_columns = None

    def fit(self, X, y=None):
        X_mag = self.magnitude_step.transform(X)
        X_med = self.median_filter_step.fit_transform(X_mag)
        ml_features_temp = self.feature_extractor_step.fit_transform(X_med)


        self.feature_columns = [col for col in ml_features_temp.columns if col not in ['activity', 'window_id']]
        self.scaler_step.fit(ml_features_temp[self.feature_columns])
        #self.label_encoder_step.fit(ml_features_temp['activity'])

        return self

    def transform(self, X):
        X_mag = self.magnitude_step.transform(X)
        X_med = self.median_filter_step.transform(X_mag)
        ml_features_transformed = self.feature_extractor_step.transform(X_med)

        if self.feature_columns is None:
            raise RuntimeError("Pipeline must be fitted before transforming.")

        X_scaled = self.scaler_step.transform(ml_features_transformed[self.feature_columns])

        output_df = pd.DataFrame(X_scaled, columns=self.feature_columns)

        return output_df

full_preprocessing_pipeline = FullPreprocessingTransformer(
    median_window_size=5,
    feature_window_size=5
)
