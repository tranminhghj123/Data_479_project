In command prompt, begin by running Hadoop:

start-dfs.cmd
start-yarn.cmd

Next, create an input folder in HDFS and upload the sample data file (if needed, replace the file path with your own):

hdfs dfs -mkdir /task3_input
hdfs dfs -put "C:\Users\student\Documents\Task3\data" /task3_input/

Make sure all files are in the input folder:

hdfs dfs -ls /task3_input/data


Now, run the Hadoop streaming job from the folder where the mappy and reducer files are saved -- in this case, "C:\Users\student\Documents\Task3". Again, change it to your specific file path if needed.


hadoop jar %HADOOP_HOME%\share\hadoop\tools\lib\hadoop-streaming-3.4.2.jar -files "mapper.py,reducer.py" -mapper "python mapper.py" -reducer "python reducer.py" -input /task3_input/data -output /task3_output

And finally, view the results:

hdfs dfs -cat /task3_output/part-00000

