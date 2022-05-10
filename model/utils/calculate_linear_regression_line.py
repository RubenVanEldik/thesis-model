from sklearn.linear_model import LinearRegression

import validate


def calculate_linear_regression_line(col1, col2):
    """
    Calculate the X and Y values for a linear regression line
    """
    assert validate.is_series(col1)
    assert validate.is_series(col2)

    # Initialize the linear regression model
    model = LinearRegression()

    # Set the X and y values
    X = col1.to_frame()
    y = col2

    # Fit the regression model and calculate the R-squared value
    model.fit(X, y)

    # Return the R-squared value
    return X, model.predict(X)
