"""
This code will extract data from NOAAS aws S3 bucket and upload them to desigened azure blob storage
By running this code, it will automatically read file from aws and overwrite file to azure blob, if exist 

- Years of data: 2022 - 2025
- Number of distinct station: 50, first 50 of year 2024
- Connection string for azure blob storage is private
"""

import boto3
from azure.storage.blob import BlobServiceClient
from botocore import UNSIGNED
from botocore.config import Config
import io
import os
from dotenv import load_dotenv

load_dotenv()

# connect token to aws s3 bucket and azure blob
s3 = boto3.client('s3', config = Config(signature_version = UNSIGNED))
bucket = 'noaa-gsod-pds'
connect_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
blob_service = BlobServiceClient.from_connection_string(conn_str=connect_str)
container_name = "rawdata"

# Getting the first 50 station of year 2024
stations =[]
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket = bucket, Prefix = f'{2024}/'):
    for obj in page.get('Contents',[]):
        station = obj['Key'].split('/')[-1].replace('.csv', '')
        if station not in stations:
            stations.append(station)
        
        if len(stations) ==50:
            break

    if len(stations) ==50:
        break

# file tracking 
total = len(stations) * 4
count = 0

# upload data to azure blob for year 2022- 2025
for year in range(2022, 2026):
    print(f"Transfering data of year {year}")
    
    for station in stations:
        key = f'{year}/{station}.csv'
        try:

            data = s3.get_object(Bucket = bucket, Key =key)['Body'].read()
            blob_service.get_blob_client(container = container_name, blob = key).upload_blob(io.BytesIO(data), overwrite = True)

            count += 1
            print(f"fininshing upload {key}")
            print(f"This is file {count} out of {total}")
        
        except Exception as e:
            print(f"skipped{key} - {e}")


print(f"Successful extract data from aws s3 bucket to azure blob")