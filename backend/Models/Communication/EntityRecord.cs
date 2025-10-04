namespace UKNF.Backend.Models.Communication;

public record EntityRecord(
    string Id,
    string Name,
    string Category,
    string? Krs,
    DateTimeOffset UpdatedAt
);
