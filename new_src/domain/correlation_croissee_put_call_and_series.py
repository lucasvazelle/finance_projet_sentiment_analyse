import os

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
import statsmodels.api as sm
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller, kpss


np.random.seed(42)
pd.options.mode.chained_assignment = None


class Preprocessing:
    def __init__(self) -> None:
        pass

    def __process_analysed_tweets(self, df: pd.DataFrame):
        # Format PostDate to datetime
        df["PostDate"] = pd.to_datetime(df["PostDate"])

        # drop rows with NaN values in the "PostDate" column
        df.dropna(subset=["PostDate"], inplace=True)

        # add a column for the year and month
        df["day"] = df["PostDate"].dt.day
        df["month"] = df["PostDate"].dt.month
        df["year"] = df["PostDate"].dt.year

        # formatting sentiments
        df["sentiment"] = df["sentiment"].map({"Bullish": 1, "Bearish": -1})
        df["sentiment_base"] = df["sentiment_base"].map(
            {"positive": 1, "neutral": 0, "negative": -1}
        )
        return df

    def __process_returns(self, df: pd.DataFrame):
        df = df / 100

        # Week-end
        nan_mask = df.isna().all(axis=1)
        df = df.loc[~nan_mask, :]
        return df

    def __group_model_results(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Grouping model results

        by: str = ["year", "month", "day", "company"]
        """
        # group the data by year and month
        grouped = df.groupby(["year", "month", "day", "company"])

        # count the number of positive and negative tweets for each year and month
        sentiment_positive_tweets_by_day = grouped["sentiment"].apply(
            lambda x: (x == 1).sum()
        )
        sentiment_negative_tweets_by_day = grouped["sentiment"].apply(
            lambda x: (x == -1).sum()
        )
        sentiment_base_positive_tweets_by_day = grouped["sentiment_base"].apply(
            lambda x: (x == 1).sum()
        )
        sentiment_base_neutral_tweets_by_day = grouped["sentiment_base"].apply(
            lambda x: (x == 0).sum()
        )
        sentiment_base_negative_tweets_by_day = grouped["sentiment_base"].apply(
            lambda x: (x == -1).sum()
        )

        # calculate the ratio of positive and negative tweets for each year and month
        positive_ratios_by_day = (
            sentiment_base_positive_tweets_by_day + sentiment_positive_tweets_by_day
        ) / (
            sentiment_positive_tweets_by_day
            + sentiment_negative_tweets_by_day
            + sentiment_base_positive_tweets_by_day
            + sentiment_base_neutral_tweets_by_day
            + sentiment_base_negative_tweets_by_day
        )

        # formatting
        positive_ratios_by_day = positive_ratios_by_day.reset_index()
        positive_ratios_by_day.rename(columns={0: "positive_ratio"}, inplace=True)
        positive_ratios_by_day["yearmonthday"] = (
            positive_ratios_by_day["year"].astype(str)
            + "-"
            + positive_ratios_by_day["month"].astype(str).str.zfill(2)
            + "-"
            + positive_ratios_by_day["day"].astype(str).str.zfill(2)
        )

        return positive_ratios_by_day

    def __adjust_returns_with_company_names(self, df: pd.DataFrame):
        """
        Rename returns to webscrapped names
        """

        selected_columns = [
            value for value in company_to_stock_dict.values() if value in df.columns
        ]
        selected_returns = df.loc[:, selected_columns]

        selected_returns.rename(
            columns={v: k for k, v in company_to_stock_dict.items()}, inplace=True
        )
        selected_returns = selected_returns.reset_index().rename(
            columns={"index": "date"}
        )

        return selected_returns

    def process(self, analysed_tweets: pd.DataFrame, returns: pd.DataFrame):
        analysed_tweets = self.__process_analysed_tweets(analysed_tweets)
        grouped_analysed_tweets = self.__group_model_results(analysed_tweets)

        returns = self.__process_returns(returns)
        returns = self.__adjust_returns_with_company_names(returns)

        return grouped_analysed_tweets, returns


class StatisticalTests:
    def __init__(self, save_path) -> None:
        self.save_path = save_path

    def dickey_fuller_test(self, series: pd.Series):
        # Perform Dickey-Fuller test
        result = adfuller(series)

        # Output the results
        print("ADF Statistic:", result[0])
        print("p-value:", result[1])
        print("Critical Values:")
        for key, value in result[4].items():
            print(f"\t{key}: {value}")

        # Interpretation
        if result[1] < 0.05:
            print(
                "Reject the null hypothesis (H0), the data does not have a unit root and is stationary."
            )
        else:
            print(
                "Fail to reject the null hypothesis (H0), the data has a unit root and is non-stationary."
            )

    def kpss_test(self, series: pd.Series):
        statistic, p_value, n_lags, critical_values = kpss(
            series, regression="c", nlags="auto"
        )
        print(f"KPSS Statistic: {statistic}")
        print(f"p-value: {p_value}")
        print("Critical Values:")
        for key, value in critical_values.items():
            print(f"\t{key}: {value}")

        # Interpreting the p-value
        if p_value < 0.05:
            print("The series is likely non-stationary.")
        else:
            print("The series is likely stationary.")

    def acf_pacf_test(self, series: pd.Series, filename: str = None):
        plt.figure(figsize=(12, 6))

        plt.subplot(121)
        plot_acf(series, ax=plt.gca(), lags=40)
        plt.title("Autocorrelation Function")

        plt.subplot(122)
        plot_pacf(series, ax=plt.gca(), lags=40)
        plt.title("Partial Autocorrelation Function")

        plt.tight_layout()
        if filename:
            plt.savefig(f"{self.save_path}acf_pacf_plot_{filename}.png")

    def plot_ccf(
        self,
        x,
        y,
        lag_range,
        filename: str = "ccf_plot.png",
        figsize=(12, 5),
        title_fontsize=15,
        xlabel_fontsize=16,
        ylabel_fontsize=16,
    ):
        """
        Plot cross-correlation between series x and y.
        """

        title = "{} & {}".format(x.name, y.name)
        lags = np.arange(
            -lag_range, lag_range + 1
        )  # This should include zero, hence +1
        ccf_yx = sm.tsa.stattools.ccf(y, x, adjusted=False)[
            : lag_range + 1
        ]  # Include up to the lag_range
        ccf_xy = sm.tsa.stattools.ccf(x, y, adjusted=False)[
            : lag_range + 1
        ]  # Same here

        ccf_yx = ccf_yx[1:][
            ::-1
        ]  # Reverse and ignore the zero-lag, this should now be of length lag_range
        cc = np.concatenate(
            [ccf_yx, ccf_xy]
        )  # Ensure this concatenation results in 2*lag_range + 1 elements

        sigma = 1 / np.sqrt(len(x))  # Standard error for confidence intervals
        fig, ax = plt.subplots(figsize=figsize)
        ax.vlines(lags, 0, cc, label="CCF")  # Ensure lags and cc are of same length
        ax.axhline(0, color="black", linewidth=1.0)
        ax.axhline(2 * sigma, color="red", linestyle="-.", linewidth=0.6)
        ax.axhline(-2 * sigma, color="red", linestyle="-.", linewidth=0.6)
        ax.set_xlabel("Lag", fontsize=xlabel_fontsize)
        ax.set_ylabel("Cross-Correlation", fontsize=ylabel_fontsize)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        fig.suptitle(title, fontsize=title_fontsize, fontweight="bold", y=0.95)

        if filename:
            plt.savefig(f"{self.save_path}ccf_plot_{filename}.png")
        plt.close(fig)

    def compute_statistical_tests(
        self, x: pd.Series, y: pd.Series = None, filename: str = None
    ):
        self.dickey_fuller_test(x)
        self.kpss_test(x)
        self.acf_pacf_test(x)

        if y:
            self.dickey_fuller_test(y)
            self.kpss_test(y)
            self.acf_pacf_test(y)

            user_input = input("are the tests ok? yes or no")
            if user_input == "yes":
                self.plot_ccf(x, y, lag_range=30, filename=filename)


class DailyModelEvaluation(StatisticalTests):
    def __init__(
        self,
        analysed_tweets: pd.DataFrame,
        returns: pd.DataFrame,
        save_path: os.PathLike,
        verbose: bool = False,
    ) -> None:
        super().__init__(save_path)
        self.grouped_analysed_tweets = analysed_tweets.copy()
        self.adjusted_returns = returns.copy()

        self.verbose = verbose
        self.strong_pos_threshold = 0.5
        self.strong_neg_threshold = -0.5
        self.neutral_threshold = 0.5
        self.shortlongdf = None  # Initialize shortlongdf attribute

    def update_thresholds(
        self, strong_pos_threshold, strong_neg_threshold, neutral_threshold
    ):
        self.strong_pos_threshold = strong_pos_threshold
        self.strong_neg_threshold = strong_neg_threshold
        self.neutral_threshold = neutral_threshold

    def prediction_matches(self, signal, market_return):
        if (
            signal > self.strong_pos_threshold and market_return > 0
        ):  # strong positive signal
            return True
        elif (
            signal < self.strong_neg_threshold and market_return < 0
        ):  # strong negative signal
            return True
        elif (
            -self.neutral_threshold <= signal <= self.neutral_threshold
            and -0.05 <= market_return <= 0.05
        ):  # neutral signal
            return True
        else:
            return False

    def short_or_long(self):
        """new dataframe with buy or sell at t"""

        positive_ratios_by_day = self.grouped_analysed_tweets.copy()

        date_index = positive_ratios_by_day["yearmonthday"].unique().tolist()
        companies = positive_ratios_by_day["company"].unique().tolist()

        self.shortlongdf = pd.DataFrame(index=date_index)

        for company in companies:
            # selection of the company
            mask = positive_ratios_by_day["company"] == company
            stock_ratios = positive_ratios_by_day.loc[mask, :]

            # lag the sentiments 1 day
            stock_ratios.loc[:, "positive_ratio_shifted"] = stock_ratios[
                "positive_ratio"
            ].shift(1)

            # faire log ou la difference premiere, test de racines unitaire
            # pour voir si les moments sont invariants avec le temps

            stock_ratios.loc[:, "buy_or_sell"] = (
                stock_ratios["positive_ratio_shifted"] - 0.5
            ) * 2

            # STOCK_RATIONS BETWEEN -1 and 1
            stock_ratios.set_index("yearmonthday", inplace=True)

            self.stock_ratios = stock_ratios
            # saving info in a dataframe
            self.shortlongdf[company] = stock_ratios["buy_or_sell"]

    def evaluate_model_accuracy(self):
        self.adjusted_returns.index = pd.to_datetime(self.adjusted_returns["date"])
        self.shortlongdf.index = pd.to_datetime(self.shortlongdf.index)

        evaluation_df = self.shortlongdf.join(
            self.adjusted_returns, how="inner", lsuffix="_buysell", rsuffix="_market"
        )

        accuracy_metrics = {}

        def prediction_matches(signal, market_return):
            if signal > 0.5 and market_return > 0:  # strong positive signal
                return True
            elif signal < -0.5 and market_return < 0:  # strong negative signal
                return True
            elif (
                -0.5 <= signal <= 0.5 and -0.05 <= market_return <= 0.05
            ):  # neutral signal
                return True
            else:
                return False

        for _, row in evaluation_df.iterrows():
            for column in evaluation_df.columns:
                if "_buysell" in column:
                    company_name = column.split("_buysell")[0]
                    market_column = company_name + "_market"

                    if market_column in evaluation_df.columns:
                        if company_name not in accuracy_metrics:
                            accuracy_metrics[company_name] = {
                                "correct_predictions": 0,
                                "total_signals": 0,
                            }

                        accuracy_metrics[company_name]["total_signals"] += 1

                        if prediction_matches(row[column], row[market_column]):
                            accuracy_metrics[company_name]["correct_predictions"] += 1

        return pd.DataFrame.from_dict(
            {
                stock: {
                    "Accuracy (%)": (
                        (metrics["correct_predictions"] / metrics["total_signals"])
                        * 100
                        if metrics["total_signals"] > 0
                        else 0
                    )
                }
                for stock, metrics in accuracy_metrics.items()
            },
            orient="index",
        )

    def evaluate_model_accuracy_with_thresholds(self, thresholds):
        self.short_or_long()  # Ensure shortlongdf is created
        self.adjusted_returns.index = pd.to_datetime(self.adjusted_returns["date"])
        self.shortlongdf.index = pd.to_datetime(self.shortlongdf.index)

        evaluation_df = self.shortlongdf.join(
            self.adjusted_returns, how="inner", lsuffix="_buysell", rsuffix="_market"
        )
        print(evaluation_df)
        results = []
        for strong_pos_threshold, strong_neg_threshold, neutral_threshold in thresholds:
            accuracy_metrics = {}

            def prediction_matches(signal, market_return):
                if (
                    signal > strong_pos_threshold and market_return > 0
                ):  # strong positive signal
                    return True
                elif (
                    signal < strong_neg_threshold and market_return < 0
                ):  # strong negative signal
                    return True
                elif (
                    -neutral_threshold <= signal <= neutral_threshold
                    and -0.05 <= market_return <= 0.05
                ):  # neutral signal
                    return True
                else:
                    return False

            for _, row in evaluation_df.iterrows():
                for column in evaluation_df.columns:
                    if "_buysell" in column:
                        company_name = column.split("_buysell")[0]
                        market_column = company_name + "_market"

                        if market_column in evaluation_df.columns:
                            if company_name not in accuracy_metrics:
                                accuracy_metrics[company_name] = {
                                    "correct_predictions": 0,
                                    "total_signals": 0,
                                }

                            accuracy_metrics[company_name]["total_signals"] += 1

                            if prediction_matches(row[column], row[market_column]):
                                accuracy_metrics[company_name][
                                    "correct_predictions"
                                ] += 1

            accuracy_df = pd.DataFrame.from_dict(
                {
                    stock: {
                        "Accuracy (%)": (
                            (metrics["correct_predictions"] / metrics["total_signals"])
                            * 100
                            if metrics["total_signals"] > 0
                            else 0
                        )
                    }
                    for stock, metrics in accuracy_metrics.items()
                },
                orient="index",
            )

            mean_accuracy = accuracy_df["Accuracy (%)"].mean()
            results.append(
                {
                    "strong_pos_threshold": strong_pos_threshold,
                    "strong_neg_threshold": strong_neg_threshold,
                    "neutral_threshold": neutral_threshold,
                    "mean_accuracy": mean_accuracy,
                }
            )

        return pd.DataFrame(results)

    def compute_signal_market_correlation(self):
        """
        Compute correlation between lagged NLP scores (buy/sell signals)
        and market returns based on a 0.5 threshold for each date.
        """
        self.update_thresholds(0.5, -0.5, 0.5)  # Set thresholds to 0.5
        self.short_or_long()  # Ensure shortlongdf is created
        self.adjusted_returns.index = pd.to_datetime(self.adjusted_returns["date"])
        self.shortlongdf.index = pd.to_datetime(self.shortlongdf.index)

        evaluation_df = self.shortlongdf.join(
            self.adjusted_returns, how="inner", lsuffix="_buysell", rsuffix="_market"
        )

        correlation_results = {}

        for column in evaluation_df.columns:
            if "_buysell" in column:
                company_name = column.split("_buysell")[0]
                market_column = company_name + "_market"

                if market_column in evaluation_df.columns:
                    signal_data = evaluation_df[column].dropna()
                    market_data = evaluation_df[market_column].dropna()

                    # Align both series to the same dates
                    combined_data = pd.concat(
                        [signal_data, market_data], axis=1
                    ).dropna()
                    signal_data = combined_data.iloc[:, 0]
                    market_data = combined_data.iloc[:, 1]

                    # Apply threshold logic to signal_data
                    signal_data = signal_data.apply(
                        lambda x: 1 if x > 0.5 else (-1 if x < -0.5 else 0)
                    )
                    if (
                        len(signal_data) > 1 and len(market_data) > 1
                    ):  # Ensure there's enough data
                        # Compute Pearson correlation
                        pearson_corr, p_value = pearsonr(signal_data, market_data)

                        correlation_results[company_name] = {
                            "Pearson Correlation": pearson_corr,
                            "P-value": p_value,
                        }

                        # Optional: Plot Cross-Correlation Function (CCF)
                        self.plot_ccf(
                            signal_data,
                            market_data,
                            lag_range=30,
                            filename=company_name,
                        )

        return pd.DataFrame.from_dict(correlation_results, orient="index")

    def save_results_to_excel(self, save_path):
        with pd.ExcelWriter(f"{save_path}daily_model_results.xlsx") as writer:
            self.evaluate_model_accuracy().to_excel(writer, sheet_name="Model Accuracy")
            self.compute_signal_market_correlation().to_excel(
                writer, sheet_name="Signal Market Correlation"
            )

        print("Results saved to daily_model_results.xlsx.")

    def visualize_courbe(self, save_path):

        os.makedirs(f"{save_path}correlation_curves/", exist_ok=True)

        evaluation_df = self.shortlongdf.join(
            self.adjusted_returns, how="inner", lsuffix="_buysell", rsuffix="_market"
        )

        def moving_average(data, window_size):
            return data.rolling(window=window_size, min_periods=1).mean()

        unique_stocks = set(
            col.split("_buysell")[0]
            for col in evaluation_df.columns
            if "_buysell" in col
        )

        for stock in unique_stocks:
            buysell_col = stock + "_buysell"
            market_col = stock + "_market"

            if (
                buysell_col in evaluation_df.columns
                and market_col in evaluation_df.columns
            ):
                fig, ax1 = plt.subplots(figsize=(14, 7))

                color = "tab:blue"
                ax1.set_xlabel("Date")
                ax1.set_ylabel("Signal", color=color)
                smoothed_signal = moving_average(
                    evaluation_df[buysell_col], window_size=5
                )
                ax1.plot(
                    evaluation_df.index,
                    smoothed_signal,
                    label="Smoothed Signal",
                    color=color,
                    alpha=0.7,
                )
                ax1.tick_params(axis="y", labelcolor=color)

                ax2 = ax1.twinx()
                color = "tab:red"
                ax2.set_ylabel("Market Return", color=color)
                smoothed_market_return = moving_average(
                    evaluation_df[market_col], window_size=5
                )
                ax2.plot(
                    evaluation_df.index,
                    smoothed_market_return,
                    label="Smoothed Market Return",
                    color=color,
                    alpha=0.7,
                )
                ax2.tick_params(axis="y", labelcolor=color)

                fig.tight_layout()
                plt.title(f"Smoothed Signal vs Market Return for {stock}")
                plt.savefig(
                    f"{save_path}/correlation_curves/{stock}_smoothed_signal_vs_market_return.png"
                )
                plt.close()

    def launch(self):

        self.short_or_long()
        self.evaluate_model_accuracy()
        self.compute_signal_market_correlation()
        self.save_results_to_excel(save_path=self.save_path)
        self.visualize_courbe(save_path=self.save_path)


def sensitivity_analysis(thresholds, grouped_analysed_tweets, df_returns, save_path):
    model_evaluator = DailyModelEvaluation(
        grouped_analysed_tweets, df_returns, save_path=save_path, verbose=False
    )

    results = model_evaluator.evaluate_model_accuracy_with_thresholds(thresholds)
    return results


def plot_sensitivity_analysis(results, save_path):
    plt.figure(figsize=(10, 6))
    plt.plot(
        results["strong_pos_threshold"],
        results["mean_accuracy"],
        marker="o",
        linestyle="-",
    )
    plt.xlabel("Strong Positive Threshold")
    plt.ylabel("Mean Accuracy (%)")
    plt.title("Sensitivity Analysis of Thresholds")
    plt.grid(True)
    plt.savefig(os.path.join(save_path, "sensitivity_analysis_plot.png"))
    plt.close()


if __name__ == "__main__":
    WEBSCRAPPED_DATA_PATH = (
        "./../../data/webscrapped/predicted/twitter/concatenated_prediction.csv"
    )
    DAILY_STOCKS_RETURNS_PATH = "./../../data/stocks_daily_data.xlsx"
    analysed_tweets = pd.read_csv(WEBSCRAPPED_DATA_PATH)
    df_returns = pd.read_excel(DAILY_STOCKS_RETURNS_PATH, index_col=0)

    preprocessor = Preprocessing()
    grouped_analysed_tweets, df_returns = preprocessor.process(
        analysed_tweets, df_returns
    )

    # Define a range of threshold values for analysis
    thresholds = [
        (0.1, -0.1, 0.1),
        (0.15, -0.15, 0.15),
        (0.2, -0.2, 0.2),
        (0.25, -0.25, 0.25),
        (0.3, -0.3, 0.3),
        (0.35, -0.35, 0.35),
        (0.4, -0.4, 0.4),
        (0.45, -0.45, 0.45),
        (0.5, -0.5, 0.5),
        (0.55, -0.55, 0.55),
        (0.6, -0.6, 0.6),
        (0.65, -0.65, 0.65),
        (0.7, -0.7, 0.7),
        (0.75, -0.75, 0.75),
        (0.8, -0.8, 0.8),
        (0.85, -0.85, 0.85),
        (0.9, -0.9, 0.9),
        (0.95, -0.95, 0.95),
        (1.0, -1.0, 1.0),
    ]

    # Run sensitivity analysis
    results = sensitivity_analysis(
        thresholds,
        grouped_analysed_tweets,
        df_returns,
        save_path="./../../data/results/daily_model/",
    )
    # Save plot
    plot_sensitivity_analysis(results, save_path="./../../data/results/daily_model/")
    # Optionally, continue with the normal evaluation process using default thresholds
    model_evaluator = DailyModelEvaluation(
        grouped_analysed_tweets,
        df_returns,
        save_path="./../../data/results/daily_model/",
        verbose=True,
    )
    model_evaluator.launch()
