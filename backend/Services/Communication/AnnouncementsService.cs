using System.Globalization;
using UKNF.Backend.Models.Communication;

namespace UKNF.Backend.Services.Communication;

public class AnnouncementsService
{
    private static readonly AnnouncementRecord[] SeedAnnouncements =
    {
        new(
            "announcement-1",
            "New prudential reporting taxonomy available",
            "Banks",
            0.62,
            DateTimeOffset.Parse("2025-03-01T06:00:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "announcement-2",
            "Reminder: Cyber resilience self-assessment deadline",
            "Payment Institutions",
            0.43,
            DateTimeOffset.Parse("2025-02-20T10:00:00Z", CultureInfo.InvariantCulture)
        )
    };

    public IEnumerable<AnnouncementRecord> GetAll() => SeedAnnouncements;
}
