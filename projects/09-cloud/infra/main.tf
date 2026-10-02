locals {
  emulated = var.emulator_endpoint != ""
  name     = "${var.project}-${var.environment}"
  buckets  = toset(["raw", "curated"])
}

provider "aws" {
  region = var.region

  # Emulador: credenciais falsas e sem chamadas de validação. AWS real: cadeia padrão (SSO/role), NUNCA chaves no código.
  access_key                  = local.emulated ? "test" : null
  secret_key                  = local.emulated ? "test" : null
  skip_credentials_validation = local.emulated
  skip_metadata_api_check     = local.emulated
  skip_requesting_account_id  = local.emulated
  s3_use_path_style           = local.emulated

  dynamic "endpoints" {
    for_each = local.emulated ? [1] : []
    content {
      s3         = var.emulator_endpoint
      sqs        = var.emulator_endpoint
      iam        = var.emulator_endpoint
      kms        = var.emulator_endpoint
      lambda     = var.emulator_endpoint
      logs       = var.emulator_endpoint
      cloudwatch = var.emulator_endpoint
      sts        = var.emulator_endpoint
    }
  }

  default_tags {
    tags = {
      project     = var.project
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

# ----------------------------------------------------------------------------- criptografia
resource "aws_kms_key" "data" {
  description             = "${local.name}: chave dos dados (S3 + SQS)"
  enable_key_rotation     = true # rotação anual automática
  deletion_window_in_days = 7
}

resource "aws_kms_alias" "data" {
  name          = "alias/${local.name}-data"
  target_key_id = aws_kms_key.data.key_id
}

# ----------------------------------------------------------------------------- data lake: raw e curated
resource "aws_s3_bucket" "lake" {
  for_each = local.buckets
  bucket   = "${local.name}-${each.key}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "lake" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.lake[each.key].id

  versioning_configuration {
    status = "Enabled" # protege contra sobrescrita/remoção acidental; custo: versões antigas (ver lifecycle)
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.lake[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
    bucket_key_enabled = true # reduz chamadas ao KMS (custo) em ~99%
  }
}

resource "aws_s3_bucket_public_access_block" "lake" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.lake[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "lake" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.lake[each.key].id

  rule {
    id     = "noncurrent-expiry"
    status = "Enabled"
    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  dynamic "rule" {
    for_each = each.key == "raw" ? [1] : []
    content {
      id     = "raw-to-infrequent-access"
      status = "Enabled"
      filter {
        prefix = "incoming/"
      }
      transition {
        days          = var.raw_transition_days
        storage_class = "STANDARD_IA"
      }
    }
  }
}

data "aws_iam_policy_document" "tls_only" {
  for_each = local.buckets

  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.lake[each.key].arn,
      "${aws_s3_bucket.lake[each.key].arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "lake" {
  for_each = var.enforce_tls_only ? local.buckets : toset([])
  bucket   = aws_s3_bucket.lake[each.key].id
  policy   = data.aws_iam_policy_document.tls_only[each.key].json

  depends_on = [aws_s3_bucket_public_access_block.lake]
}

# ----------------------------------------------------------------------------- fila + DLQ
resource "aws_sqs_queue" "dlq" {
  name                      = "${local.name}-ingest-dlq"
  message_retention_seconds = 1209600 # 14 dias para investigar
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "ingest" {
  name                       = "${local.name}-ingest"
  visibility_timeout_seconds = var.lambda_timeout_s * 6 # regra da AWS para Lambda + SQS
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })
}

data "aws_iam_policy_document" "queue_from_s3" {
  statement {
    sid       = "AllowRawBucketToSend"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.ingest.arn]

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.lake["raw"].arn]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sqs_queue_policy" "ingest" {
  queue_url = aws_sqs_queue.ingest.id
  policy    = data.aws_iam_policy_document.queue_from_s3.json
}

resource "aws_s3_bucket_notification" "raw" {
  bucket = aws_s3_bucket.lake["raw"].id

  queue {
    queue_arn     = aws_sqs_queue.ingest.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "incoming/"
    filter_suffix = ".csv"
  }

  depends_on = [aws_sqs_queue_policy.ingest]
}

# ----------------------------------------------------------------------------- compute: Lambda + IAM de MENOR privilégio
data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${var.lambda_src_dir}/handler.py"
  output_path = "${path.module}/build/lambda.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name}-transform"
  retention_in_days = var.log_retention_days
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.name}-transform"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid       = "ReadIncomingObjects"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.lake["raw"].arn}/incoming/*"]
  }
  statement {
    sid       = "WriteCuratedAndRejected"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.lake["curated"].arn}/curated/*", "${aws_s3_bucket.lake["curated"].arn}/rejected/*"]
  }
  statement {
    sid       = "ConsumeIngestQueue"
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.ingest.arn]
  }
  statement {
    sid       = "UseDataKey"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [aws_kms_key.data.arn]
  }
  statement {
    sid       = "WriteOwnLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "least-privilege"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda.json
}

resource "aws_lambda_function" "transform" {
  function_name    = "${local.name}-transform"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = var.lambda_timeout_s
  memory_size      = 256

  environment {
    variables = {
      CURATED_BUCKET = aws_s3_bucket.lake["curated"].id
      STAGE          = var.environment
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda, aws_iam_role_policy.lambda]
}

resource "aws_lambda_event_source_mapping" "ingest" {
  count                              = var.enable_event_source_mapping ? 1 : 0
  event_source_arn                   = aws_sqs_queue.ingest.arn
  function_name                      = aws_lambda_function.transform.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  function_response_types            = ["ReportBatchItemFailures"] # falha PARCIAL: só reentrega o que falhou
}

# ----------------------------------------------------------------------------- observabilidade
resource "aws_cloudwatch_metric_alarm" "dlq_not_empty" {
  alarm_name          = "${local.name}-dlq-not-empty"
  alarm_description   = "Há mensagens na DLQ: arquivos que a Lambda não conseguiu processar."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.dlq.name }
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
}
