namespace UKNF.Backend.Models.Communication;

public record LibraryRecord(
    string Id,
    string Title,
    string Category,
    DateTimeOffset UpdatedAt,
    string DownloadUrl
);
