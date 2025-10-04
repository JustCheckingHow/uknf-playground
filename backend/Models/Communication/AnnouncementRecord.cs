namespace UKNF.Backend.Models.Communication;

public record AnnouncementRecord(
    string Id,
    string Title,
    string TargetAudience,
    double AcknowledgementRate,
    DateTimeOffset PublishedAt
);
