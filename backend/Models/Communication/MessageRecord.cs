namespace UKNF.Backend.Models.Communication;

public record MessageRecord(
    string Id,
    string Subject,
    string Counterpart,
    DateTimeOffset UpdatedAt
);
