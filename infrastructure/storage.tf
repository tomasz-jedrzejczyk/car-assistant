# ─── S3 Bucket for Voice Notes ────────────────────────────────
# Temporary storage for audio files before/during transcription

resource "aws_s3_bucket" "voice_notes" {
  bucket = "${var.project_name}-voice-notes-${var.environment}"
}

# Auto-delete audio files after 7 days — we only need the transcript
resource "aws_s3_bucket_lifecycle_configuration" "voice_notes" {
  bucket = aws_s3_bucket.voice_notes.id

  rule {
    id     = "expire-old-audio"
    status = "Enabled"

    filter {}

    expiration {
      days = 7
    }
  }
}

# Block all public access — audio files are private
resource "aws_s3_bucket_public_access_block" "voice_notes" {
  bucket = aws_s3_bucket.voice_notes.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "voice_notes" {
  bucket = aws_s3_bucket.voice_notes.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}