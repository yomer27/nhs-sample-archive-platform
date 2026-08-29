resource "aws_dynamodb_table" "samples" {
  name         = "Samples"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "sampleId"

  attribute {
    name = "sampleId"
    type = "S"
  }

  attribute {
    name = "sendingHospital"
    type = "S"
  }

  global_secondary_index {
    name            = "sendingHospital-index"
    hash_key        = "sendingHospital"
    projection_type = "ALL"
  }
}
