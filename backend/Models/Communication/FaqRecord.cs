namespace UKNF.Backend.Models.Communication;

public record FaqRecord(
    string Id,
    string Question,
    string Answer,
    DateTimeOffset UpdatedAt
);
