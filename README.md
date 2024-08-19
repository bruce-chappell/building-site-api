This project requires Python>=3.10. Packages/environment can be installed by downloading Poetry 1.8.3 and running `poetry install`in the project folder.

Data handling and validation is done by the classes and functions in the site-api/ folder

Per now, the api can handle accepting one project at a time with multiple building sites and multiple height plateaus. The strucutre of the request body should match the example given with the case study prompt. It will split each building site into corresponding height plateaus and save the data into an AWS DynmoDB table. It will also throw errors if the geometries don't make sense (overlapping heigh plateaus, building sites not covered by height plateaus, shapes with no area etc) or the data format is incomplete as defined by the Pydantic model.

Project_name is the primary key, and building_id is the sort key. Building_id will be assigned by the API by order of the building sites in the input data.

The FastAPI docs can be seen at http://16.171.174.108/docs. The split-save-project-data post function validates the user inputs and saves the data. If there is already a project with the same name in the database, the old data is overwritten with the new data. The get-building-data get function can be used to access saved data in the table.
