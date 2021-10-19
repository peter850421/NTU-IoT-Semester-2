FROM public.ecr.aws/lambda/python:3.8

RUN pip install requests
RUN pip install matplotlib
RUN pip install boto3

COPY s3_credentials ./s3_credentials
COPY dynamodb_credentials ./dynamodb_credentials
COPY app.py ./
COPY process_distance.py ./
COPY process_light.py ./
COPY process_text.py ./
COPY util.py ./

CMD ["app.lambda_handler"]
