namespace UKNF.Backend.Models.Communication;

public record ReportRecord(
    string Id,
    string Name,
    string Period,
    string Status,
    DateTimeOffset SubmittedAt
);
