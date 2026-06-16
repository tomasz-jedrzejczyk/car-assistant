import boto3
import os
import uuid
from datetime import datetime

AWS_REGION = os.getenv("AWS_REGION_NAME", "eu-central-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

s3_client = boto3.client("s3", region_name=AWS_REGION)
transcribe_client = boto3.client("transcribe", region_name=AWS_REGION)


def upload_audio_to_s3(audio_bytes: bytes, file_extension: str = "mp3") -> str:
    """
    Upload audio file to S3 and return the S3 key (path).
    """
    s3_key = f"voice-notes/{uuid.uuid4()}.{file_extension}"
    
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=audio_bytes,
        ContentType=f"audio/{file_extension}"
    )
    
    return s3_key


def start_transcription_job(s3_key: str) -> str:
    """
    Start an async AWS Transcribe job for the uploaded audio.
    Returns the job name — used later to check status.
    """
    job_name = f"transcribe-{uuid.uuid4()}"
    media_uri = f"s3://{S3_BUCKET}/{s3_key}"
    
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": media_uri},
        MediaFormat=s3_key.split(".")[-1],  # mp3, wav, etc
        LanguageCode="en-US",  # Could be made dynamic later
        OutputBucketName=S3_BUCKET,
        OutputKey=f"transcripts/{job_name}.json"
    )
    
    return job_name


def get_transcription_status(job_name: str) -> dict:
    """
    Check the status of a transcription job.
    Returns dict with status and transcript text (if completed).
    """
    response = transcribe_client.get_transcription_job(
        TranscriptionJobName=job_name
    )
    
    job = response["TranscriptionJob"]
    status = job["TranscriptionJobStatus"]  # IN_PROGRESS, COMPLETED, FAILED
    
    result = {"status": status.lower()}
    
    if status == "COMPLETED":
        # Download and parse the transcript JSON from S3
        transcript_uri = job["Transcript"]["TranscriptFileUri"]
        transcript_key = f"transcripts/{job_name}.json"
        
        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=transcript_key)
        import json
        transcript_data = json.loads(obj["Body"].read())
        
        result["transcript"] = transcript_data["results"]["transcripts"][0]["transcript"]
    
    elif status == "FAILED":
        result["error"] = job.get("FailureReason", "Unknown error")
    
    return result