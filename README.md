# ExcavationPack
Data dumped online from breaches is rich with information but can be challenging to process. The data is often unstructured and littered with different data types.
This framework uses Docker containers to process unstructured data. Utilizing this framework will help identify points of interest in data dumps.


# Usage
1.	Ensure Docker and docker-compose are operational.
2.	Edit the environmental variable (.env) file to specify a working directory and the directory to be searched. 
3.	Place a keyword text file in the working directory.
4.	[Optional] Customize the docker-compose file.
5.	Issue the command ‘docker-compose up’ from the project directory.

Customizing the docker-compose file provides more processing control. For example, users can configure the 'replicas' setting to create more or fewer instances of a specific container. The user can configure the 'resources' setting to control the amount of CPU and/or memory the containers use. The framework can take significant time to process depending on the size of the data dump. A useful command to check on the status of containers is 'docker container stats'. This command shows the currently running containers and their resource utilization.

# Current Functionality
To-date, the framework provides the capability to process six data types using a supplied list of keywords. The results are stored in text files which are grouped by keyword. The processing occurs concurrently. There is no known limitation for the depth of directories and subdirectories the framework can traverse or the number of files it can search through. The framework will also handle decompressing files and adding newly decompressed files into the processing workflow. The specific data types supported are as follows:

## Searching
- [x] Plaintext files
- [x] Microsoft Excel spreadsheets
- [x] Legacy Microsoft Excel spreadsheets
- [x] Microsoft Word documents
- [x] Portable Document Format (Pdf)

## Decompression
- [x] Gzip

# Concept
The framework is focused on identifying points of interest within a data dump containing an unforeseen number of directories, subdirectories, and files. Files stored in an unstructured tree are common, as evidenced in ‘Cit0Day’ breach collection and the ‘BlueLeaks’ data dump. The strategy taken to solve this problem can be summarized into two simple steps:
1. Categorize each file into data types. Examples of data types include plaintext, Excel spreadsheet, PDF, etc.
2. The appropriate 'workflow' will process the data type. 

The diagram below illustrates how the framework processes data. There are 'categorizers' and 'searchers' running in containers. Multiple containers of any type can work concurrently. Also, note that each type of container can utilize a different programming/scripting language. For example, the Categorizers and Excel Searchers can utilize Python, while Plaintext searchers utilize Go, and Pdf Searchers utilize Bash. Only two instances of each container are illustrated below; however, the quantity of containers is controlled by the user.

![image](https://user-images.githubusercontent.com/45752781/111229585-607e8580-85a3-11eb-9b7d-7bdde6de9dfe.png)

*To date all of the containers are using Python, but that is just based on my knowledge, comfort level, and the fact that this was the next evolution of a monolithic Python script.*
