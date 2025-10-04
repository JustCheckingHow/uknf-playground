namespace UKNF.Backend.Models.Communication;

public record CaseRecord(
    string Id,
    string Reference,
    string Topic,
    string Status,
    DateTimeOffset UpdatedAt
);
