import pandas as pd
import numpy as np
from typing import Dict
from dataclasses import dataclass, field
from scipy.signal import find_peaks, savgol_filter
from scipy import integrate

from AcquityFileParser.util import cast_to_int


@dataclass
class ChromatographicPeak:
    """
    Class to identify peak borders and estimate associated areas from data stored in a pandas dataframe.

    ```
    Attributes
    ----------
    data: pd.DataFrame
        raw chromatogram data
    peak_center: int
        Index of peak center relative to self.data
    peak_height: float
        Height of peak as stored in y_accessor column
    x_accessor: str
        Accessor for x axis variable. Traditionally time or scan number
    y_accessor: str
        Accessor for y axis variable. Traditionally the measured response of an instrument.
    peak_properties: Dict
        Dictionary storing output measures from scipy.signal.find_peaks
    border_detection_method: str
        Specifies method to be used for peak border detection
    peak_integration_method: str
        Determines percentage of data to remove from start of chromatogram if remove_solvent front is True
    peak_borders: list
        List containing index for the left and right peak boundaries
    peak_area: float
        Estimated peak area based on specifies integration method
    ```

    """

    data: pd.DataFrame
    peak_center: int
    peak_height: float
    x_accessor: str
    y_accessor: str
    peak_properties: Dict = field(default_factory=dict)
    border_detection_method = "gradient"
    peak_integration_method = "cumulative_trapezoid"
    peak_borders: [int, int] = None
    peak_area: float = None

    def __post_init__(self):

        valid_peak_integration_methods = ["cumulative_simpson", "cumulative_trapezoid"]
        valid_border_detection_methods = ["gradient", "FWHM", "prominence"]
        if self.peak_integration_method not in valid_peak_integration_methods:
            raise Exception(
                f"Peak integration method {self.peak_integration_method} is not valid. Valid options are: {valid_peak_integration_methods}"
            )

        if self.border_detection_method not in valid_border_detection_methods:
            raise Exception(
                f"Border detection method {self.border_detection_method} is not valid. Valid options are: {valid_border_detection_methods}"
            )

    @staticmethod
    def find_peak_borders_by_gradient(
        data: pd.Series, peak_center: int, gradient_padding: int
    ) -> [int, int]:
        """Method to find peak boundaries by detecting where slope becomes zero. Gradient padding modifies
        the starting point for peak descent to avoid problems with poorly smoothed data.
        """

        gradient = np.gradient(data)
        left_border = peak_center
        right_border = peak_center

        for i in range(peak_center - gradient_padding, 0, -1):
            if gradient[i] <= 0:
                left_border = i
                break

        for j in range(peak_center + gradient_padding, len(data)):
            if gradient[j] >= 0:
                right_border = j
                break

        return left_border, right_border

    def _define_borders(self):

        if self.border_detection_method == "gradient":
            self.peak_borders = list(
                ChromatographicPeak.find_peak_borders_by_gradient(
                    self.data[self.y_accessor], self.peak_center, 10
                )
            )

        elif self.border_detection_method == "FWHM":

            self.peak_borders = [
                cast_to_int(self.peak_properties.get("left_ips")),
                cast_to_int(self.peak_properties.get("right_ips")),
            ]

        elif self.border_detection_method == "prominence":
            self.peak_borders = [
                cast_to_int(self.peak_properties.get("left_bases")),
                cast_to_int(self.peak_properties.get("right_bases")),
            ]

        return self

    def _integrate_peak(self):

        if not self.peak_borders:
            raise Exception(
                f"Peak borders provided: {self.peak_borders} are invalid. Please ensure border detection is successful prior to integration."
            )

        if None in self.peak_borders:
            raise Exception(
                f"Peak borders provided: {self.peak_borders} are invalid. Please ensure border detection is successful prior to integration."
            )

        sliced_data = self.data.copy().iloc[
            int(self.peak_borders[0]) : int(self.peak_borders[1])
        ]

        if self.peak_integration_method == "cumulative_simpson":
            estimated_area = integrate.cumulative_simpson(
                y=sliced_data[self.y_accessor], x=sliced_data[self.x_accessor]
            )[-1]

            self.peak_area = estimated_area

        elif self.peak_integration_method == "cumulative_trapezoid":
            estimated_area = integrate.cumulative_trapezoid(
                y=sliced_data[self.y_accessor], x=sliced_data[self.x_accessor]
            )[-1]

            self.peak_area = estimated_area

        return self


@dataclass
class ChromatogramProcessor:
    """
    Class to process chromatogram data stored as a pandas dataframe.

    ```
    Attributes
    ----------
    data: pd.DataFrame
        raw chromatogram data
    x_accessor: str
        Accessor for x axis variable. Traditionally time or scan number
    y_accessor: str
        Accessor for y axis variable. Traditionally the measured response of an instrument.
    remove_solvent_front: bool
        Toggle to truncate initial data from chromatogram
    remove_late_elution: bool
        Toggle to truncate end data from chromatogram
    solvent_front_factor: float
        Determines percentage of data to remove from start of chromatogram if remove_solvent front is True
    late_elution_factor: float
        Determines percentage of data to remove from end of chromatogram if remove_late_elution is True
    min_peak_distance: int
        Minimum distance between peaks used when determining peak centers
    min_peak_width: int
        Minimum peak width when deteriming peaks in chromatogram
    peak_prominence: float
        Minimum peak prominence for a peak to be identified. Prominences will need to scale with chromatogram data
    smoothing_filter: str
        Type of smoothing filter to use on chromatogram y data
    baseline_correction: bool
        Toggle to apply polynomial baseline correction to chromatogram data
    baseline_poly_order: int
        Polynomial function degree used to model baseline
    identified_peaks: [ChromatographicPeak]
        List of ChromatographicPeak instances associated with identified peak centers
    ```

    """

    data: pd.DataFrame
    x_accessor: str
    y_accessor: str
    remove_solvent_front: bool = True
    remove_late_elution: bool = True
    solvent_front_factor: float = 0.1
    late_elution_factor: float = 0.15
    min_peak_distance: int = 15
    min_peak_width: int = 10
    peak_prominence: float = 0.3
    smoothing_filter: str = "savgol"
    baseline_correction: bool = True
    baseline_poly_order: int = 3
    identified_peaks: [ChromatographicPeak] = field(default_factory=list)

    def __post_init__(self):

        valid_filters = ["savgol"]

        if self.smoothing_filter not in valid_filters:
            raise Exception(
                f"Invalid filter {self.smoothing_filter} found. Valid filters are: {valid_filters}"
            )

    def preprocess_chromatogram(self):

        self._truncate_chromatogram()
        self._smooth_chromatogram()
        self._detect_peak_centers()

        if self.baseline_correction:
            self._estimate_baseline()
            self._shift_chromatogram()

        return self

    def _truncate_chromatogram(self):
        """Truncates chromatogram at one or both ends. Truncation is proportional to total number of collected data points."""
        if self.remove_solvent_front:
            time_boundary = (
                np.max(self.data[self.x_accessor]) * self.solvent_front_factor
            )

            self.data = self.data.loc[self.data[self.x_accessor] > time_boundary]

        if self.remove_late_elution:
            time_boundary = (
                np.max(self.data[self.x_accessor])
                - np.max(self.data[self.x_accessor]) * self.late_elution_factor
            )
            self.data = self.data.loc[self.data[self.x_accessor] < time_boundary]

        self.data.reset_index(inplace=True)

        return self

    def _smooth_chromatogram(self):

        if self.smoothing_filter == "savgol":
            self.data["Smoothed " + self.y_accessor] = savgol_filter(
                self.data[self.y_accessor],
                window_length=self.min_peak_width,
                polyorder=self.baseline_poly_order,
            )
            self.y_accessor = "Smoothed " + self.y_accessor

        return self

    def _detect_peak_centers(self):
        """Detected peak centers by using scipy.signal.find_peaks. Assumes usage with distance, width, and prominence variables. Stores
        identified peaks as ChromatographPeak instances."""

        peak_centers, peak_properties = find_peaks(
            self.data[self.y_accessor],
            distance=self.min_peak_distance,
            width=self.min_peak_width,
            prominence=self.peak_prominence,
        )

        for i in range(len(peak_centers)):
            individual_peak_properties = {
                key: peak_properties[key][i] for key in peak_properties.keys()
            }

            peak_object = ChromatographicPeak(
                data=self.data.copy(),
                peak_center=peak_centers[i],
                peak_height=self.data[self.y_accessor].iloc[peak_centers[i]],
                x_accessor=self.x_accessor,
                y_accessor=self.y_accessor,
                peak_properties=individual_peak_properties,
            )

            self.identified_peaks.append(peak_object)

        return self

    def _estimate_baseline(self):
        """Fits polynomial to baseline and uses the resulting fit to adjust chromatogram data. Identified peaks are removed
        from baseline estimation prior to fitting."""
        baseline_df = self.data.copy()

        for peak in self.identified_peaks:
            baseline_df = baseline_df[
                ~baseline_df.index.isin(
                    range(
                        peak.peak_center - int(self.min_peak_width),
                        peak.peak_center + int(self.min_peak_width),
                    )
                )
            ]

        fit_params = np.polyfit(
            baseline_df[self.x_accessor],
            baseline_df[self.y_accessor],
            self.baseline_poly_order,
        )
        poly_function = np.poly1d(fit_params)

        estimated_baseline = poly_function(self.data[self.x_accessor])

        self.data["Baseline Corrected Value"] = (
            self.data[self.y_accessor] - estimated_baseline
        )

        self.y_accessor = "Baseline Corrected Value"

    def _shift_chromatogram(self):
        """Adjusts chromatogram such that all values are positive."""

        self.data[self.y_accessor] = self.data[self.y_accessor] - min(
            self.data[self.y_accessor]
        )

        for peak in self.identified_peaks:
            peak.data = self.data.copy()
            peak.y_accessor = self.y_accessor
            peak.peak_height = self.data[self.y_accessor].iloc[peak.peak_center]

        return self

    def integrate_peaks(self):

        for peak in self.identified_peaks:
            peak._define_borders()
            peak._integrate_peak()

        return self
