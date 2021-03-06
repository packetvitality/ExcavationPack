![logo_github_readme](https://user-images.githubusercontent.com/45752781/114323589-b9760680-9ada-11eb-9777-c9f857ecbb48.png)

# Summary
Data dumped online from breaches is rich with information but can be challenging to process. The data is often unstructured and littered with different data types.
This framework uses Docker containers to process unstructured data. Utilizing this framework will help identify points of interest in data dumps. This project was written as part of my Masters program, more details about the motives and build process can be found here: https://www.sans.org/reading-room/whitepapers/OpenSource/excavationpack-framework-processing-data-dumps-40275

# Usage
1.	Ensure Docker and docker-compose are operational.
2.	[Optional] Customize the docker-compose file.
3.	Place a keyword text file in the working directory.
4.	Edit the environmental variable (.env) file to specify a working directory and the directory to be searched. 
6.	Issue the command ‘docker-compose up’ from the project directory.

Customizing the docker-compose file provides more processing control. For example, users can configure the 'replicas' setting to create more or fewer instances of a specific container. The user can configure the 'resources' setting to control the amount of CPU and/or memory the containers use. The framework can take significant time to process depending on the size of the data dump. A useful command to check on the status of containers is 'docker container stats'. This command shows the currently running containers and their resource utilization.

![Screenshot 2021-05-07 145442](https://user-images.githubusercontent.com/45752781/117512294-306cb680-af44-11eb-922a-fe99197434b1.png)
Starting from left to right, and moving from top to bottom, the image above illustrates what is needed to run the project. 

The framework runs using Docker and docker-compose. We must ensure Docker and Docker-compose are operational.

Next is the docker-compose configuration file. Modifying this file is optional and allows the user to decide how many instances of any workflow to run. In the example above, 5 instances of the data categorizer will run and 2 copies of the excel search will run (the rest of the config is truncated). 

A list of keywords is required to specify what we will be searching for.

There is a ‘.env’ file which specifies a working directory (where things like the ‘keywords.txt’ file and results are stored) and where to find the data to search. 

Lastly, the project is initiated using the ‘docker-compose up’ command from the project directory. 


![Screenshot 2021-05-07 145613](https://user-images.githubusercontent.com/45752781/117512401-66aa3600-af44-11eb-9bfb-bb53e8a74571.png)
In the image above, the top right corner shows how the results are stored in text files. As keywords are identified in the data dump, the results are stored in text files with names corresponding to the keyword. A snippet of one of the text files is shown in the second screenshot from the top. The result file contains the file where the keyword was discovered and the full context of the line.

While the framework is running, a helpful command is ‘docker container stats’. This will show the current resource utilization of the various workflows. As the data processing completes, each container will shut down. This is a good indicator to check if data is still being processed. 


# Current Functionality
To-date, the framework provides the capability to process five data types using a supplied list of keywords. It also handles uncompressing a few different formats. The results are stored in text files which are grouped by keyword. The processing occurs concurrently. There is no known limitation for the depth of directories and subdirectories the framework can traverse or the number of files it can search through. The framework will also handle decompressing files and adding newly decompressed files into the processing workflow. The specific data types supported are as follows:

## Searching
- [x] Plaintext files
- [x] Microsoft Excel spreadsheets
- [x] Legacy Microsoft Excel spreadsheets
- [x] Microsoft Word documents
- [x] Portable Document Format (Pdf)

## Decompression
- [x] Gzip
- [x] RAR
- [x] ZIP
- [x] TAR
- [x] BZIP2

## Supported Platforms
The framework was developed and tested using Ubuntu 20.04.1. Though it technically works on Microsoft Windows using Docker Desktop, the performance is abysmal due to how Docker containers access the Windows file system. Docker Desktop for Windows is facilitated by using Windows Subsystem for Linux 2 (WSL2). The path to attach volumes from Windows to Docker is: Docker -> WSL2 -> Windows file system. This connection path adds latency and renders the framework unusable. The latency for attached volumes is a known issue, and Microsoft generally recommends against "working across operating systems with your files". Performance is likely better if attached volumes reside directly in WSL2 instead of the Windows filesystem; however, this research did not cover this test. This framework was not tested with Docker Desktop on Mac. 

# Concept
The framework is focused on identifying points of interest within a data dump containing an unforeseen number of directories, subdirectories, and files. Files stored in an unstructured tree are common, as evidenced in ‘Cit0Day’ breach collection and the ‘BlueLeaks’ data dump. The strategy taken to solve this problem can be summarized into two simple steps:
1. Categorize each file into data types. Examples of data types include plaintext, Excel spreadsheet, PDF, etc.
2. The appropriate 'workflow' will process the data type. 

The diagram below illustrates how the framework processes data. There are 'categorizers' and 'searchers' running in containers. Multiple containers of any type can work concurrently. Also, note that each type of container can utilize a different programming/scripting language. For example, the Categorizers and Excel Searchers can utilize Python, while Plaintext searchers utilize Go, and Pdf Searchers utilize Bash. Only two instances of each container are illustrated below; however, the quantity of containers is controlled by the user.

![image](https://user-images.githubusercontent.com/45752781/111229585-607e8580-85a3-11eb-9b7d-7bdde6de9dfe.png)

*To date all of the containers are using Python, but that is just based on my knowledge, comfort level, and the fact that this was the next evolution of a monolithic Python script.*

# Common Problems / Troubleshooting
Make sure the user you initiate the containers with has read/write access to the data dump directory. If there are no compressed files, only read access is needed. However, if a file needs to be uncompressed it will do so within the data dump directory. I've noted a couple instances where the data was copied/moved to a folder created by 'root', making the contents unavailable to normal user accounts. 

Logs files are created in the working directory within the results folder. Searching or following those logs looking for 'Failed' events can help identify what may be going wrong.

Happy to answer questions if you have having trouble. I wrote this to help others in the community, so I'd love to hear from you! I can be reached on Twitter @packetvitality.
