from typing import Tuple, List
import numpy as np
from sklearn.linear_model import LinearRegression

# Create a Linear Regression model
model = LinearRegression()


# Last 10 values of each bearing, x, z
def predict(bearing: np.ndarray[float], x: np.ndarray[float], z: np.ndarray[float], d_t: float) -> List[float]:
    start_t = 10
    d_t *= (20 / 1000) * 2

    pred_t_values = np.linspace(start_t, start_t + d_t, 100)
    vx = np.diff(x)
    vz = np.diff(z)
    bearing = - np.arctan2(vx, vz) * 180 / np.pi + 90
    v = np.sqrt(np.power(vx, 2) + np.power(vz, 2))

    t_values = np.arange(10)

    # Reshape the 1D arrays to 2D
    t_values = t_values.reshape(-1, 1)
    bearing = bearing.reshape(-1, 1)

    model.fit(t_values[:-1], v)
    v_slope = model.coef_[0]
    v_intercept = model.intercept_

    pred_v = np.mean(v_slope * pred_t_values + v_intercept)

    # Fit the model to your data
    model.fit(t_values[:-1], bearing)

    # Get the coefficients
    b_slope = model.coef_[0]
    b_intercept = model.intercept_

    pred_bearing = np.mean(b_slope * pred_t_values + b_intercept) * np.pi / 180

    return [x[-1] + np.cos(pred_bearing) * pred_v * d_t, z[-1] + np.sin(pred_bearing) * pred_v * d_t]
