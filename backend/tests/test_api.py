def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "IP-SAKTI" in data["project_name"]

def test_documents_list_empty(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)

def test_chat_insufficient_evidence_when_empty(client):
    response = client.post(
        "/api/v1/chat",
        json={"query": "Can I patent classical Charaka Samhita formulas?", "language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["confidence_status"] == "INSUFFICIENT_EVIDENCE"
