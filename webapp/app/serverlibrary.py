import numpy as np
import pandas as pd
from app import db
from app.models import User, Post, FarmerData
from typing import Optional

# Precomputed values from training (Polynomial Model)
# These represent means and standard deviations for normalization
PRECOMPUTED_MEANS = [
    3.16531154e+19, 2.46629167e+01, 5.98605000e+06,
    2.33238799e+02, 8.41371250e+04, 7.03379420e+07
]
PRECOMPUTED_STDS = [
    1.09002043e+19, 3.72910614e-01, 5.00222329e+05, 
    1.59659474e+02, 9.56351764e+04, 1.87028452e+07
]

# Final trained beta coefficients for the multiple linear regression model
BETA_FINAL = np.array([
    [ 2.30270515e+08], # Intercept
    [-1.92163191e+06],
    [ 1.99882125e+07],
    [ 1.82389237e+08],
    [-3.79494624e+07],
    [-4.23365272e+07],
    [-5.93943483e+07]
])

def split_data(
    df_feature: pd.DataFrame, df_target: pd.DataFrame,
    random_state: Optional[int] = None,
    test_size: float = 0.5
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into training and testing sets.

    Parameters:
        df_feature (pd.DataFrame): Feature dataset.
        df_target (pd.DataFrame): Target dataset.
        random_state (Optional[int]): Seed for randomization.
        test_size (float): Proportion of the dataset to include in the test split.

    Returns:
        tuple: Training features, testing features, training targets, testing targets.
    """
    if random_state is not None:
        np.random.seed(random_state)

    num_samples_feature = df_feature.shape[0]
    num_test_samples = int(test_size * num_samples_feature)

    # Randomly select indices for the test set
    test_indices = np.random.choice(num_samples_feature, num_test_samples, replace=False)
    df_feature_test = df_feature.loc[test_indices, :]
    df_target_test = df_target.loc[test_indices, :]
    df_feature_train = df_feature.drop(test_indices)
    df_target_train = df_target.drop(test_indices)

    return df_feature_train, df_feature_test, df_target_train, df_target_test


def normalize_z(
    array: np.ndarray, 
    columns_means: Optional[np.ndarray] = None,
    columns_stds: Optional[np.ndarray] = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Normalize data using z-score normalization.

    Parameters:
        array (np.ndarray): Input array to normalize.
        columns_means (Optional[np.ndarray]): Precomputed column means.
        columns_stds (Optional[np.ndarray]): Precomputed column standard deviations.

    Returns:
        tuple: Normalized array, column means, column standard deviations.
    """
    if columns_means is None:
        columns_means = array.mean(axis=0)
    if columns_stds is None:
        columns_stds = array.std(axis=0)

    out = (array - columns_means) / columns_stds
    return out, columns_means, columns_stds


def prepare_feature(np_feature: np.ndarray) -> np.ndarray:
    """
    Add a bias (intercept) term to the feature matrix.

    Parameters:
        np_feature (np.ndarray): Feature matrix.

    Returns:
        np.ndarray: Feature matrix with an added bias term.
    """
    row = np_feature.shape[0]
    ones = np.ones((row, 1))
    return np.concatenate((ones, np_feature), axis=1)


def calc_linreg(X: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """
    Calculate predictions using linear regression.

    Parameters:
        X (np.ndarray): Feature matrix.
        beta (np.ndarray): Coefficients.

    Returns:
        np.ndarray: Predicted values.
    """
    return np.matmul(X, beta)


def predict_linreg(
    array_feature: np.ndarray, beta: np.ndarray,
    means: Optional[np.ndarray] = None, 
    stds: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Predict using a linear regression model.

    Parameters:
        array_feature (np.ndarray): Feature array.
        beta (np.ndarray): Regression coefficients.
        means (Optional[np.ndarray]): Precomputed means for normalization.
        stds (Optional[np.ndarray]): Precomputed standard deviations for normalization.

    Returns:
        np.ndarray: Predicted values.
    """
    standardized_feature, _, _ = normalize_z(array_feature, means, stds)
    X_prepared = prepare_feature(standardized_feature)
    predictions = calc_linreg(X_prepared, beta)
    return predictions


def compute_cost_linreg(X: np.ndarray, y: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """
    Compute the cost for linear regression.

    Parameters:
        X (np.ndarray): Feature matrix.
        y (np.ndarray): Target values.
        beta (np.ndarray): Coefficients.

    Returns:
        np.ndarray: Cost value.
    """
    m = y.shape[0]
    predictions = calc_linreg(X, beta)
    errors = predictions - y
    J = (1 / (2 * m)) * np.matmul(errors.T, errors)
    return np.squeeze(J)


def gradient_descent_linreg(
    X: np.ndarray, y: np.ndarray, beta: np.ndarray, 
    alpha: float, num_iters: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Perform gradient descent for linear regression.

    Parameters:
        X (np.ndarray): Feature matrix.
        y (np.ndarray): Target values.
        beta (np.ndarray): Initial coefficients.
        alpha (float): Learning rate.
        num_iters (int): Number of iterations.

    Returns:
        tuple: Final coefficients, cost history.
    """
    row = y.shape[0]
    J_storage = np.zeros(num_iters)

    for i in range(num_iters):
        predictions = calc_linreg(X, beta)
        gradient = (1 / row) * np.matmul(X.T, (predictions - y))
        beta -= alpha * gradient
        J_storage[i] = compute_cost_linreg(X, y, beta)

    return beta, J_storage


def create_post(title: str, content: str, user_id: int):
    """
    Create a new forum post.

    Parameters:
        title (str): Title of the post.
        content (str): Content of the post.
        user_id (int): Author's user ID.
    """
    new_post = Post(title=title, content=content, user_id=user_id)
    db.session.add(new_post)
    db.session.commit()


def get_all_posts() -> list:
    """
    Retrieve all posts from the database.

    Returns:
        list: All posts ordered by timestamp.
    """
    return Post.query.order_by(Post.timestamp.desc()).all()


def add_farmer_production(user_id: int, year: int, production: float):
    """
    Add production data for a farmer.

    Parameters:
        user_id (int): Farmer's user ID.
        year (int): Year of production.
        production (float): Production amount.
    """
    new_data = FarmerData(user_id=user_id, year=year, production=production)
    db.session.add(new_data)
    db.session.commit()


def get_farmer_data(user_id: int) -> list:
    """
    Get all production data for a specific farmer.

    Parameters:
        user_id (int): Farmer's user ID.

    Returns:
        list: List of tuples (year, production).
    """
    data = FarmerData.query.filter_by(user_id=user_id).order_by(FarmerData.year).all()
    return [(entry.year, entry.production) for entry in data]
