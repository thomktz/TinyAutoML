import logging
from typing import Optional, Union

import pandas as pd
from numpy import ndarray
from sklearn.ensemble import RandomForestClassifier

from ...support.MyTools import checkClassBalance, getAdaptedCrossVal
from ..EstimatorPools.EstimatorPool import EstimatorPool
from ..EstimatorPools.EstimatorPoolCV import EstimatorPoolCV
from ..MetaModel import MetaModel

pd.options.mode.chained_assignment = None  # default='warn'


class OneRulerForAll(MetaModel):
    """
    The OneRulerForAll bottleneck estimator uses stacking techniques to leverage the strengths of estimators in the pool.
    We first train a pool of estimator, then another 'ruler' estimator is trained to decide which estimator in
    the pool might be right, given the pool outputs
    """

    def __init__(
        self,
        comprehensiveSearch: bool = True,
        parameterTuning: bool = True,
        metrics: str = "accuracy",
        nSplits: int = 10,
        ruler=RandomForestClassifier(),
    ):

        self.ruler = ruler
        self.estimatorPool: Optional[Union[EstimatorPoolCV, EstimatorPool]] = None
        self.comprehensiveSearch = comprehensiveSearch
        self.nSplits = nSplits
        self.parameterTuning = parameterTuning
        self.metrics = metrics

    def fit(self, X: pd.DataFrame, y: pd.Series) -> MetaModel:

        checkClassBalance(y)

        logging.info("Training models...")

        cv = getAdaptedCrossVal(X, self.nSplits)

        if self.estimatorPool is None:
            self.estimatorPool = (
                EstimatorPoolCV() if self.comprehensiveSearch else EstimatorPool()
            )
            # Training the pool
            if self.parameterTuning:
                self.estimatorPool.fitWithParameterTuning(X, y, cv, self.metrics)
            else:
                self.estimatorPool.fit(X, y)

        estimatorsPoolOutputs = self.estimatorPool.predict(X)

        self.ruler.fit(estimatorsPoolOutputs, y)

        return self

    # Overriding sklearn BaseEstimator methods
    def predict(self, X: pd.DataFrame) -> Union[pd.Series, ndarray, list[ndarray]]:
        assert (
            self.estimatorPool is not None and self.estimatorPool.is_fitted
        ), "Please fit the model before"
        estimatorsPoolOutputs = self.estimatorPool.predict(X)

        return self.ruler.predict(estimatorsPoolOutputs)

    def predict_proba(
        self, X: pd.DataFrame
    ) -> Union[pd.Series, ndarray, list[ndarray]]:
        assert (
            self.estimatorPool is not None and self.estimatorPool.is_fitted
        ), "Please fit the model before"
        estimatorsPoolOutputs = self.estimatorPool.predict(X)
        return self.ruler.predict_proba(estimatorsPoolOutputs)

    def transform(self, X: pd.DataFrame):
        return X

    def __repr__(self, **kwargs):
        return "ORFA"
