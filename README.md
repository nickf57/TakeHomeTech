# Water Acquity LC Parser
Waters Acquity LC Parser is a tool to parse Acquity LC output files that are formatted as text. The parser records all parsable metadata and provides the following functionalities:
+	Metadata captured via predefined string mappings
+	Chromatogram truncation at the start and/or end to eliminate solvent fronts and target that elute during the wash phase
+	Chromatogram smoothing prior to peak integration and baseline estimation
+	Polynomial baseline correction and fixed
+	Peak thresholds can be determined via gradient-based method, FWHM, or prominences
+	Peak integration is provided via simpson and trapezoid estimations

## Function Methodology and Limitations

### Metadata capture

Metadata is parsed and captured if a valid field stored in any of the predefined metadata mappings stored in `util.py`. While this requires metadata mappings to be updated as Acquity data formats change, explicitly defining the mapping enables easy tracking via git histories. An evolution of this implementation would be to store values via config files or a centralized database. These types of metadata capture processes necessitate accurate version control.

### Truncating Chromatograms

Chromatographic methods employing gradients exhibit two features: 
1.	A significant initial bolus of material corresponding to solvent and molecules that do not bind to a stationary phase
2.	A second bolus at the end of the method as tightly bound molecules are washed away

To avoid problems associated with baseline estimation and peak finding introduced by these chromatogram artifacts, I provide an option to truncate both ends of a given chromatogram. Truncation is performed based on a proportion of the total data points in a provided chromatogram--this value may need to be tweaked for dramatically different types of LC assays.

### Chromatogram Smoothing

Traditional LC processing includes a smoothing step to make subsequent analysis (peak detection/integration) more manageable. One of the most popular LC smoothing filters is the savitsky-golay filter, implemented here, because of its performance in preserving peak shapes. While the window can be tuned for specific needs, it may be wise to implement alternative smoothing methods as well (Gaussian, custom moving average). One must always be conscientious to not oversmooth data and lose peak definition.

### Peak detection

Peak detection is performed using scipy.signals.find_peaks with basic assumptions provided for peak distances and widths. Better performance in peak calling can likely be obtained by further optimization of finding parameters and/or implementation of a custom peak detection method. Additionally peak normalization can go far in ensuring peak finding parameters are useful across disparate assay types. In my opinion, finding peak centers is generally an easier task than finding boundaries which requires more nuance. As such, improvements here would likely be low priority.

### Baseline Estimation

Chromatogram baselines are estimated via a 3rd degree polynomial performed on isolated background data. Isolated background is obtained by excising a fixed number of data points around each peak center. This method of background isolation is servicable, but leaves room for more refined isolation based on accurate peak borders. Relatedly, the estimated baseline can be improved by utilizing splines rather than relying on a single function over the entirety of the chromatogram. 

### Peak Integration

Peak integration is performed via numerical methods (simpson or trapezoidal integration). Provided enough data points are available, numerical methods provide a very close approximation to the definitive solution. An alternative method commonly used is to fit a Gaussian function to each peak and calculate areas via the definite integral. One benefit to using numerical methods is generally better performance in integration of asymmetrical peaks, though performance can deteriorate with low data point frequency across a peak. 

### Basic Tests

In a production environment proper unit tests need to be written and maintained to ensure consistent performance.

## How to use

After downloading the repo install the package locally for use in your python environment. Additionally save example Acquity files to a directory of your choice (example files can be found [here](https://github.com/Tarskin/HappyTools/tree/master/Example%20Data))

1. import the `FileParser` class and create an instance providing a path to the desired file
2. Call the methods make_chromatography_data_df() and process_chromatogram() to parse metadata and perform peak detection/integration.

Metadata can be inspected by accessing each metadata atribute of the FileParser instance as follows.

```
from AcquityFileParser import FileParser

parser_instance = FileParser(r'C:\Document\data_file.txt') #replace filepath with the path to your file
parser_instance.parse_file().make_chromatography_data_df().process_chromatogram()

print(parser_instance.injection_metadata)
print(parser_instance.chromatogram_metadata)

```

Individual peak data is make available via ChromatographicPeak objects stored in the FileParser object.

```
from AcquityFileParser import FileParser

parser_instance = FileParser(r'C:\Document\data_file.txt') #replace filepath with the path to your file
parser_instance.parse_file().make_chromatography_data_df().process_chromatogram()

#print out peak data
for peak in parser_instance.processed_chromatogram.identified_peaks:
    print('peak borders are:', peak.peak_borders)
    print('peak area is:', peak.peak_area)
    print('peak height is:', peak.peak_height)

```

To change parameters during chromatogram processing, one must manually create a ChromatogramProcessing object rather than rely on `process_chromatograms`

Example with parameter customization:
```
from AcquityFileParser import FileParser
from AcquityFileParser import ChromatogramProcessor

updated_instance = FileParser(r'C:\Document\data_file.txt')
updated_instance.parse_file().make_chromatography_data_df()

chromatogram_instance = ChromatogramProcessor( data = updated_instance.chromatography_data_df,
                                                x_accessor='Time (min)',
                                                y_accessor= 'Value (EU)',
                                                baseline_correction=False,  #Removes baseline correction
                                                peak_prominence=0.5,  #Change from default. Make peak calling more restrictive
                                                min_peak_width=10  #Changes how peaks are called based on minimum widths
                                                ) 

chromatogram_instance.preprocess_chromatogram()
chromatogram_instance.integrate_peaks()

#Not strictly necessary, but maintains the traditional relationship between FileParser and identified peaks
updated_instance.processed_chromatogram=chromatogram_instance

for peak in updated_instance.processed_chromatogram.identified_peaks:
    print('peak borders are:', peak.peak_borders)
    print('peak area is:', peak.peak_area)
    print('peak height is:', peak.peak_height)
```

If you would like to modify peak integration specific parameters, you need to follow the same pattern by manually calling the steps of `integrate_peaks`.

Beyond basic numerical descriptions, performance can be evaluated via plots like the following. The blue line represents raw data, the red line baseline corrected data, and green dots identifies peak centers.

![image](https://github.com/nabfl/takeHome/assets/174144713/ce298510-d17f-4079-8315-4f2b867ee793)


## Overall Thoughts

The current implementation of an Acquity data parser contains all the essential features for chromatographic processing but utilizes several naïve assumptions. Future iterations should improve on:
1.	Refining peak border calling. The current methods all have obvious shortcomings, though gradient based detection is the most versatile. Gradient based border  detection can, and should, be updated to provide explicit means to alter how peak tails are integrated.
2.	Implementing chromatogram normalization to reduce required tuning of parameters across diverse datasets.
3.	Refining baseline estimation. The current baseline estimation method fits a single polynomial to the entire length of a chromatogram. While one must be wary of overfitting, better results can be obtained by utilizing splines to estimate regions of the baseline. Similarly, a better background isolation method can be used to more precisely model the chromatogram baseline
4.	Provide a basic gaussian fit based method to integrate peak areas. Though not a personal preference, this is still a common method used by many and should be accounted for.


