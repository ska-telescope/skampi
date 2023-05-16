terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
    }
  }
}

resource "null_resource" "test" {
  triggers = {
    "some" = "trigger"
  }
}