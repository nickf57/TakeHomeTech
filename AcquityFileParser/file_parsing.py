import os
import pandas as pd
from typing import List
from dataclasses import dataclass, field
from AcquityFileParser.chromatogram_processing import ChromatogramProcessor
from AcquityFileParser.util import (
    InjectionMetadata,
    ChromatogramMetadata,
    SignalParameterMetadata,
    injection_metadata_map,
    chromatogram_metadata_map,
    signal_metadata_map,
    cast_to_float,
)


@dataclass
class FileParser:
    """
    Class to parse Waters Acquity files for raw chromatogram data and associated instrument metadata.

    ```
    Attributes
    ----------
    path: str
        path use to find file
    filename: str
        parsed filename from provided path
    injection_metadata:
        object to store injection associated metadata
    chromatogram_metadata:
        object to store chromatogram associated metadata
    signal_parameter_metadata:
        object to store signal associated metadata
    chromatography_data_toggle: bool
        toggle to mark when parser reaches raw chromatogram data
    raw_chromatography_data: list
        stores raw chromatogram data as list of lists
    processed_chromatogram: ChromatogramProcessing
        stores processed chromatogram and identified peaks
    chromatography_data_df: pd.DataFrame
        chromatogram data organized as pandas dataframe
    ```

    """

    path: str
    filename: str = None
    injection_metadata: InjectionMetadata = InjectionMetadata()
    chromatogram_metadata: ChromatogramMetadata = ChromatogramMetadata()
    signal_parameter_metadata: SignalParameterMetadata = SignalParameterMetadata()
    chromatography_data_toggle: bool = False
    raw_chromatography_data: List = field(default_factory=list)
    processed_chromatogram: ChromatogramProcessor = None
    chromatography_data_df: pd.DataFrame = None

    def __post_init__(self):

        valid_file_extensions = ["txt"]

        if self.path.split(".")[-1] not in valid_file_extensions:
            raise Exception(
                f"File extension must be one of the following: {valid_file_extensions}"
            )

        self.filename = os.path.basename(self.path)

    def parse_file(self):
        """Parses provided file line by line. Metadata is identified via predefined key mappings stored in util.py.
         Prior to storage, metadata values are cast to appropriate types. Chromatogram
        data is stored as a list of lists for eventual conversion to a dataframe."""

        with open(self.path, "r", encoding="utf-8") as file:
            for line in file:

                if self.chromatography_data_toggle:
                    # We need to split the header line slightly differently from the raw value lines
                    if self.raw_chromatography_data:
                        self.raw_chromatography_data.append(line.split())
                    else:
                        self.raw_chromatography_data.append(line.strip().split("\t"))

                else:

                    stripped_line = line.strip("\n")
                    key_value_pair = stripped_line.split("\t")

                    if len(key_value_pair) == 2:
                        # metadata_map values are tuples containing attribute names and type casting functions
                        if injection_metadata_map.get(key_value_pair[0]):
                            setattr(
                                self.injection_metadata,
                                injection_metadata_map[key_value_pair[0]][0],
                                injection_metadata_map[key_value_pair[0]][1](
                                    key_value_pair[1]
                                ),
                            )
                        elif chromatogram_metadata_map.get(key_value_pair[0]):
                            setattr(
                                self.chromatogram_metadata,
                                chromatogram_metadata_map[key_value_pair[0]][0],
                                chromatogram_metadata_map[key_value_pair[0]][1](
                                    key_value_pair[1]
                                ),
                            )
                        elif signal_metadata_map.get(key_value_pair[0]):
                            setattr(
                                self.signal_parameter_metadata,
                                signal_metadata_map[key_value_pair[0]][0],
                                signal_metadata_map[key_value_pair[0]][1](
                                    key_value_pair[1]
                                ),
                            )

                if line.strip().startswith("Chromatogram Data:"):
                    # Toggle to let us know we switched from parsing metadata to raw chromatogram data
                    self.chromatography_data_toggle = True

        return self

    def make_chromatography_data_df(self):
        """Generates dataframe to store raw chromatogram data. Dataframe headers are determined by parsed file."""

        if not self.raw_chromatography_data:
            raise Exception(
                f"No chromatography data extracted from file. Cannot process chromatogram."
            )

        self.chromatography_data_df = pd.DataFrame(
            columns=self.raw_chromatography_data[:1][0],
            data=self.raw_chromatography_data[1:],
        )
        for column in self.chromatography_data_df:
            self.chromatography_data_df[column] = self.chromatography_data_df[
                column
            ].apply(cast_to_float)

        return self

    def process_chromatogram(self):
        """Creates ChromatogramProcessing object and triggers chromatogram preprocessing and peak integration."""

        self.processed_chromatogram = ChromatogramProcessor(
            data=self.chromatography_data_df,
            x_accessor="Time (min)",
            y_accessor="Value (EU)",
        )

        self.processed_chromatogram.preprocess_chromatogram()
        self.processed_chromatogram.integrate_peaks()

        return self
