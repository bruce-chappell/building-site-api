from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import boto3
from boto3.dynamodb.conditions import Key
import json
from decimal import Decimal
from site_api.data_model import BuildSite
from site_api.helper_functions import buildsite_to_geodataframes, split_building_limits
# import os
# from dotenv import load_dotenv

# load_dotenv()
# a = os.environ.get('aws_access_key_id')

# session = boto3.Session(
#     aws_access_key_id=os.environ.get('aws_access_key_id'),
#     aws_secret_access_key=os.environ.get('aws_secret_access_key'),
#     region_name='eu-north'
# )
session= boto3.Session()
dynamodb = session.resource("dynamodb")


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Building site database."}

# Pass through error details when Pydantic model initialization fails
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# Pass thorugh error details when ValueError is through from validate_site() function
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )

@app.post("/split-save-project-data/")
async def create_item(item: BuildSite, project_name: str = 'tmp', tolerance: int = 6):
    msg=''
    # Validate
    item.validate_site(tolerance)

    # Connect to table
    table_name = 'split-site-table'
    table = dynamodb.Table(table_name)

    # Check if project exists in database, delte if it does to overwrite with new data
    response = table.query(
        KeyConditionExpression = Key('project_name').eq(project_name)
    )
    if response['Items']:
        for i in response['Items']:
            table.delete_item(
                Key={
                    'project_name':i['project_name'],
                    'building_id':i['building_id']
                }
            )
        msg += 'Old project entry deleted. '

    # # Split building limits
    building_limits_gdf, height_plateaus_gdf = buildsite_to_geodataframes(item)
    results = split_building_limits(project_name,building_limits_gdf, height_plateaus_gdf)

    # # prep data object for database
    for i in results:
        # change all floats to Decimal? Weird boto3 requirement
        item_out = json.loads(json.dumps(results[i]), parse_float=Decimal)
        try:
            table.put_item(Item=item_out)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return{'message':msg +'New project data saved to table'}

    

@app.get("/get-building-data/")
async def get_item(project_name: str, building_id: int):
    # Connect to table
    table_name = 'split-site-table'
    table = dynamodb.Table(table_name)
    try:
        response = table.get_item(Key={"project_name":project_name,'building_id':building_id})
        return {'item':response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.patch("/update-building-data/")
async def update_item():
    return {'message':'Update not yet implemented, currently deleting and writing new entries to update'}
