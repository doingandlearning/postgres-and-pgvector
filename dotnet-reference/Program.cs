// Program.cs
//
// .NET reference implementation of the semantic search pattern from
// Module 05 / the Day 2 capstone: generate a real embedding via Ollama,
// then use pgvector's <=> operator to find the closest matches in
// Postgres. Not an official course exercise -- see README.md.
//
// Mirrors, roughly:
//   - Python: psycopg + requests (05-querying-with-vectors, embed_text.py)
//   - .NET:   Npgsql + Pgvector.Npgsql + HttpClient

using System.Net.Http.Json;
using System.Text.Json.Serialization;
using Npgsql;
using Pgvector;
using Pgvector.Npgsql;

const string ConnectionString =
    "Host=localhost;Port=5050;Database=pgvector;Username=postgres;Password=postgres";
const string OllamaUrl = "http://localhost:11434/api/embed";
const string OllamaModel = "bge-m3";

var queryText = args.Length > 0
    ? string.Join(' ', args)
    : "artificial intelligence and machine learning";

Console.WriteLine($"Query: \"{queryText}\"");

// 1. Generate a real embedding via Ollama (same model, same endpoint, as
//    every Python script in this course).
var embedding = await GetEmbeddingAsync(queryText);
Console.WriteLine($"Got a {embedding.Length}-dimension embedding from Ollama.");

// 2. Register pgvector's `vector` type with Npgsql so we can pass a
//    Pgvector.Vector straight in as a query parameter, instead of
//    formatting it into a SQL string ourselves.
var dataSourceBuilder = new NpgsqlDataSourceBuilder(ConnectionString);
dataSourceBuilder.UseVector();
await using var dataSource = dataSourceBuilder.Build();
await using var conn = await dataSource.OpenConnectionAsync();

// 3. Semantic search: same `<=>` cosine-distance operator used
//    throughout the course, just called from C# instead of psql.
await using var cmd = new NpgsqlCommand(
    """
    SELECT name, item_data->>'subject' AS subject, embedding <=> $1 AS distance
    FROM items
    ORDER BY distance ASC
    LIMIT 5;
    """,
    conn);
cmd.Parameters.AddWithValue(new Vector(embedding));

await using var reader = await cmd.ExecuteReaderAsync();

Console.WriteLine("\nTop 5 closest items:");
while (await reader.ReadAsync())
{
    var name = reader.GetString(0);
    var subject = reader.IsDBNull(1) ? "(none)" : reader.GetString(1);
    var distance = reader.GetDouble(2);
    Console.WriteLine($"  {distance:F4}  {name}  [{subject}]");
}

static async Task<float[]> GetEmbeddingAsync(string text)
{
    using var http = new HttpClient();
    var payload = new { model = OllamaModel, input = text };

    var response = await http.PostAsJsonAsync(OllamaUrl, payload);
    response.EnsureSuccessStatusCode();

    var result = await response.Content.ReadFromJsonAsync<OllamaEmbedResponse>();
    if (result?.Embeddings is null || result.Embeddings.Length == 0)
    {
        throw new InvalidOperationException($"No embedding returned for: {text[..Math.Min(50, text.Length)]}...");
    }

    return result.Embeddings[0];
}

record OllamaEmbedResponse(
    [property: JsonPropertyName("embeddings")] float[][] Embeddings
);
