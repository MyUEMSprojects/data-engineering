variable "project" {
  description = "Prefixo dos recursos."
  type        = string
  default     = "orders"
}

variable "environment" {
  description = "dev | staging | prod."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment deve ser dev, staging ou prod."
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "emulator_endpoint" {
  description = "URL de um emulador AWS (ex.: http://moto:5000). Vazio = AWS de verdade."
  type        = string
  default     = ""
}

variable "enable_event_source_mapping" {
  description = "Liga a Lambda à fila. No emulador fica false (Moto precisa do Docker para EXECUTAR a Lambda)."
  type        = bool
  default     = true
}

variable "lambda_src_dir" {
  description = "Diretório com o código da Lambda (handler.py)."
  type        = string
  default     = "../src/cloudpipe"
}

variable "lambda_timeout_s" {
  type    = number
  default = 60
}

variable "max_receive_count" {
  description = "Tentativas antes de a mensagem ir para a DLQ."
  type        = number
  default     = 3
}

variable "raw_transition_days" {
  description = "Dias até mover a camada raw para Standard-IA."
  type        = number
  default     = 30
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "enforce_tls_only" {
  description = "Nega qualquer acesso S3 sem TLS. Em produção: SEMPRE true. O emulador só fala HTTP, então o e2e desliga."
  type        = bool
  default     = true
}
