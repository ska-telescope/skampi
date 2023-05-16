terraform {
  required_version = "~>1.3.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~>3.1.1"
    }
  }
}

resource "null_resource" "test" {
  triggers = {
    "some" = "trigger"
  }
}