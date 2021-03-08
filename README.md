# ExcavationPack
Data dumped online from breaches is rich with information but can be challenging to process. The data is often unstructured and littered with different data types.
This  framework uses Docker containers to process unstructured data. The container-focused approach enables flexible data processing strategies, horizontal scaling of resources, the efficacy of processing strategies, and future growth. Security professionals utilizing this framework will be able to identify points of interest in data dumps.


# Usage
1.	Ensure Docker and docker-compose are operational.
2.	Edit the environmental variable (.env) file to specify a working directory and the directory to be searched. 
3.	Place a keyword text file in the working directory.
4.	[Optional] Customize the docker-compose file.
5.	Issue the command ‘docker-compose up’ from the project directory.

Customizing the docker-compose file provides more processing control. For example, users can configure the 'replicas' setting to create more or fewer instances of a specific container. The user can configure the 'resources' setting to control the amount of CPU and/or memory the containers use. The framework can take significant time to process depending on the size of the data dump. A useful command to check on the status of containers is 'docker container stats'. This command shows the currently running containers and their resource utilization.
