# ─── IAM Role for Lambda ──────────────────────────────────────
# Lambda needs permission to run and write logs

resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Allow Lambda to write logs to CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allow Lambda to run inside the VPC (needed to reach RDS)
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Allow Lambda to use Transcribe
resource "aws_iam_role_policy_attachment" "lambda_transcribe" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonTranscribeFullAccess"
}

# Allow Lambda to read/write the voice notes S3 bucket
resource "aws_iam_role_policy" "lambda_s3" {
  name = "${var.project_name}-lambda-s3-${var.environment}"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ]
      Resource = "${aws_s3_bucket.voice_notes.arn}/*"
    }]
  })
}

# ─── Lambda Security Group ────────────────────────────────────
# Lambda needs its own security group to talk to RDS

resource "aws_security_group" "lambda" {
  name        = "${var.project_name}-lambda-${var.environment}"
  description = "Security group for Lambda function"
  vpc_id      = aws_vpc.main.id

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ─── Lambda Function ──────────────────────────────────────────

resource "aws_lambda_function" "api" {
  filename         = "../backend/lambda_package.zip"
  function_name    = "${var.project_name}-api-${var.environment}"
  role             = aws_iam_role.lambda.arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256

  # Place Lambda in private app subnets so it can reach RDS
  vpc_config {
    subnet_ids         = [aws_subnet.private_app_a.id, aws_subnet.private_app_b.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  # Environment variables — pass secrets to Lambda
  environment {
    variables = {
      DB_HOST             = aws_db_instance.main.address
      DB_PORT             = "5432"
      DB_NAME             = "carassistant"
      DB_USER             = var.db_username
      DB_PASSWORD         = var.db_password
      ANTHROPIC_API_KEY   = var.anthropic_api_key
      AWS_REGION_NAME     = var.aws_region
      S3_BUCKET_NAME      = aws_s3_bucket.voice_notes.id
    }
  }

  source_code_hash = filebase64sha256("../backend/lambda_package.zip")
}

# ─── API Gateway ─────────────────────────────────────────────
# Creates a public HTTPS endpoint that triggers Lambda

resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.api.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Allow API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}