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
    job_name = f"transcribe-{uuid.uuid4()}"
    media_uri = f"s3://{S3_BUCKET}/{s3_key}"
    
    # Map file extensions to Transcribe media formats
    format_map = {"m4a": "mp4", "mp3": "mp3", "wav": "wav", "mp4": "mp4", "ogg": "ogg", "flac": "flac"}
    file_ext = s3_key.split(".")[-1].lower()
    media_format = format_map.get(file_ext, "mp3")
    
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": media_uri},
        MediaFormat=media_format,
        LanguageCode="en-US",
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

ALLOWED_AUDIO_EXTENSIONS = {"m4a", "mp3", "wav", "mp4", "ogg", "flac"}

def generate_presigned_upload_url(file_extension: str = "m4a") -> dict:
    """
    Generate a presigned S3 URL for direct audio upload from client.
    Only allows audio file types — rejects anything else.
    URL expires in 5 minutes.
    """
    # Security: validate file extension
    ext = file_extension.lower().strip(".")
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(f"File type '{ext}' not allowed. Must be one of: {ALLOWED_AUDIO_EXTENSIONS}")
    
    s3_key = f"voice-notes/{uuid.uuid4()}.{ext}"
    
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": S3_BUCKET,
            "Key": s3_key,
            "ContentType": f"audio/{ext}",
            "ServerSideEncryption": "AES256"
        },
        ExpiresIn=300  # 5 minutes
    )
    
    return {
        "upload_url": presigned_url,
        "s3_key": s3_key
    }