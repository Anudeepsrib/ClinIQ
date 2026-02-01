# Start Setup
$baseUrl = "http://127.0.0.1:8001/api/v1"

# 1. Ingest Data (Should be redacted internally)
Write-Host "Uploading patient data..."
$upload = Invoke-RestMethod -Uri "$baseUrl/ingest" -Method Post -InFile "data/test_docs/patient_alpha.txt" -ContentType "multipart/form-data"
Write-Host "Upload Result: $($upload | ConvertTo-Json -Depth 2)"

# 2. Query as RESEARCHER (Expect REDACTED response)
Write-Host "`nQuerying as RESEARCHER (Public)..."
$body = @{ question = "What is the patient's name and condition?" } | ConvertTo-Json
$responseResearcher = Invoke-RestMethod -Uri "$baseUrl/query" -Method Post -Body $body -ContentType "application/json" -Headers @{ "X-Role" = "researcher" }
Write-Host "Researcher sees: $($responseResearcher.answer)"

# 3. Query as DOCTOR (Expect UNMASKED response)
Write-Host "`nQuerying as DOCTOR..."
$responseDoctor = Invoke-RestMethod -Uri "$baseUrl/query" -Method Post -Body $body -ContentType "application/json" -Headers @{ "X-Role" = "doctor" }
Write-Host "Doctor sees: $($responseDoctor.answer)"

# Check success criteria
if ($responseResearcher.answer -match "<PERSON_") {
    Write-Host "`n[SUCCESS] Researcher saw redacted tokens."
} else {
    Write-Host "`n[FAIL] Researcher did NOT see redacted tokens (or LLM hallucinated)."
}

if ($responseDoctor.answer -notmatch "<PERSON_") {
    Write-Host "[SUCCESS] Doctor saw unmasked data."
} else {
    Write-Host "[FAIL] Doctor saw redacted tokens."
}
