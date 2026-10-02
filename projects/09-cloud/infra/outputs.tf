output "raw_bucket" {
  value = aws_s3_bucket.lake["raw"].id
}

output "curated_bucket" {
  value = aws_s3_bucket.lake["curated"].id
}

output "ingest_queue_url" {
  value = aws_sqs_queue.ingest.id
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.id
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda.arn
}

output "lambda_function" {
  value = aws_lambda_function.transform.function_name
}
