Data overview 

The dataset is a subset of data from “NOAA Global Surface Summary of Day”. It covers data from 2022 to 2025, 4 years in total, and included data for 50 unique weather stations. The following are important data elements included in the dataset (as available from each station), and how they are denoted in data frame: 

* Station id. STATION 

* Station name. NAME 

* Station latitude, Station longitude. LATITUDE, LONGTITUDE 

* Collected date. DATE 

* Mean temperature (.1 Fahrenheit). TEMP 

* Mean dew point (.1 Fahrenheit). DEWP 

* Mean sea level pressure (.1 mb). SLP 

* Mean station pressure (.1 mb). STP 

* Mean visibility (.1 miles). VISIB 

* Mean wind speed (.1 knots), WDSP 

* Maximum sustained wind speed (.1 knots). MXSPD 

* Maximum wind gust (.1 knots). GUST 

* Maximum temperature (.1 Fahrenheit). MAX 

* Minimum temperature (.1 Fahrenheit). MIN 

* Precipitation amount (.01 inches). PRCP 

* Snow depth (.1 inches). SNDP 

* Indicator for occurrence of: Fog. Rain or Drizzle. Snow or Ice Pellets. Hail. Thunder. Tornado/Funnel Cloud. FRSHTT 

* Each measured element such as: TEMP, SLP... will have another attribute columns, such as TEMP_ATTRIBUTES, SLP_ATTRIBUTES 

 

Contributions 

Ngoc Minh Tran: Task 1 

Adrian Julve: Task 2 

Anna Phan: Task 3 

Evan Poulson: Task 4 

 

Task 1 

The dataset has a total of 48404 records and 28 columns.  

For schema inspection, there are 4 types of data in dataset, including: Integer, Double, String and Date. The Following list shows columns for each type of data 

Integer type columns: TEMP_ATTRIBUTES, DEWP_ATTRIBUTES, SLP_ATTRIBUTES, STP_ATTRIBUTES, VISIB_ATTRIBUTES, WDSP_ATTRIBUTES, STATION. 

String type columns:  NAME, MAX_ATTRIBUTES, MIN_ATTRIBUTES, FRSHTT 

Date type columns: Date 

Double type column: LATITUDE, LONGITUDE, ELEVATION, TEMP, DEWP, SLP, STP, VISIB, WDSP, MXSPD, GUST, MAX, MIN, PRCP, SNDP 

STATION, primary key, null value is set to false, other columns can have null values 

In terms of data quality, the dataset shows high quality in temperature and wind data. In detail, there is no missing value in average temperature column aka TEMP, 160 in max temperature aka MAX, 153 in min temperature aka MIN, 153 for wrong logical records in temperature field, and 2208 for dew point. For wind data, there are only 2850 and 2857 null value data for wind speed, WDSP, and max wind speed, 2857, respectively. On the other hand, the dataset shows poor collection on pressure data, SLP and STP have 32186 and 32191 of missing data, respectively. Besides, Attribute columns also show a high number of missing data. There also observed that columns consist of stations data such as: STATION, DATE, LATITUDE, LOGITUDE, ELEVATION, NAME does not have any missing data; these columns could be used for feature global key or primary keys for different tables.  

 

Task 2 

The PySpark implementation reads the combined dataset from the shared folder, totaling 48,404 records across 50 stations and 4 years (2022-2025). Before computing averages, invalid and missing temperature values were filtered out. NOAA uses 9999.9 as a sentinel value for missing data, and these records along with null values in the TEMP column were removed from the dataset. 

The core computation extracts the station identifier and year from the DATE field, then groups the data by station and year. The avg() aggregation function computes the mean temperature for each group, rounded to two decimal places. The results are ordered by station and year for readability. PySpark's groupBy and agg operations handle this as a distributed aggregation, meaning the work is split across partitions and combined automatically. 

Spark is well suited for this task because it processes data in memory rather than writing intermediate results to disk. The lazy evaluation model allows Spark to optimize the full chain of transformations before executing them. For a dataset of this size, the computation completes in seconds. The DataFrame API also keeps the code concise, with the entire filtering, grouping, and aggregation workflow handled in under 10 lines. 

The final output follows the required format of station, year, and average temperature, saved as a single CSV file for use in Tasks 3 and 4. 

 

 Task 3 

Although MapReduce and PySpark both support batch processing, they differ in performance and ease of use. MapReduce – the original data-processing model used in Hadoop – tends to be slower because it writes intermediate results to disk, whereas its newer and faster counterpart, Spark, keeps data in memory whenever possible. In terms of usability, MapReduce programs are generally more complex to write, while Spark offers simpler and more flexible programming interfaces. Additionally, Spark’s versatility stands out when compared to MapReduce, as Spark also supports real-time streaming, machine learning, and graph processing. Despite Spark’s widespread adoption in modern applications, MapReduce remains important for understanding the foundations of big data processing, being one of the earliest software designs adopted for use in cloud systems.  

The PySpark implementation in the previous task required relatively little code for the computation of average annual temperature per station. In just a few readable lines, the entire workflow of selecting the appropriate columns, grouping them by station and year, aggregating them by the average temperature, and ordering the results by station and year was accomplished. The MapReduce implementation, however, was not quite simple. Both the mapper and reducer script for this same computation were considerably longer, with roughly 40 – 50 lines of code each, reflecting the need to manually handle parsing, key-value emission, intermediate formatting, and aggregation logic. 

While the exact execution times were not recorded for this task and the previous, the performance difference between the two approaches was clear even though they produced the same output results. As expected, PySpark completed the task noticeably faster, which is consistent with its in-memory model and improved processing engine. MapReduce, with its reliance on intermediate disk storage, experienced additional latency – it was still rapid, taking only a few seconds, but less efficient relative to the PySpark method. 

 

Task 4 

The subset I worked with is 50 NOAA GSOD stations spread across Norway and Svalbard, between 60°N and 81°N, from 2022 through 2025. The annual means come from the Task 2 Spark output, and the dashboard layers station metadata (name, latitude, longitude) pulled from the raw GSOD partitions so that every station shows up by name instead of a ten-digit ID. The dashboard itself is a Streamlit app with a sidebar filter for latitude band and year range, a KPI strip, a latitude-band trend chart, a map of the four-year station means, a horizontal ranking of each station's 2022 to 2025 change, a station-to-station comparison overlay, and a year-over-year outlier table. 

  

I wanted the dashboard to answer three things. First, do the stations as a group move in the same direction across these four years, or does every station have its own story? Second, does latitude actually predict temperature in a small high-latitude subset like this, or are other factors (elevation, coastline, oil platform vs inland ridge) doing more of the work? Third, where are the anomalies that look like real climate signal versus the ones that look like coverage or sensor issues? To handle the latitude question, I grouped stations into three bands: Sub-Arctic below 67°N, Arctic from 67 to 75°N, and High Arctic at 75°N and up. 

   

The three bands are cleanly separated and stay separated. Sub-Arctic stations average in the high 40s°F, the Arctic band runs in the mid 30s, and the High Arctic averages low-to-mid 20s, with roughly 25°F between the warmest and coldest band means across the full window. Inside each band, though, the year-to-year movements are small and coordinated: 2024 is the warmest year in all three bands, and 2023 is the coolest year in the Arctic and Sub-Arctic bands. The High Arctic's coldest year is 2022 rather than 2023, which I suspect reflects the fact that three Svalbard stations only began reporting in 2023, shifting the 2022 sample toward the slightly warmer High Arctic sites. SORSTOKKEN on the southern Norwegian coast comes out as the warmest station in the set at about 49.6°F mean, and the Svalbard cluster (Verlegenhuken, Karl XII Oya, Kongsoya, Edgeoya) anchors the cold end. 

  

Of the 46 stations with complete four-year coverage, 36 ended 2025 warmer than 2022, roughly 78 percent. Nine cooled. The cooling stations are almost entirely inside the Arctic band rather than the High Arctic, which is the opposite of what I expected going in. The biggest single-station warmings are all on the Fennoscandian interior or Svalbard: Suolovuopmi Lulit climbs from 6.3°F in 2022 to 33.1°F in 2025, Tanabru climbs 25°F over the same window, and three Svalbard stations (Edgeoya, Kongsoya, Sorkappoya) each gain roughly 18 to 22°F. Those 2022 readings are low enough that I treat them as suspect rather than as real climate signal. The station comparison view makes this easy to see: pairing Suolovuopmi Lulit against a nearby station like Karasjok, they start the window 28°F apart and finish within a degree of each other, which is not how two neighboring stations actually behave. 

  

On the anomaly side, the year-over-year outlier table flags station-years whose change from the prior year lands more than one standard deviation (about 7.4°F) off the dataset mean. The single largest swing is Kautokeino II dropping from 47.3°F in 2022 to 10.2°F in 2023 before recovering into the mid 30s, a 37°F drop in one year. A genuine winter cannot do that in interior Norway, so I read it as a sensor or reporting gap. Most of the flagged outliers fit the same shape, a single cold year surrounded by normal ones, which is why the dashboard frames the outlier table as a data-quality view rather than a climate-change view. 

   

The headline from this subset is that high-latitude temperature behaves more like a regional system than a station-by-station one. All three latitude bands moved in near parallel across four winters, which is the kind of signal you want when you are trying to attribute change to broad climate drivers rather than local siting effects. At the same time, the messy edges matter just as much as the clean trend. In a dataset this small, a handful of stations with bad 2022 readings can single-handedly produce the appearance of rapid Arctic warming, and any downstream claim about "Arctic stations warmed 20 degrees in four years" would be wrong in exactly that way. Putting the map, the ranking, and the outlier table on the same page makes those artifacts visible instead of letting them disappear into an aggregate number, which is the whole point of building the dashboard rather than shipping a single summary statistic. 
