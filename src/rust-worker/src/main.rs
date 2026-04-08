use axum::{extract::Json, routing::{get, post}, Router};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer};

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

#[derive(Deserialize)]
struct ProcessRequest {
    data: Vec<Vec<String>>,
    operation: String, // "deduplicate", "aggregate"
}

#[derive(Serialize)]
struct ProcessResponse {
    result: serde_json::Value,
    rows_processed: usize,
    duration_ms: u64,
}

// ---------------------------------------------------------------------------
// POST /similarity  -  cosine similarity on character n-gram vectors
// ---------------------------------------------------------------------------

#[derive(Deserialize)]
struct SimilarityRequest {
    text_a: String,
    text_b: String,
    #[serde(default = "default_ngram_size")]
    ngram_size: usize,
}

fn default_ngram_size() -> usize {
    3
}

#[derive(Serialize)]
struct SimilarityResponse {
    similarity: f64,
    duration_ms: u64,
}

/// Extract character-level n-grams and return frequency counts.
fn char_ngrams(text: &str, n: usize) -> HashMap<String, f64> {
    let chars: Vec<char> = text.chars().collect();
    let mut freq: HashMap<String, f64> = HashMap::new();
    if chars.len() < n {
        // If the text is shorter than ngram_size, treat the whole text as one gram.
        *freq.entry(text.to_string()).or_default() += 1.0;
        return freq;
    }
    for window in chars.windows(n) {
        let gram: String = window.iter().collect();
        *freq.entry(gram).or_default() += 1.0;
    }
    freq
}

/// Cosine similarity between two frequency vectors.
fn cosine_similarity(a: &HashMap<String, f64>, b: &HashMap<String, f64>) -> f64 {
    let dot: f64 = a.iter().map(|(k, v)| v * b.get(k).unwrap_or(&0.0)).sum();
    let mag_a: f64 = a.values().map(|v| v * v).sum::<f64>().sqrt();
    let mag_b: f64 = b.values().map(|v| v * v).sum::<f64>().sqrt();
    if mag_a == 0.0 || mag_b == 0.0 {
        return 0.0;
    }
    dot / (mag_a * mag_b)
}

async fn similarity(Json(req): Json<SimilarityRequest>) -> Json<SimilarityResponse> {
    let start = std::time::Instant::now();
    let n = if req.ngram_size == 0 { 3 } else { req.ngram_size };
    let vec_a = char_ngrams(&req.text_a, n);
    let vec_b = char_ngrams(&req.text_b, n);
    let sim = cosine_similarity(&vec_a, &vec_b);
    Json(SimilarityResponse {
        similarity: (sim * 1000.0).round() / 1000.0, // 3 decimal places
        duration_ms: start.elapsed().as_millis() as u64,
    })
}

// ---------------------------------------------------------------------------
// POST /csv-to-json  -  streaming CSV to JSON transform
// ---------------------------------------------------------------------------

#[derive(Deserialize)]
struct CsvToJsonRequest {
    csv: String,
}

#[derive(Serialize)]
struct CsvToJsonResponse {
    rows: Vec<serde_json::Value>,
    row_count: usize,
    duration_ms: u64,
}

async fn csv_to_json(Json(req): Json<CsvToJsonRequest>) -> Json<CsvToJsonResponse> {
    let start = std::time::Instant::now();
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(true)
        .from_reader(req.csv.as_bytes());

    let headers: Vec<String> = reader
        .headers()
        .map(|h| h.iter().map(|s| s.to_string()).collect())
        .unwrap_or_default();

    let mut rows: Vec<serde_json::Value> = Vec::new();
    for result in reader.records() {
        if let Ok(record) = result {
            let mut map = serde_json::Map::new();
            for (i, field) in record.iter().enumerate() {
                let key = headers.get(i).cloned().unwrap_or_else(|| format!("col_{i}"));
                map.insert(key, serde_json::Value::String(field.to_string()));
            }
            rows.push(serde_json::Value::Object(map));
        }
    }

    let count = rows.len();
    Json(CsvToJsonResponse {
        rows,
        row_count: count,
        duration_ms: start.elapsed().as_millis() as u64,
    })
}

// ---------------------------------------------------------------------------
// POST /transform  -  generic chained data transformation
// ---------------------------------------------------------------------------

#[derive(Deserialize)]
struct TransformRequest {
    data: Vec<serde_json::Value>,
    operations: Vec<String>,
}

#[derive(Serialize)]
struct TransformResponse {
    data: Vec<serde_json::Value>,
    original_count: usize,
    result_count: usize,
    operations_applied: Vec<String>,
    duration_ms: u64,
}

/// Apply a chain of operations: "sort:field", "filter:field:value", "limit:N"
fn apply_operations(
    mut data: Vec<serde_json::Value>,
    operations: &[String],
) -> (Vec<serde_json::Value>, Vec<String>) {
    let mut applied = Vec::new();

    for op in operations {
        let parts: Vec<&str> = op.splitn(3, ':').collect();
        match parts.first().copied() {
            Some("sort") => {
                if let Some(&field) = parts.get(1) {
                    let field = field.to_string();
                    data.sort_by(|a, b| {
                        let va = a.get(&field).and_then(|v| v.as_str()).unwrap_or("");
                        let vb = b.get(&field).and_then(|v| v.as_str()).unwrap_or("");
                        // Try numeric comparison first, fall back to string.
                        match (va.parse::<f64>(), vb.parse::<f64>()) {
                            (Ok(na), Ok(nb)) => na.partial_cmp(&nb).unwrap_or(std::cmp::Ordering::Equal),
                            _ => va.cmp(vb),
                        }
                    });
                    applied.push(format!("sort:{field}"));
                }
            }
            Some("filter") => {
                if let (Some(&field), Some(&value)) = (parts.get(1), parts.get(2)) {
                    let field = field.to_string();
                    let value = value.to_string();
                    data.retain(|item| {
                        item.get(&field)
                            .and_then(|v| {
                                // Match against string repr or raw value.
                                if let Some(s) = v.as_str() {
                                    Some(s == value)
                                } else {
                                    Some(v.to_string() == value)
                                }
                            })
                            .unwrap_or(false)
                    });
                    applied.push(format!("filter:{field}:{value}"));
                }
            }
            Some("limit") => {
                if let Some(Ok(n)) = parts.get(1).map(|s| s.parse::<usize>()) {
                    data.truncate(n);
                    applied.push(format!("limit:{n}"));
                }
            }
            _ => { /* skip unknown operations */ }
        }
    }

    (data, applied)
}

async fn transform(Json(req): Json<TransformRequest>) -> Json<TransformResponse> {
    let start = std::time::Instant::now();
    let original_count = req.data.len();
    let (data, applied) = apply_operations(req.data, &req.operations);
    let result_count = data.len();

    Json(TransformResponse {
        data,
        original_count,
        result_count,
        operations_applied: applied,
        duration_ms: start.elapsed().as_millis() as u64,
    })
}

// ---------------------------------------------------------------------------
// Existing endpoints
// ---------------------------------------------------------------------------

async fn health() -> &'static str {
    "ok"
}

async fn process(Json(req): Json<ProcessRequest>) -> Json<ProcessResponse> {
    let start = std::time::Instant::now();
    let rows = req.data.len();

    let result = match req.operation.as_str() {
        "deduplicate" => {
            let mut seen = std::collections::HashSet::new();
            let unique: Vec<&Vec<String>> = req
                .data
                .iter()
                .filter(|row| {
                    let key = row.join("|");
                    seen.insert(key)
                })
                .collect();
            serde_json::json!({
                "unique_rows": unique.len(),
                "duplicates_removed": rows - unique.len()
            })
        }
        "aggregate" => {
            let mut counts = std::collections::HashMap::new();
            for row in &req.data {
                if let Some(key) = row.first() {
                    *counts.entry(key.clone()).or_insert(0u64) += 1;
                }
            }
            serde_json::json!({ "groups": counts })
        }
        _ => serde_json::json!({ "error": "unknown operation" }),
    };

    Json(ProcessResponse {
        result,
        rows_processed: rows,
        duration_ms: start.elapsed().as_millis() as u64,
    })
}

// ---------------------------------------------------------------------------
// Main — wire up routes + CORS
// ---------------------------------------------------------------------------

#[tokio::main]
async fn main() {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let app = Router::new()
        .route("/health", get(health))
        .route("/process", post(process))
        .route("/similarity", post(similarity))
        .route("/csv-to-json", post(csv_to_json))
        .route("/transform", post(transform))
        .layer(cors);

    let addr = SocketAddr::from(([0, 0, 0, 0], 8080));
    println!("Rust worker listening on {addr}");
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
